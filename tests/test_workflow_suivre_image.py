"""Structure du robot .github/workflows/suivre-image.yml (lecture du texte, sans PyYAML)."""
import pathlib
import re
import unittest

CHEMIN = pathlib.Path(__file__).resolve().parent.parent / ".github" / "workflows" / "suivre-image.yml"


def etape(texte, nom):
    """Texte de l'étape `nom` (de « - name: nom » à l'étape suivante)."""
    debut = texte.index(f"      - name: {nom}\n")
    suite = re.search(r"^      - ", texte[debut + 1 :], re.M)
    return texte[debut : debut + 1 + suite.start()] if suite else texte[debut:]


class SuivreImageWorkflowTest(unittest.TestCase):
    def setUp(self):
        self.texte = CHEMIN.read_text(encoding="utf-8")

    def test_en_tete(self):
        en_tete = self.texte.split("\nname: suivre-image\n", 1)[0]
        self.assertTrue(en_tete.startswith("# "))
        # Déclencheurs : cron, à la demande, et dispatch par la publication de l'image.
        self.assertIn('"47 6 * * *"', self.texte)
        for mot in ("06:47", "à la demande", "devcontainer-publish", "aval",
                    ".devcontainer/devcontainer.json", "garder-ouverte", "Superseded by #"):
            self.assertIn(mot, en_tete)

    def test_jeton_de_l_app_limite_au_depot(self):
        jeton = etape(self.texte, "Jeton de l'App")
        self.assertIn("actions/create-github-app-token@64ab729a6294000f5aa4a4bc0b73d1f32bc45510 # v3.3.0", jeton)
        self.assertIn("client-id: ${{ secrets.RELEASE_APP_ID }}", jeton)
        self.assertIn("private-key: ${{ secrets.RELEASE_APP_SECRET }}", jeton)
        self.assertIn("owner: steamicc", jeton)
        self.assertIn("repositories: arduino-steami-starter", jeton)
        # La garde relance une fois un check rouge (gh run rerun).
        self.assertIn("permission-actions: write", jeton)

    def test_fusion_automatique_par_la_garde_commune(self):
        fusion = etape(self.texte, "Activer la fusion automatique")
        self.assertIn("if: steps.publiee.outputs.publiee == 'oui'", fusion)
        self.assertIn("GH_TOKEN: ${{ steps.app.outputs.token }}", fusion)
        self.assertIn(
            'bash .github/scripts/garde-fusion-auto.sh "$GITHUB_REPOSITORY" "$PR" "$APP_SLUG" compiler',
            fusion,
        )
        # Plus de garde écrite dans le workflow.
        self.assertNotIn("current_user_can_bypass", self.texte)
        self.assertNotIn("gh pr merge", self.texte)

    def test_fermeture_des_prs_depassees(self):
        fermer = etape(self.texte, "Fermer les PR dépassées")
        self.assertIn("suivre_image.py depassees", fermer)
        self.assertIn('--comment "Superseded by #$PR."', fermer)
        self.assertIn("--delete-branch", fermer)
        # Pas de --author : l'index de recherche retarde sur la création de la PR.
        self.assertNotIn("--author", self.texte)

    def test_branche_du_robot_sans_pr(self):
        chercher = etape(self.texte, "Chercher une image plus récente")
        self.assertIn("compare/", chercher)
        self.assertIn("suivre_image.py robot", chercher)
        self.assertIn("action=branche", chercher)
        ouvrir = etape(self.texte, "Ouvrir la PR")
        self.assertIn("steps.image.outputs.action == 'branche'", ouvrir)


if __name__ == "__main__":
    unittest.main()
