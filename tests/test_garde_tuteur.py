"""Tests de la garde du tuteur IA (.agents/garde-tuteur.py) et de la synchronisation
du bloc de tutorat entre AGENTS.md et .github/copilot-instructions.md.

Lancer : python3 -m unittest discover -s tests -p 'test_*.py'
"""
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
GARDE = RACINE / ".agents" / "garde-tuteur.py"


def lancer(entree, brut=False):
    """Lance la garde avec `entree` sur stdin ; renvoie (code, stdout, stderr)."""
    texte = entree if brut else json.dumps(entree)
    r = subprocess.run(
        [sys.executable, "-I", str(GARDE)],
        input=texte, capture_output=True, text=True, timeout=20,
    )
    return r.returncode, r.stdout, r.stderr


def bash(commande):
    """Entrée au format Claude Code / Codex."""
    return {"tool_name": "Bash", "tool_input": {"command": commande}, "cwd": str(RACINE)}


def copilot(commande, nom="run_in_terminal", en_chaine=False):
    """Entrée au format Copilot (toolArgs objet ou chaîne JSON)."""
    args = {"command": commande}
    return {"toolName": nom, "toolArgs": json.dumps(args) if en_chaine else args, "cwd": str(RACINE)}


class GardeTestCase(unittest.TestCase):
    def assertRefuse(self, entree, contient=None):
        code, out, err = lancer(entree)
        self.assertEqual(code, 2, f"devait être refusé : {entree!r}\nstdout={out!r}\nstderr={err!r}")
        self.assertTrue(err.strip(), "la raison doit être sur stderr")
        decision = json.loads(out)
        self.assertEqual(decision["permissionDecision"], "deny")
        self.assertEqual(decision["permissionDecisionReason"].strip(), err.strip())
        if contient:
            self.assertIn(contient, err)

    def assertAutorise(self, entree):
        code, out, err = lancer(entree)
        self.assertEqual(code, 0, f"devait être autorisé : {entree!r}\nstdout={out!r}\nstderr={err!r}")
        self.assertEqual(out, "")


class OutilsEcriture(GardeTestCase):
    def test_outils_d_ecriture_refuses(self):
        for nom in ["Edit", "Write", "MultiEdit", "NotebookEdit", "apply_patch",
                    "create_file", "replace_string_in_file", "insert_edit_into_file",
                    "edit_file", "editFiles", "createFile", "str_replace_editor",
                    "create", "edit", "delete_file", "rename_file"]:
            with self.subTest(outil=nom):
                self.assertRefuse({"tool_name": nom, "tool_input": {"file_path": "src/main.cpp"}})
                self.assertRefuse({"toolName": nom, "toolArgs": {"filePath": "src/main.cpp"}})

    # Liste blanche : chaque outil ci-dessous lit sans rien écrire (voir OUTILS_LECTURE dans la garde).
    OUTILS_LECTURE = [
        # Claude Code
        "Read", "Grep", "Glob", "LS", "NotebookRead", "WebFetch", "WebSearch", "TodoWrite", "TodoRead",
        "TaskCreate", "TaskUpdate", "TaskGet", "TaskList", "BashOutput", "Skill", "AskUserQuestion",
        # Codex
        "update_plan", "view_image", "read_file", "list_dir", "grep_files", "web_search",
        # Copilot dans VS Code
        "file_search", "grep_search", "semantic_search", "get_errors", "fetch_webpage",
        "get_changed_files", "list_code_usages", "get_task_output", "get_terminal_output",
        "terminal_last_command", "terminal_selection", "get_search_view_results", "test_search",
        "manage_todo_list", "search_workspace_symbols", "get_vscode_api", "github_repo",
        "copilot_readFile", "copilot_listDirectory", "copilot_findFiles", "copilot_findTextInFiles",
        "copilot_searchCodebase", "copilot_getErrors", "copilot_fetchWebPage", "getErrors", "readFile",
        "open_file", "show_file", "search", "text_search", "search_codebase",
        # Copilot CLI
        "view", "grep", "glob", "web_fetch", "report_intent", "ask_user", "update_todo", "read_bash",
        # Claude Code (chargement de schémas d'outils différés, sortie du mode plan)
        "ToolSearch", "ExitPlanMode",
    ]

    def test_outils_de_lecture_autorises(self):
        for nom in self.OUTILS_LECTURE:
            with self.subTest(outil=nom):
                self.assertAutorise({"tool_name": nom, "tool_input": {"file_path": "src/main.cpp"}})
                self.assertAutorise({"toolName": nom, "toolArgs": {"path": "src/main.cpp"}})

    def test_outil_inconnu_refuse(self):
        # liste blanche : ce que la garde ne connaît pas est refusé, même sans argument
        for nom in ["vscode_runCommand", "runCommand", "executeTask", "runTests", "run_tests",
                    "mcp__serveur__outil", "Task", "Agent", "KillShell", "MonOutil", "get_errors2",
                    "ReadAndWrite", "format_document", "run_notebook_cell", "open_simple_browser"]:
            with self.subTest(outil=nom):
                self.assertRefuse({"tool_name": nom, "tool_input": {}}, "outil")
                self.assertRefuse({"toolName": nom, "toolArgs": {"x": 1}}, "outil")
        self.assertRefuse({"tool_name": "MonTerminal", "tool_input": {"command": "ls"}})

    def test_outils_qui_lancent_une_tache_ou_une_commande_de_l_editeur_refuses(self):
        # la tâche VS Code « STeaMi : sauvegarder » lance steami-sauver sans question
        for nom in ["run_task", "create_and_run_task", "run_vscode_command", "install_extension",
                    "runTask", "run_in_task"]:
            with self.subTest(outil=nom):
                self.assertRefuse({"toolName": nom, "toolArgs": {"id": "shell: STeaMi : sauvegarder"}})
                self.assertRefuse({"tool_name": nom, "tool_input": {"command": "workbench.action.terminal.sendSequence"}})

    def test_saisie_dans_un_programme_interactif_refusee(self):
        self.assertRefuse({"tool_name": "write_stdin", "tool_input": {"session_id": 1, "chars": "rm x\n"}})
        self.assertAutorise({"tool_name": "write_stdin", "tool_input": {"session_id": 1}})


class CommandesRefusees(GardeTestCase):
    REFUSEES = [
        # actions réservées à l'élève
        "steami-sauver", 'steami-sauver "mon message"',
        "steami-copier LIS2MDL/BasicReader", "steami-copier --remplacer BLE/BleBeacon",
        # git qui modifie
        'git commit -m x', "git push", "git push origin main", "git reset --hard", "git clean -fd",
        "git checkout main", "git checkout -- src/main.cpp", "git restore src/main.cpp",
        "git stash", "git rebase main", "git tag v1", "git merge x", "git pull",
        "git rm src/main.cpp", "git mv a b", "git add .", "git config user.name x",
        "git -c core.pager=x log", "git -C /tmp commit -m x", "git branch nouvelle",
        "git status && git commit -m x", "git diff --output=src/main.cpp",
        "git log --output=x", "git show --output=x HEAD", "git diff --outp=x",
        # jokers non protégés : un fichier nommé -f ou --output=x deviendrait une option
        "tail *", "tail -n 2 *.md", "head *", "head -n 3 *.md", "tail ?", "head [a-z]*",
        # suppression, copie, déplacement
        "rm src/main.cpp", "rm -rf src", "/usr/bin/rm src/main.cpp", "/bin/rm x",
        "\\rm x", "r''m x", '"rm" x', "mv a b", "cp a b", "ln -s a b", "touch x", "mkdir d",
        "chmod +x x", "truncate -s0 x", "dd if=a of=b", "install a b", "rsync a b",
        # écriture par redirection, tee, sed, here-doc
        "echo x > src/main.cpp", "echo x >> src/main.cpp", "cat a > b", "cat a >b",
        "ls 1> out", "ls 2> err", "ls &> out", "ls >| out", "cat a | tee b",
        "tee x", "sed -i s/a/b/ src/main.cpp", "sed -i'' s/a/b/ x", "sed s/a/b/ x",
        "cat <<EOF\nhello\nEOF", "cat <<< hello", "cat > x <<EOF\nhi\nEOF",
        "cat <> x", "ls >(tee x)", "cat <(ls)",
        # code arbitraire
        "python -c 'open(\"x\",\"w\")'", "python3 -c 'print(1)'", "python3 script.py", "python3",
        "/usr/bin/python3 -c 1", "node -e 1", "perl -e 1", "ruby -e 1", "awk 'BEGIN{}'",
        "bash -c 'rm x'", "sh -c 'rm x'", "/bin/bash script.sh", "zsh -c ls", "bash",
        "env rm x", "env FOO=1 ls", "xargs rm", "ls | xargs rm", "find . | xargs cat",
        "sudo ls", "nohup ls", "time ls", "command rm x", "exec rm x", "timeout 5 rm x",
        "eval 'rm x'", "source x.sh", ". x.sh", "./script.sh", "src/script.sh", "~/x",
        "FOO=bar ls", "PATH=/tmp:$PATH ls", "LD_PRELOAD=x ls",
        # find, curl, gh
        "find . -delete", "find . -exec rm {} \\;", "find . -execdir rm {} +", "find . -ok rm {} \\;",
        "find . -fprint x", "find . -fprintf x %p", "find . -fls x", "find . -okdir rm {} \\;",
        "curl -o x http://a", "curl http://a", "wget http://a", "wget -O x http://a",
        "gh pr create", "gh repo delete",
        # chaînes qui contiennent une commande refusée
        "ls; rm x", "ls && rm x", "ls || rm x", "ls | rm x", "ls & rm x", "ls\nrm x",
        "ls;rm x", "cat x|rm y", "echo $(rm x)", "echo `rm x`", "ls $(rm x)", "(rm x)",
        "{ rm x; }", "echo \"$(rm x)\"", "echo \"`rm x`\"", "ls ; steami-sauver",
        "steami-compiler && git push", "cat a | grep b | python3",
        # développements inconnus et métacaractères douteux
        "$CMD x", "${CMD} x", "ls $HOME", "echo $'\\x72m'", "echo x # rm", "cd $(mktemp -d)",
        # commande inconnue : on refuse par prudence
        "pio run", "make", "npm install", "pip install x", "apt install x", "unzip x", "tar xf x",
        "tail -f x", "less x", "vim x", "nano x", "code x", "man ls", "sort -o x y", "tree -o x",
        "xdg-open x", "open x", "script x", "nc -l 1", "ssh x", "scp a b",
        # steami-* avec arguments inattendus
        "steami-compiler ../../etc", "steami-compiler a b", "steami-compiler $X", "steami-compiler -x",
        "steami-exemples ; rm x", "steami-televerser --arret",
        "steami-serveur stop", "steami-inconnue",
        # contournements classiques
        "ls |& tee x", "ls >& out", "echo x >&out", "=rm x", "r\\\nm x", "ls >!x", "ls >x",
        "ls; >x", ";;rm x", "ls \\\n| rm x", "/usr/bin/../bin/rm x", "/tmp/rm x", "/usr/bin/env rm x",
        "/usr/bin/find . -delete", "echo hi |& tee /tmp/x", "tail --follow=name x", "tail -nf x",
        # développement des accolades : fabrique des options que la garde ne voit pas
        "git diff --{output=src/main.cpp,stat}", "git log --{output=x,oneline}",
        "find src -name main.cpp -{delete,print}", "git diff --{out,}put=x", "ls src/{a,b}",
        "echo {a,b}", "cat {x,y}", "git show HEAD}",
        # joker non protégé dans find et git : un fichier nommé « -delete » ou « --output=x »
        # deviendrait une option
        "find . -name x *", "find . ?delete", "find . [-]delete", "find * -name x",
        "git diff --stat *", "git diff -- *.cpp", "git log src/*", "git show HEAD:src/?.cpp",
        "git diff [-]-output=x", "git ls-files *.cpp", "git status ?",
        "ls | find . -name x *",
    ]

    def test_refus_format_claude(self):
        for commande in self.REFUSEES:
            with self.subTest(commande=commande):
                self.assertRefuse(bash(commande))

    def test_refus_format_copilot(self):
        for commande in self.REFUSEES:
            with self.subTest(commande=commande):
                self.assertRefuse(copilot(commande))

    def test_raisons_en_francais_pour_le_tuteur(self):
        self.assertRefuse(bash("steami-sauver"), "steami-sauver")
        self.assertRefuse(bash("steami-copier BLE/BleBeacon"), "steami-copier")
        self.assertRefuse(bash("git commit -m x"), "git")
        self.assertRefuse(bash("rm x"), "fichier")
        self.assertRefuse(bash("echo x > y"), "redirection")
        self.assertRefuse(bash("python3 -c 1"), "code")
        # la raison dit au tuteur quoi faire à la place
        _, _, err = lancer(bash("steami-sauver"))
        self.assertIn("élève", err)

    def test_entree_illisible_refusee(self):
        for brut in ["", "pas du json", "{", "[]", "null", "42", '"rm x"']:
            with self.subTest(brut=brut):
                code, out, err = lancer(brut, brut=True)
                self.assertEqual(code, 2)
                self.assertEqual(json.loads(out)["permissionDecision"], "deny")
                self.assertTrue(err.strip())

    def test_commande_vide_ou_absente_refusee_en_cas_de_doute(self):
        self.assertRefuse({"tool_name": "Bash", "tool_input": {}})
        self.assertRefuse(bash(""))
        self.assertRefuse(bash("   "))


class CommandesAutorisees(GardeTestCase):
    AUTORISEES = [
        "ls", "ls -la", "ls src", "ls -la /opt/steami/libs/STeaMi", "pwd",
        "cat README.md", "cat src/main.cpp", "head -n 20 src/main.cpp", "tail -n 20 src/main.cpp",
        "grep -n loop src/main.cpp", "grep -rn 'Serial' src", 'grep -rn "digitalWrite" src/',
        "grep -r --include='*.h' begin /opt/steami/libs/STeaMi", "grep '^#include' src/main.cpp",
        "grep -c '$' src/main.cpp", "grep 'a|b' README.md", "wc -l src/main.cpp",
        "find . -name '*.cpp'", "find src -type f", "find /opt/steami/libs/STeaMi -name '*.ino'",
        "/usr/bin/cat src/main.cpp", "/bin/ls", "/usr/bin/grep -n x y",
        "git status", "git status --short", "git log", "git log --oneline -n 5", "git diff",
        "git diff src/main.cpp", "git diff --stat", "git show HEAD", "git show HEAD:src/main.cpp",
        "git log --oneline --graph", "git blame src/main.cpp", "git ls-files",
        "steami-exemples", "steami-exemples LIS2MDL", "steami-exemples bme280",
        "steami-compiler", "steami-compiler LIS2MDL/BasicReader", "steami-compiler WSEN-HIDS/BasicReader", "steami-compiler BLE/BleBeacon",
        "steami-compiler --help", "steami-compiler -h", "steami-televerser", "steami-televerser --help",
        "steami-exemples | head -20", "steami-compiler 2>&1 | head -40", "steami-compiler 2>&1",
        "steami-compiler > /dev/null", "steami-compiler 2>/dev/null", "steami-compiler >/dev/null 2>&1", "steami-compiler >&/dev/null", "ls &>/dev/null",
        "cat src/main.cpp | grep -n delay", "ls src | wc -l", "cat a | grep b | head -3",
        "cd src && ls", "cd /opt/steami && ls", "ls; pwd", "ls && cat README.md",
        "git status && git diff", "git log --oneline | head -5", "steami-exemples | grep -i led",
        "cat README.md || echo introuvable", "echo bonjour", 'echo "a > b"', "echo 'rm x'",
        "grep -n 'rm ' README.md", 'grep -rn "git commit" .', "cat 'fichier avec espaces.txt'",
        "ls *.md", "cat src/*.cpp", "grep -n x src/*.cpp", "wc -l *.md",
        "head -n 3 '*.md'", "tail -n 2 README.md", "head -n 3 src/main.cpp",
        "find . -name '*.cpp'", "find . -name \"*.h\"", "git diff -- 'src/*.cpp'", "git ls-files '*.cpp'",
        "git log -- src/\\*.cpp", "ls src/\\{a,b\\}", "echo '{a,b}'", 'grep "{" src/main.cpp',
    ]

    def test_autorisees_format_claude(self):
        for commande in self.AUTORISEES:
            with self.subTest(commande=commande):
                self.assertAutorise(bash(commande))

    def test_autorisees_format_copilot(self):
        for commande in self.AUTORISEES:
            with self.subTest(commande=commande):
                self.assertAutorise(copilot(commande))

    def test_copilot_toolargs_en_chaine_json(self):
        self.assertAutorise(copilot("git status", nom="bash", en_chaine=True))
        self.assertRefuse(copilot("rm x", nom="bash", en_chaine=True))
        self.assertRefuse(copilot("git push", nom="run_in_terminal", en_chaine=True))

    def test_toolargs_chaine_qui_n_est_pas_du_json_est_la_commande(self):
        self.assertAutorise({"toolName": "bash", "toolArgs": "git status"})
        self.assertRefuse({"toolName": "bash", "toolArgs": "rm x"})

    def test_noms_d_outils_shell(self):
        for nom in ["Bash", "bash", "shell", "local_shell", "exec_command", "run_in_terminal",
                    "runTerminalCommand", "powershell"]:
            with self.subTest(outil=nom):
                self.assertAutorise({"tool_name": nom, "tool_input": {"command": "git status"}})
                self.assertRefuse({"tool_name": nom, "tool_input": {"command": "rm x"}})

    def test_plusieurs_cles_de_commande_toutes_analysees(self):
        # la garde lisait seulement la première clé non vide : la seconde passait sans examen
        for cle in ["cmd", "commandLine", "script"]:
            with self.subTest(cle=cle):
                self.assertRefuse({"tool_name": "Bash", "tool_input": {"command": "ls", cle: "rm x"}})
                self.assertRefuse({"tool_name": "Bash", "tool_input": {"command": "rm x", cle: "ls"}})
                self.assertRefuse({"toolName": "bash", "toolArgs": {"command": "ls", cle: "rm x"}})
                self.assertRefuse({"toolName": "bash", "toolArgs": json.dumps({"command": "ls", cle: "rm x"})})
                # valeurs différentes, même si les deux sont permises : ambigu, donc refusé
                self.assertRefuse({"tool_name": "Bash", "tool_input": {"command": "ls", cle: "pwd"}})
        self.assertRefuse({"tool_name": "Bash", "tool_input": {"command": ["ls"], "cmd": "rm x"}})
        # la même commande répétée sous plusieurs clés reste permise
        self.assertAutorise({"tool_name": "Bash", "tool_input": {"command": "ls", "cmd": "ls"}})
        self.assertAutorise({"toolName": "bash", "toolArgs": {"command": "ls", "commandLine": "ls"}})

    def test_exec_command_avec_cmd(self):
        self.assertRefuse({"tool_name": "exec_command", "tool_input": {"cmd": "rm x"}})
        self.assertAutorise({"tool_name": "exec_command", "tool_input": {"cmd": "ls"}})

    def test_codex_commande_en_tableau(self):
        self.assertAutorise({"tool_name": "shell", "tool_input": {"command": ["bash", "-lc", "git status"]}})
        self.assertRefuse({"tool_name": "shell", "tool_input": {"command": ["bash", "-lc", "rm x"]}})
        self.assertAutorise({"tool_name": "shell", "tool_input": {"command": ["cat", "src/main.cpp"]}})
        self.assertRefuse({"tool_name": "shell", "tool_input": {"command": ["rm", "src/main.cpp"]}})
        self.assertRefuse({"tool_name": "shell", "tool_input": {"command": ["git", "commit", "-m", "x"]}})


class Sortie(GardeTestCase):
    def test_autorisation_silencieuse(self):
        code, out, err = lancer(bash("git status"))
        self.assertEqual((code, out, err), (0, "", ""))

    def test_refus_stdout_json_et_stderr(self):
        code, out, err = lancer(bash("rm x"))
        self.assertEqual(code, 2)
        decision = json.loads(out)
        self.assertEqual(set(decision), {"permissionDecision", "permissionDecisionReason"})
        self.assertEqual(decision["permissionDecision"], "deny")
        self.assertEqual(decision["permissionDecisionReason"], err.strip())


class AucuneEcriture(GardeTestCase):
    def test_commandes_autorisees_n_ecrivent_rien(self):
        """Exécute pour de vrai, dans un dépôt temporaire, chaque commande que la garde autorise
        (batterie CommandesAutorisees) et vérifie qu'aucun fichier n'a été créé, modifié ou supprimé."""
        with tempfile.TemporaryDirectory() as tmp:
            depot = Path(tmp) / "depot"
            (depot / "src").mkdir(parents=True)
            (depot / "src" / "main.cpp").write_text("void setup() {}\nvoid loop() {}\n", encoding="utf-8")
            (depot / "README.md").write_text("# test\n", encoding="utf-8")
            (depot / "fichier avec espaces.txt").write_text("x\n", encoding="utf-8")
            # faux programmes steami-* : les vrais (image du devcontainer) compilent ou téléversent
            faux = Path(tmp) / "faux"
            faux.mkdir()
            for nom in ("steami-exemples", "steami-compiler", "steami-televerser"):
                (faux / nom).write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
                (faux / nom).chmod(0o755)
            env = {"PATH": f"{faux}:/usr/bin:/bin", "HOME": tmp, "GIT_PAGER": "cat", "PAGER": "cat",
                   "GIT_CONFIG_NOSYSTEM": "1", "LC_ALL": "C.UTF-8"}
            git = ["git", "-c", "user.name=t", "-c", "user.email=t@example.org"]
            for c in (["init", "-q"], ["add", "."], ["commit", "-q", "-m", "init"]):
                subprocess.run(git + c, cwd=depot, env=env, check=True, capture_output=True)

            def instantane():
                return {
                    str(p.relative_to(depot)): (p.read_bytes() if p.is_file() else None)
                    for p in sorted(depot.rglob("*")) if ".git" not in p.relative_to(depot).parts
                }

            avant = instantane()
            for commande in CommandesAutorisees.AUTORISEES:
                with self.subTest(commande=commande):
                    self.assertAutorise({"tool_name": "Bash", "tool_input": {"command": commande}, "cwd": str(depot)})
                    subprocess.run(["bash", "-c", commande], cwd=depot, env=env, stdin=subprocess.DEVNULL,
                                   capture_output=True, timeout=20)
            self.assertEqual(instantane(), avant, "un fichier a été créé, modifié ou supprimé")
            statut = subprocess.run(git + ["status", "--porcelain"], cwd=depot, env=env,
                                    capture_output=True, text=True, check=True).stdout
            self.assertEqual(statut, "", "le dépôt temporaire n'est plus propre")


class SynchronisationDuTutorat(unittest.TestCase):
    MOTIF = re.compile(r"<!-- TUTEUR-PLAYBOOK-START -->.*?<!-- TUTEUR-PLAYBOOK-END -->", re.S)

    def bloc(self, chemin):
        texte = (RACINE / chemin).read_text(encoding="utf-8")
        blocs = self.MOTIF.findall(texte)
        self.assertEqual(len(blocs), 1, f"{chemin} doit contenir un seul bloc de tutorat")
        return blocs[0]

    def test_bloc_identique(self):
        self.assertEqual(self.bloc("AGENTS.md"), self.bloc(".github/copilot-instructions.md"))

    def test_bloc_non_vide(self):
        self.assertGreater(len(self.bloc("AGENTS.md")), 2000)


class ConfigurationDesAgents(unittest.TestCase):
    def charger(self, chemin):
        return json.loads((RACINE / chemin).read_text(encoding="utf-8"))

    def test_json_valides(self):
        for chemin in [".claude/settings.json", ".vscode/settings.json", ".github/hooks/garde-tuteur.json"]:
            with self.subTest(chemin=chemin):
                self.charger(chemin)

    def test_hooks_appellent_la_garde(self):
        claude = self.charger(".claude/settings.json")
        commande = claude["hooks"]["PreToolUse"][0]["hooks"][0]["command"]
        self.assertIn(".agents/garde-tuteur.py", commande)
        copilot_hooks = self.charger(".github/hooks/garde-tuteur.json")
        self.assertIn(".agents/garde-tuteur.py", copilot_hooks["hooks"]["preToolUse"][0]["bash"])

    def test_completion_copilot_desactivee(self):
        self.assertEqual(self.charger(".vscode/settings.json")["github.copilot.enable"], {"*": False})

    def test_approbation_automatique_git_refuse_output_et_accolades(self):
        regles = self.charger(".vscode/settings.json")["chat.tools.terminal.autoApprove"]
        motif = next(re.compile(k[1:-1]) for k, v in regles.items() if v is True and k.startswith("/^git"))
        for commande in ["git status", "git log --oneline -n 5", "git diff --stat", "git diff src/main.cpp"]:
            self.assertTrue(motif.search(commande), commande)
        for commande in ["git diff --output=x", "git diff --outp=x", "git log --output x",
                         "git diff --{output=x,stat}", "git show", "git commit -m x",
                         "git diff *", "git diff -- *", "git log ?", "git diff src/[a]*.cpp"]:
            self.assertFalse(motif.search(commande), commande)

    def test_deny_claude_couvre_les_ecritures(self):
        deny = self.charger(".claude/settings.json")["permissions"]["deny"]
        for regle in ["Edit", "Write", "NotebookEdit", "Bash(steami-sauver)", "Bash(steami-sauver *)",
                      "Bash(steami-copier *)", "Bash(git commit *)", "Bash(git push *)", "Bash(rm *)"]:
            self.assertIn(regle, deny)

    def test_skills_et_lien_symbolique(self):
        for nom in ["approfondir-une-notion", "quiz-thematique"]:
            texte = (RACINE / ".agents" / "skills" / nom / "SKILL.md").read_text(encoding="utf-8")
            self.assertTrue(texte.startswith("---\nname: " + nom + "\n"))
        lien = RACINE / ".claude" / "skills"
        self.assertTrue(lien.is_symlink())
        self.assertEqual(str(lien.readlink()), "../.agents/skills")
        self.assertTrue((lien / "quiz-thematique" / "SKILL.md").is_file())


if __name__ == "__main__":
    unittest.main()
