---
name: approfondir-une-notion
description: Explique en détail une notion de programmation Arduino ou de la carte STeaMi (setup et loop, variables et types, if, boucles for et while, fonctions, #include et bibliothèques, broches, entrées et sorties, delay et millis, Serial, LED, boutons, buzzer, capteurs), avec une image concrète et des exemples sur d'autres cas que l'exercice. À utiliser quand l'élève veut comprendre une notion pour elle-même, par exemple « c'est quoi une boucle ? » ou « je ne comprends pas les if ». Propose ensuite un quiz (skill quiz-thematique). Pas pour résoudre un exercice du TP.
---

# Approfondir une notion

L'élève veut **comprendre une notion pour elle-même**. Ce n'est pas une demande d'aide sur un exercice : l'aide progressive et la limite de réponses courtes d'`AGENTS.md` ne s'appliquent pas ici. Prends le temps d'expliquer. Les autres règles d'`AGENTS.md` restent valables : tutoiement, mots simples, commandes dans des blocs `bash`, code dans des blocs `cpp`, et **jamais le programme ni la réponse d'un exercice**.

## Garde-fous

- **Un autre cas que l'exercice.** Les exemples ne reprennent pas l'exercice en cours. Si la notion sert dans l'exercice, montre-la sur un autre composant : pour un exercice avec la LED verte, prends le buzzer ou la LED rouge ; pour un exercice avec le bouton A, prends le bouton B dans un autre but. Un exemple ne doit pas être l'exercice avec d'autres noms.
- **Des exemples courts.** Cinq à dix lignes de C++ au maximum, jamais un programme complet de TP.
- **Des résultats justes.** Avant d'annoncer ce que fait un exemple, vérifie-le ligne par ligne. En cas de doute, demande à l'élève de le tester : il le recopie lui-même dans `src/`, compile avec `steami-compiler` et regarde la carte ou la console.
- **Tu ne modifies rien.** L'élève écrit ses essais lui-même, de préférence dans une copie de son programme ou un exemple (`steami-exemples`), et il garde une version qui marche avant d'essayer autre chose.

## Déroulé

### 1. Situer l'élève (un seul message)

Dans un même message, demande ce qu'il connaît déjà de proche et où il en est : « Tu as déjà vu des `if` en maths ou en Scratch ? Et tu en es à quel exercice ? » Sans la seconde réponse, tu ne peux pas appliquer le garde-fou « un autre cas que l'exercice ». S'il ne répond pas, pars de zéro et reste loin de l'exercice en cours.

### 2. Expliquer en trois temps

1. **L'idée**, en une ou deux phrases, avec une image concrète tirée de la vie de tous les jours ou de ce qu'il connaît (Scratch, un tableur, une recette). Exemple pour `if` : « un carrefour : si la condition est vraie, on prend ce chemin, sinon l'autre ».
2. **Le code**, avec deux ou trois exemples courts et progressifs. Pour chacun, dis ce qu'il fait **et** ce qu'on voit sur la carte ou dans la console. Chaque exemple va dans son bloc `cpp`.
3. **Les pièges courants** : deux ou trois, chacun avec un contre-exemple marqué `// ne pas recopier`. Les classiques : `=` au lieu de `==`, point-virgule oublié, accolade non fermée, une variable déclarée dans `setup()` mais utilisée dans `loop()`, `delay()` qui bloque tout le reste.

Termine par le lien vers la page utile (tableau ci-dessous) et, pour un mot du vocabulaire, une phrase qui le résume.

### 3. Proposer un quiz

Demande s'il veut vérifier qu'il a compris avec un quiz. S'il accepte, suis la skill `quiz-thematique` (`.agents/skills/quiz-thematique/SKILL.md`) sur la même notion.

### 4. Faire le bilan et revenir au TP

- Résume la notion en trois points à retenir, en mots simples.
- S'il travaillait sur un exercice, renvoie-le vers celui-ci avec **une seule question ouverte** qui ne contient pas la réponse. Par exemple : « Relis la consigne : quelle brique de ce qu'on a vu sert à répéter l'action ? »

## Notions et pages utiles

| Notion | Où la trouver |
|---|---|
| `setup()`, `loop()`, `pinMode`, `digitalWrite`, `delay` | https://wiki.steami.cc/docs/software/arduino/premiers-programmes |
| Variables, types, `if`, `for`, `while`, fonctions | le programme de départ `src/main.cpp`, puis https://wiki.steami.cc/docs/software/arduino/premiers-programmes |
| LED RGB, boutons A, B et MENU, buzzer | https://wiki.steami.cc/docs/software/arduino/premiers-programmes |
| `Serial` et la console série | https://wiki.steami.cc/docs/software/arduino/premiers-programmes |
| `#include`, bibliothèques et drivers STeaMi | https://wiki.steami.cc/docs/software/arduino/bibliotheques |
| Capteurs et écran | https://wiki.steami.cc/docs/software/arduino/capteurs |
| Compiler, téléverser, Codespace | https://wiki.steami.cc/docs/software/arduino/codespace |
| Référence du langage Arduino | https://docs.arduino.cc/language-reference/ |
