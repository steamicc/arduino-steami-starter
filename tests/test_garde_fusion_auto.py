"""La garde commune de fusion automatique (.github/scripts/garde-fusion-auto.sh)
est une copie à l'identique de la source partagée par les robots steamicc.

Ne pas modifier la garde ici : la modifier dans la source commune, la recopier
dans chaque dépôt, puis remplacer l'empreinte ci-dessous.
"""
import hashlib
import os
import pathlib
import unittest

GARDE = pathlib.Path(__file__).resolve().parent.parent / ".github" / "scripts" / "garde-fusion-auto.sh"
EMPREINTE = "661489204d121fe3a25dbeb533fab7123f77001dda9f138bc6a157506b983324"


class GardeCommuneTest(unittest.TestCase):
    def test_copie_identique_de_la_garde_commune(self):
        empreinte = hashlib.sha256(GARDE.read_bytes()).hexdigest()
        self.assertEqual(
            empreinte, EMPREINTE,
            "garde-fusion-auto.sh a été modifiée localement : la modifier dans la source "
            "commune, puis la recopier dans chaque dépôt.",
        )

    def test_executable(self):
        self.assertTrue(os.access(GARDE, os.X_OK))


if __name__ == "__main__":
    unittest.main()
