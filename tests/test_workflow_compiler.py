import pathlib
import re
import unittest

CHEMIN = pathlib.Path(__file__).resolve().parent.parent / ".github" / "workflows" / "compiler.yml"


def bloc_job(texte, nom):
    """Lignes du job `nom` (indentation de deux espaces sous `jobs:`)."""
    lignes = texte.splitlines()
    debut = lignes.index(f"  {nom}:")
    fin = next(
        (i for i in range(debut + 1, len(lignes)) if re.match(r"^  \S", lignes[i])),
        len(lignes),
    )
    return lignes[debut + 1 : fin]


def condition_job(texte, nom):
    for ligne in bloc_job(texte, nom):
        m = re.match(r"^    if: (.+)$", ligne)
        if m:
            return m.group(1)
    return None


class CompilerWorkflowTest(unittest.TestCase):
    def setUp(self):
        self.texte = CHEMIN.read_text(encoding="utf-8")

    def test_compiler_ne_saute_jamais_si_image_est_annule(self):
        # Un check obligatoire sauté compte comme réussi : si « image » est
        # annulé, « compiler » doit tourner quand même et échouer (première
        # étape), d'où always() et non !cancelled().
        condition = condition_job(self.texte, "compiler")
        self.assertIsNotNone(condition)
        self.assertIn("always()", condition)
        self.assertNotIn("cancelled()", condition)
        self.assertIn("github.repository == 'steamicc/arduino-steami-starter'", condition)

    def test_premiere_etape_exige_que_image_ait_reussi(self):
        bloc = "\n".join(bloc_job(self.texte, "compiler"))
        etapes = bloc.split("\n    steps:\n", 1)[1]
        premiere = etapes.split("\n      - ", 1)[0]
        self.assertIn("if: needs.image.result != 'success'", premiere)
        self.assertIn("exit 1", premiere)


if __name__ == "__main__":
    unittest.main()
