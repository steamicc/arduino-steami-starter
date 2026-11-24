#!/usr/bin/env python3
"""Garde du tuteur IA : hook PreToolUse partagé par Claude Code (.claude/settings.json),
Codex et GitHub Copilot, CLI et VS Code (.github/hooks/garde-tuteur.json).

L'assistant est un tuteur : il lit, explique, aide à comprendre une erreur et propose des
quiz, mais il ne modifie aucun fichier et ne lance pas à la place de l'élève les commandes
qui sauvegardent son travail. La garde :

  - refuse tout outil d'écriture de fichier (Edit, Write, apply_patch, create_file...) ;
  - en shell, n'autorise que des commandes connues, en lecture : ls, cat, head, tail, grep,
    wc, find (sans action), git status/log/diff/show, steami-exemples, steami-compiler,
    steami-televerser. Tout le reste est refusé, avec une raison adaptée pour les
    commandes qui écrivent (rm, cp, mv, tee, sed, redirections), qui exécutent du code
    (python, bash -c, xargs, env...) ou qui sont réservées à l'élève (steami-sauver,
    steami-copier, git commit/push...).

C'est une liste d'autorisations : en cas de doute (syntaxe shell qu'on ne sait pas lire,
développement $VAR ou $(...), commande inconnue), la garde refuse. Ce n'est pas un coffre-fort
(l'élève peut tout faire lui-même dans son terminal) : c'est un garde-fou contre un tuteur
qui écrirait le programme à la place de l'élève.

Entrée : un objet JSON sur stdin, au format Claude/Codex ({tool_name, tool_input, cwd}) ou au
format Copilot ({toolName, toolArgs, cwd}, toolArgs pouvant être une chaîne JSON).
Refus : code de sortie 2, raison sur stderr (Claude Code, Codex, Copilot CLI) et décision JSON
sur stdout (Copilot dans VS Code). Autorisation : code 0, sans sortie.

Python 3, bibliothèque standard seulement.
"""
import json
import re
import sys

RAISON = (
    "Refusé par la configuration du TP : le tuteur ne modifie aucun fichier du dépôt et ne fait "
    "pas le travail à la place de l'élève. Explique-lui la notion, montre un exemple court sur un "
    "autre cas dans ta réponse (l'élève l'écrit lui-même), ou demande-lui de lancer la commande "
    "lui-même dans son terminal."
)
RAISON_ELEVE = (
    "Refusé par la configuration du TP : cette commande appartient à l'élève. Le tuteur ne copie "
    "pas d'exemple dans src/ et ne sauvegarde pas le travail à sa place. Explique à quoi sert la "
    "commande et donne-la dans un bloc bash pour que l'élève la lance lui-même."
)
RAISON_INCONNUE = (
    "Refusé par la configuration du TP : le tuteur n'utilise que des commandes de lecture "
    "(ls, cat, head, tail, grep, wc, find, git status/log/diff/show) et les commandes "
    "steami-exemples, steami-compiler et steami-televerser. Par prudence, tout le reste est "
    "refusé. Explique à l'élève ce que tu voulais vérifier, ou demande-lui de lancer la commande."
)


class Refus(Exception):
    """Commande refusée : `detail` précise pourquoi, `motif` est le message général."""

    def __init__(self, detail, motif=RAISON):
        super().__init__(detail)
        self.detail = detail
        self.motif = motif


def refuser(detail, motif=RAISON):
    raison = f"{motif} ({detail})" if detail else motif
    sys.stdout.write(json.dumps({"permissionDecision": "deny", "permissionDecisionReason": raison}, ensure_ascii=False) + "\n")
    sys.stderr.write(raison + "\n")
    sys.exit(2)


# ---------------------------------------------------------------------------------------------
# Lecture de la ligne de commande, à la manière du shell, mais en refusant tout ce qu'on ne sait
# pas lire avec certitude.
# ---------------------------------------------------------------------------------------------

class Mot:
    __slots__ = ("v", "joker")

    def __init__(self, v, joker):
        self.v = v
        self.joker = joker


INCONNU_SHELL = "développement ou syntaxe du shell que la garde ne sait pas lire ($, `, (, ), #, <)"
ECRITURE_REDIR = "redirection d'écriture (>, >>, tee) : le tuteur n'écrit aucun fichier"
CIBLES_PERMISES = {"/dev/null"}


def decouper(commande):
    """Découpe `commande` en segments (séparés par ; & && | || et retours à la ligne), chacun
    étant une liste de Mot. Lève Refus pour ce qui est douteux."""
    segments, mots = [], []
    courant = None  # texte du mot en cours, None s'il n'y en a pas
    joker = False  # le mot en cours contient un caractère spécial du shell non protégé
    cite = False  # le mot en cours contient des guillemets
    redirection = None  # (opérateur) dont la cible est le prochain mot
    i, n = 0, len(commande)

    def finir_mot():
        nonlocal courant, joker, cite, redirection
        if courant is None:
            return
        if redirection is not None:
            op, redirection = redirection, None
            ok = (op in (">", ">>", "&>", "&>>") and courant in CIBLES_PERMISES) or (
                op == ">&" and (re.fullmatch(r"\d+|-", courant) or courant in CIBLES_PERMISES)
            )
            if not ok:
                raise Refus(ECRITURE_REDIR)
        else:
            mots.append(Mot(courant, joker))
        courant, joker, cite = None, False, False

    def finir_segment():
        finir_mot()
        if redirection is not None:
            raise Refus(ECRITURE_REDIR)
        if mots:
            segments.append(list(mots))
            mots.clear()

    def ajouter(texte, special=False, quote=False):
        nonlocal courant, joker, cite
        courant = (courant or "") + texte
        joker = joker or special
        cite = cite or quote

    while i < n:
        c = commande[i]
        if c in " \t":
            finir_mot()
        elif c == "\n":
            finir_segment()
        elif c == "\\":
            if i + 1 < n:
                if commande[i + 1] != "\n":  # « \ » en fin de ligne : continuation
                    ajouter(commande[i + 1], quote=True)
                i += 1
        elif c == "'":
            fin = commande.find("'", i + 1)
            if fin < 0:
                raise Refus("guillemet simple non fermé")
            ajouter(commande[i + 1:fin], quote=True)
            i = fin
        elif c == '"':
            i += 1
            ajouter("", quote=True)
            while True:
                if i >= n:
                    raise Refus("guillemet double non fermé")
                d = commande[i]
                if d == '"':
                    break
                if d in "$`":
                    raise Refus(INCONNU_SHELL)
                if d == "\\" and i + 1 < n:
                    suivant = commande[i + 1]
                    if suivant == "\n":
                        i += 2
                        continue
                    ajouter(suivant if suivant in '$`"\\' else d + suivant)
                    i += 2
                    continue
                ajouter(d)
                i += 1
        elif c in "$`()":
            raise Refus(INCONNU_SHELL)
        elif c == "#" and courant is None:
            raise Refus(INCONNU_SHELL)
        elif c == ";":
            finir_segment()
        elif c == "|":
            finir_segment()
            if i + 1 < n and commande[i + 1] in "|&":
                i += 1
        elif c == "&" and commande.startswith("&>", i):
            finir_mot()
            op = "&>>" if commande.startswith("&>>", i) else "&>"
            redirection = op
            i += len(op) - 1
        elif c == "&":
            finir_segment()
            if i + 1 < n and commande[i + 1] == "&":
                i += 1
        elif c in "<>":
            # descripteur devant l'opérateur : « 2>&1 » ; sinon le mot en cours est un argument
            if courant is not None and re.fullmatch(r"\d+", courant) and not cite:
                courant = None
            else:
                finir_mot()
            if c == "<":
                raise Refus("redirection d'entrée ou here-doc (<, <<) : passe le fichier en argument")
            suite = commande[i + 1:i + 2]
            if suite == ">":
                op = ">>"
            elif suite == "&":
                op = ">&"
            elif suite == "|":
                raise Refus(ECRITURE_REDIR)
            else:
                op = ">"
            redirection = op
            i += len(op) - 1
        else:
            ajouter(c, special=c in "*?[{}")
        i += 1

    finir_segment()
    return segments


# ---------------------------------------------------------------------------------------------
# Règles par commande
# ---------------------------------------------------------------------------------------------

DOSSIERS_SYSTEME = {"/usr/bin", "/bin", "/usr/local/bin", "/usr/sbin", "/sbin"}

ECRIT_FICHIERS = {
    "rm", "rmdir", "mv", "cp", "ln", "touch", "mkdir", "chmod", "chown", "chgrp", "truncate", "dd",
    "install", "rsync", "tee", "sed", "patch", "ed", "ex", "vi", "vim", "nano", "emacs", "code",
    "unzip", "tar", "zip", "cpio", "shred", "mktemp", "mkfifo", "tar", "gzip", "gunzip",
}
CODE_ARBITRAIRE = {
    "node", "deno", "bun", "perl", "ruby", "php", "lua", "awk", "gawk", "bash", "sh", "zsh", "dash",
    "ksh", "fish", "env", "xargs", "sudo", "su", "doas", "nohup", "time", "command", "exec", "eval",
    "source", ".", "timeout", "nice", "stdbuf", "watch", "script", "setsid", "busybox", "builtin",
}
RESEAU = {"curl", "wget", "nc", "ncat", "ssh", "scp", "sftp", "ftp"}

LECTURE_SIMPLE = {"ls", "cat", "head", "tail", "grep", "egrep", "fgrep", "wc", "pwd", "echo", "cd"}
ACTIONS_FIND = {"-exec", "-execdir", "-ok", "-okdir", "-delete", "-fprint", "-fprint0", "-fprintf", "-fls"}
GIT_LECTURE = {"status", "log", "diff", "show", "blame", "ls-files"}

ARG_EXEMPLE = re.compile(r"[A-Za-z0-9_][A-Za-z0-9_./+-]*")
ARG_PROGRAMME = re.compile(r"[A-Za-z0-9_-]+/[A-Za-z0-9_-]+")


def verifier_git(args):
    if not args or args[0] not in GIT_LECTURE:
        raise Refus(
            "commande git qui modifie le dépôt ou son historique (commit, push, reset, checkout, "
            "restore, stash, tag...) : seuls git status, log, diff, show, blame et ls-files sont "
            "permis ; c'est à l'élève de sauvegarder avec steami-sauver"
        )
    for a in args[1:]:
        if a == "--":
            break
        # --output=fichier écrit un fichier ; git accepte les abréviations (--outp, --ou...)
        if a.startswith("--o") and a.split("=")[0] != "--oneline":
            raise Refus("option git qui écrit dans un fichier (--output)")


def verifier_segment(mots):
    premier = mots[0]
    if premier.joker:
        raise Refus(INCONNU_SHELL)
    nom = premier.v
    args = [m.v for m in mots[1:]]
    if "=" in nom:
        raise Refus("variable d'environnement placée avant la commande", RAISON_INCONNUE)
    if "/" in nom:
        dossier, _, base = nom.rpartition("/")
        if dossier not in DOSSIERS_SYSTEME:
            raise Refus("programme lancé par son chemin : écris seulement son nom", RAISON_INCONNUE)
        nom = base

    if nom in ("steami-sauver", "steami-copier"):
        raise Refus(nom, RAISON_ELEVE)
    if nom == "gh":
        raise Refus("commande gh : elle agit sur le compte GitHub de l'élève")
    if nom in ECRIT_FICHIERS:
        raise Refus(f"{nom} : commande qui crée, copie, déplace, modifie ou supprime des fichiers")
    if re.fullmatch(r"python[\d.]*|pypy[\d.]*|pip[\d.]*", nom) or nom in CODE_ARBITRAIRE:
        raise Refus(f"{nom} : exécution de code arbitraire, d'un script ou d'une autre commande")
    if nom in RESEAU:
        raise Refus(f"{nom} : accès réseau ou téléchargement")

    if nom == "git":
        verifier_git(args)
    elif nom in LECTURE_SIMPLE:
        if nom == "tail" and any(
            (a.startswith("-") and not a.startswith("--") and re.search("[fF]", a)) or a.startswith("--f")
            for a in args
        ):
            raise Refus("tail -f ne rend jamais la main")
    elif nom == "find":
        if any(a in ACTIONS_FIND for a in args):
            raise Refus("find avec une action (-exec, -delete, -fprint...) : find ne sert qu'à chercher")
    elif nom == "steami-exemples":
        if not all(a in ("-h", "--help") or ARG_EXEMPLE.fullmatch(a) for a in args):
            raise Refus("steami-exemples : argument inattendu", RAISON_INCONNUE)
    elif nom == "steami-compiler":
        if len(args) > 1 or (args and args[0] not in ("-h", "--help") and not ARG_PROGRAMME.fullmatch(args[0])):
            raise Refus("steami-compiler : seul un argument de la forme driver/Exemple est permis", RAISON_INCONNUE)
    elif nom == "steami-televerser":
        if args and args not in (["-h"], ["--help"]):
            raise Refus("steami-televerser : aucun argument permis", RAISON_INCONNUE)
    else:
        raise Refus(f"commande inconnue : {nom}", RAISON_INCONNUE)


def verifier_commande(commande):
    if not commande.strip():
        raise Refus("commande vide ou illisible", RAISON_INCONNUE)
    segments = decouper(commande)
    if not segments:
        raise Refus("commande vide ou illisible", RAISON_INCONNUE)
    for mots in segments:
        verifier_segment(mots)


# ---------------------------------------------------------------------------------------------
# Lecture de l'entrée du hook
# ---------------------------------------------------------------------------------------------

SHELL = re.compile(
    r"^(Bash|shell|local_shell|exec_command|container\.exec|powershell|run_in_terminal|"
    r"runInTerminal|runTerminalCommand|terminal)$",
    re.I,
)
SAISIE_INTERACTIVE = re.compile(r"^(write_stdin|write_bash|send_to_terminal|sendToTerminal)$", re.I)
OUTIL_TODO = re.compile(r"^(TodoWrite|TodoRead|TaskCreate|TaskUpdate|update_todo|manage_todo_list)$", re.I)
OUTIL_ECRITURE = re.compile(
    r"(edit|write|create|patch|replace|insert|delete|remove|rename|move|notebook|str_replace|"
    r"commit|push|apply|append|mkdir|copy|save|upload)",
    re.I,
)


def commande_depuis(args):
    """Texte de la commande shell, ou None si l'outil n'en porte pas."""
    brut = None
    for cle in ("command", "cmd", "commandLine"):
        if args.get(cle) not in (None, ""):
            brut = args[cle]
            break
    if brut is None:
        return None
    if isinstance(brut, list):
        # Codex : ["bash", "-lc", "cat x"] ou ["cat", "x"]
        mots = [str(m) for m in brut]
        if len(mots) >= 3 and re.fullmatch(r"(/\S*/)?(ba|z|da)?sh", mots[0]) and re.fullmatch(r"-\w*c", mots[-2]):
            return mots[-1]
        return " ".join(m if re.fullmatch(r"[\w@%+=:,./-]+", m) else "'" + m.replace("'", "'\\''") + "'" for m in mots)
    return str(brut)


def main():
    # Quelle que soit la locale du terminal : les messages sont en français (UTF-8).
    for flux in (sys.stdin, sys.stdout, sys.stderr):
        flux.reconfigure(encoding="utf-8", errors="replace")
    try:
        entree = json.loads(sys.stdin.read())
    except (ValueError, OSError):
        refuser("entrée du hook illisible")
    if not isinstance(entree, dict):
        refuser("entrée du hook illisible")

    outil = str(entree.get("tool_name") or entree.get("toolName") or "")
    args = entree.get("tool_input")
    if args is None:
        args = entree.get("toolArgs")
    if isinstance(args, str):
        try:
            args = json.loads(args)
        except ValueError:
            args = {"command": args}
        if not isinstance(args, dict):
            args = {"command": str(args)}
    if not isinstance(args, dict):
        args = {}
    if not outil:
        refuser("outil inconnu")

    # Saisie dans un programme interactif déjà lancé : le garde ne verrait pas ce qui est tapé.
    if SAISIE_INTERACTIVE.search(outil):
        saisie = any(
            isinstance(v, str) and v != "" and not re.search(r"session|^id$|shellId|terminalId", k, re.I)
            for k, v in args.items()
        )
        if saisie:
            refuser(f"saisie dans un programme interactif ({outil})")
        sys.exit(0)

    if not OUTIL_TODO.search(outil) and OUTIL_ECRITURE.search(outil):
        refuser(f"outil {outil}")

    commande = commande_depuis(args)
    if SHELL.search(outil) or commande is not None:
        try:
            verifier_commande(commande or "")
        except Refus as e:
            refuser(e.detail, e.motif)
    sys.exit(0)


if __name__ == "__main__":
    main()
