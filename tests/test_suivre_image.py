import importlib.util
import pathlib
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


if __name__ == "__main__":
    unittest.main()
