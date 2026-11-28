import importlib.util
import json
import pathlib
import subprocess
import sys
import unittest

CHEMIN = pathlib.Path(__file__).resolve().parent.parent / ".github" / "scripts" / "suivre_image.py"
spec = importlib.util.spec_from_file_location("suivre_image", CHEMIN)
suivre = importlib.util.module_from_spec(spec)
spec.loader.exec_module(suivre)


def tags(*versions):
    return "\n".join(f"{'a' * 40}\trefs/tags/devcontainer-{v}" for v in versions)


class VersionsTest(unittest.TestCase):
    def test_comparaison_numerique(self):
        self.assertEqual(suivre.derniere_version(tags("2026.11.9", "2026.11.10", "2026.11.2")), "2026.11.10")

    def test_changement_de_mois_et_d_annee(self):
        self.assertEqual(suivre.derniere_version(tags("2026.11.7", "2026.12.1", "2026.2.9")), "2026.12.1")
        self.assertEqual(suivre.derniere_version(tags("2026.12.3", "2027.01.1")), "2027.01.1")

    def test_tags_pele_et_autres_tags_ignores(self):
        sortie = tags("2026.11.4") + f"\n{'b' * 40}\trefs/tags/devcontainer-2026.11.4^{{}}\n{'c' * 40}\trefs/tags/v9.9.9\n"
        sortie += f"{'d' * 40}\trefs/tags/devcontainer-latest\n"
        self.assertEqual(suivre.derniere_version(sortie), "2026.11.4")

    def test_aucun_tag(self):
        self.assertIsNone(suivre.derniere_version(""))

    def test_plus_recente(self):
        self.assertEqual(suivre.plus_recente("2026.11.4", "2026.11.5"), "2026.11.5")
        self.assertEqual(suivre.plus_recente("2026.11.9", "2026.11.10"), "2026.11.10")
        self.assertIsNone(suivre.plus_recente("2026.11.5", "2026.11.5"))
        self.assertIsNone(suivre.plus_recente("2026.11.5", "2026.11.4"))
        self.assertIsNone(suivre.plus_recente("2026.11.5", None))

    def test_version_image(self):
        texte = '{"image": "ghcr.io/steamicc/arduino-steami-devcontainer:2026.11.5"}'
        self.assertEqual(suivre.version_image(texte), "2026.11.5")
        for mauvaise in ("latest", "autre/image:2026.11.5", "ghcr.io/steamicc/arduino-steami-devcontainer:latest"):
            with self.assertRaises(ValueError):
                suivre.version_image('{"image": "%s"}' % mauvaise)

    def test_devcontainer_du_depot(self):
        racine = CHEMIN.parent.parent.parent
        version = suivre.version_image((racine / ".devcontainer" / "devcontainer.json").read_text(encoding="utf-8"))
        self.assertRegex(version, r"^\d{4}\.\d{2}\.\d+$")


def pr(numero, branche, auteur="app/semantic-release-updater", fork=False):
    return {"number": numero, "headRefName": branche, "isCrossRepository": fork, "author": {"login": auteur}}


def commit(auteur="semantic-release-updater[bot]", committer=None):
    return {
        "sha": "e" * 40,
        "author": {"login": auteur} if auteur else None,
        "committer": {"login": committer or auteur} if (committer or auteur) else None,
    }


class PrDepasseesTest(unittest.TestCase):
    SLUG = "semantic-release-updater"

    def test_seules_les_autres_prs_image_du_robot_sont_fermees(self):
        prs = [
            pr(30, "chore/image-2026.11.14"),
            pr(25, "chore/image-2026.11.12"),
            pr(26, "chore/image-2026.11.13", auteur="semantic-release-updater[bot]"),
            pr(27, "chore/image-2026.11.11", auteur="un-humain"),
            pr(28, "chore/image-2026.11.10", fork=True),
            pr(29, "docs/autre-chose"),
        ]
        self.assertEqual(suivre.prs_depassees(prs, "chore/image-2026.11.14", self.SLUG), [25, 26])

    def test_aucune_pr(self):
        self.assertEqual(suivre.prs_depassees([], "chore/image-2026.11.14", self.SLUG), [])


class CommitsDuRobotTest(unittest.TestCase):
    SLUG = "semantic-release-updater"

    def test_tous_les_commits_du_robot(self):
        self.assertTrue(suivre.commits_du_robot([commit(), commit()], self.SLUG))

    def test_un_commit_humain(self):
        self.assertFalse(suivre.commits_du_robot([commit(), commit("un-humain")], self.SLUG))

    def test_commit_du_robot_recommite_par_un_humain(self):
        self.assertFalse(suivre.commits_du_robot([commit(committer="un-humain")], self.SLUG))

    def test_auteur_inconnu(self):
        # Adresse de courriel non liée à un compte : « author » vaut null.
        self.assertFalse(suivre.commits_du_robot([commit(auteur=None)], self.SLUG))

    def test_aucun_commit(self):
        # Une branche sans commit d'avance ne peut pas porter de PR.
        self.assertFalse(suivre.commits_du_robot([], self.SLUG))


class FluxJsonTest(unittest.TestCase):
    def test_pages_concatenees_de_gh_api_paginate(self):
        self.assertEqual(suivre.lire_flux_json('[1, 2]\n[3]\n'), [1, 2, 3])

    def test_objet_de_compare(self):
        texte = json.dumps({"ahead_by": 1, "commits": [commit()]})
        self.assertEqual(suivre.lire_flux_json(texte, cle="commits"), [commit()])

    def test_vide(self):
        self.assertEqual(suivre.lire_flux_json(""), [])


class LigneDeCommandeTest(unittest.TestCase):
    SLUG = "semantic-release-updater"

    def lancer(self, *args, entree=""):
        r = subprocess.run(
            [sys.executable, "-I", str(CHEMIN), *args],
            input=entree, capture_output=True, text=True, timeout=20,
        )
        return r.returncode, r.stdout, r.stderr

    def test_depassees(self):
        entree = json.dumps([pr(30, "chore/image-2026.11.14"), pr(25, "chore/image-2026.11.12")])
        self.assertEqual(self.lancer("depassees", "chore/image-2026.11.14", self.SLUG, entree=entree), (0, "25\n", ""))

    def test_robot_sur_les_commits_d_une_pr(self):
        code, sortie, _ = self.lancer("robot", self.SLUG, entree=json.dumps([commit()]) + json.dumps([commit()]))
        self.assertEqual((code, sortie), (0, "robot\n"))
        code, sortie, _ = self.lancer("robot", self.SLUG, entree=json.dumps([commit("un-humain")]))
        self.assertEqual((code, sortie), (0, "humain\n"))

    def test_robot_sur_une_comparaison(self):
        entree = json.dumps({"ahead_by": 1, "commits": [commit()]})
        self.assertEqual(self.lancer("robot", self.SLUG, "commits", entree=entree)[:2], (0, "robot\n"))

    def test_json_illisible(self):
        code, _, erreur = self.lancer("robot", self.SLUG, entree="pas du json")
        self.assertEqual(code, 1)
        self.assertIn("✗", erreur)

    def test_usage(self):
        self.assertEqual(self.lancer()[0], 2)
        self.assertEqual(self.lancer("depassees", "chore/image-2026.11.14")[0], 2)
        self.assertEqual(self.lancer("robot")[0], 2)


if __name__ == "__main__":
    unittest.main()
