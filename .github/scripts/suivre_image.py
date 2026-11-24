#!/usr/bin/env python3
"""Compare la version de l'image du modèle au dernier tag publié.

Usage : suivre_image.py FICHIER_DEVCONTAINER < sortie de « git ls-remote --tags »
Affiche la version (AAAA.MM.N) du dernier tag si elle est plus récente que
celle de l'image du modèle, sinon n'affiche rien. Code de sortie 0 dans les
deux cas ; 1 si le fichier ne contient pas d'image reconnue.
"""
import json
import re
import sys

DEPOT_IMAGE = "ghcr.io/steamicc/arduino-steami-devcontainer"
VERSION = r"\d{4}\.\d{2}\.\d+"
RE_TAG = re.compile(r"refs/tags/devcontainer-(" + VERSION + r")(\^\{\})?")
RE_IMAGE = re.compile("^" + re.escape(DEPOT_IMAGE) + ":(" + VERSION + ")$")


def cle(version):
    """AAAA.MM.N en tuple d'entiers : 2026.11.10 est plus récent que 2026.11.9."""
    return tuple(int(partie) for partie in version.split("."))


def derniere_version(sortie_ls_remote):
    versions = []
    for ligne in sortie_ls_remote.splitlines():
        trouve = RE_TAG.search(ligne)
        if trouve:
            versions.append(trouve.group(1))
    return max(versions, key=cle) if versions else None


def version_image(texte_devcontainer):
    image = json.loads(texte_devcontainer)["image"]
    trouve = RE_IMAGE.match(image)
    if not trouve:
        raise ValueError("image inattendue : " + image)
    return trouve.group(1)


def plus_recente(actuelle, derniere):
    """Renvoie `derniere` si elle est strictement plus récente que `actuelle`."""
    if derniere and cle(derniere) > cle(actuelle):
        return derniere
    return None


def main(argv):
    if len(argv) != 2:
        print(__doc__, file=sys.stderr)
        return 2
    try:
        with open(argv[1], encoding="utf-8") as f:
            actuelle = version_image(f.read())
    except (OSError, ValueError, KeyError) as erreur:
        print("✗ " + str(erreur), file=sys.stderr)
        return 1
    nouvelle = plus_recente(actuelle, derniere_version(sys.stdin.read()))
    if nouvelle:
        print(nouvelle)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
