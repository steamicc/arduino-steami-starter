#!/usr/bin/env python3
"""Décisions du robot suivre-image, testées dans tests/test_suivre_image.py.

suivre_image.py FICHIER_DEVCONTAINER < sortie de « git ls-remote --tags »
    Affiche la version (AAAA.MM.N) du dernier tag si elle est plus récente que
    celle de l'image du modèle, sinon n'affiche rien. Code de sortie 0 dans les
    deux cas ; 1 si le fichier ne contient pas d'image reconnue.

suivre_image.py depassees BRANCHE SLUG < JSON de « gh pr list --json number,headRefName,isCrossRepository,author »
    Numéros (un par ligne) des PR à fermer : branche chore/image-* de ce dépôt,
    ouverte par l'App SLUG, autre que BRANCHE. La liste est lue sans --author
    (l'index de recherche retarde) : le filtre sur l'auteur se fait ici.

suivre_image.py robot SLUG [CLE] < JSON de commits de l'API REST
    Affiche « robot » si tous les commits (au moins un) ont l'App SLUG pour
    auteur et pour committer, sinon « humain ». L'entrée est une liste de
    commits (pages de « gh api --paginate .../pulls/N/commits ») ou, avec CLE,
    un objet dont CLE contient la liste (« commits » pour .../compare/A...B).
    Code de sortie 1 si l'entrée n'est pas du JSON.
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


PREFIXE_BRANCHE = "chore/image-"


def auteurs_du_robot(slug):
    """Logins de l'App SLUG : « app/SLUG » (gh pr list) et « SLUG[bot] » (API REST)."""
    return {"app/" + slug, slug + "[bot]"}


def prs_depassees(prs, branche, slug):
    """PR ouvertes du robot pour une autre image que `branche` (jamais une PR de fork)."""
    robot = auteurs_du_robot(slug)
    return [
        pr["number"]
        for pr in prs
        if not pr.get("isCrossRepository", True)
        and pr.get("headRefName", "").startswith(PREFIXE_BRANCHE)
        and pr.get("headRefName") != branche
        and ((pr.get("author") or {}).get("login") in robot)
    ]


def commits_du_robot(commits, slug):
    """Vrai si chaque commit (au moins un) a l'App pour auteur et pour committer."""
    bot = slug + "[bot]"

    def login(commit, role):
        return (commit.get(role) or {}).get("login")

    return bool(commits) and all(login(c, "author") == bot and login(c, "committer") == bot for c in commits)


def lire_flux_json(texte, cle=None):
    """Valeurs JSON concaténées (pages de « gh api --paginate ») mises bout à bout."""
    decodeur = json.JSONDecoder()
    valeurs = []
    position = 0
    while True:
        while position < len(texte) and texte[position].isspace():
            position += 1
        if position == len(texte):
            return valeurs
        valeur, position = decodeur.raw_decode(texte, position)
        if cle is not None:
            valeur = valeur[cle]
        valeurs.extend(valeur if isinstance(valeur, list) else [valeur])


def commande(argv):
    """Sous-commandes « depassees » et « robot » ; None si argv n'en est pas une."""
    if len(argv) == 4 and argv[1] == "depassees":
        prs = lire_flux_json(sys.stdin.read())
        for numero in prs_depassees(prs, argv[2], argv[3]):
            print(numero)
        return 0
    if len(argv) in (3, 4) and argv[1] == "robot":
        commits = lire_flux_json(sys.stdin.read(), argv[3] if len(argv) == 4 else None)
        print("robot" if commits_du_robot(commits, argv[2]) else "humain")
        return 0
    return None


def main(argv):
    if len(argv) > 1 and argv[1] in ("depassees", "robot"):
        try:
            code = commande(argv)
        except (ValueError, KeyError, TypeError, AttributeError) as erreur:
            print("✗ JSON inattendu : " + str(erreur), file=sys.stderr)
            return 1
        if code is not None:
            return code
        print(__doc__, file=sys.stderr)
        return 2
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
