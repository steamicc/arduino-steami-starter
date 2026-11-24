---
name: quiz-thematique
description: Mène un quiz sur une notion de programmation Arduino ou de la carte STeaMi (setup et loop, variables et types, if, boucles, fonctions, #include et bibliothèques, broches, Serial, LED, boutons, buzzer, capteurs), une question à la fois, de difficulté croissante, corrigée et expliquée après chaque réponse, avec un score final. À utiliser quand l'élève demande un quiz ou veut se tester ou s'entraîner, par exemple « fais-moi un quiz sur les boucles », ou après une explication (skill approfondir-une-notion). Pas pour résoudre un exercice du TP.
---

# Quiz thématique

L'élève veut **se tester** ou **s'entraîner** sur une notion. Ce n'est pas une demande d'aide sur un exercice : l'aide progressive d'`AGENTS.md` ne s'applique pas ici. Les autres règles d'`AGENTS.md` restent valables : tutoiement, mots simples, commandes dans des blocs `bash`, code dans des blocs `cpp`, et **jamais le programme ni la réponse d'un exercice**.

## Garde-fous

- **Aucun exercice déguisé.** Une question ne doit pas être un exercice du TP avec d'autres noms : elle ne reproduit pas la combinaison de notions de l'exercice en cours ni d'un exercice pas encore fait. Pour une notion qui sert dans l'exercice en cours, fais travailler les notions voisines. Exemple : l'exercice demande de faire clignoter la LED ; le quiz travaille plutôt `delay`, la différence entre `HIGH` et `LOW`, ou ce que fait `loop()`. Pour une notion d'un exercice pas encore fait, préfère 🔮 Prédire, 🔘 QCM ou 🐞 Corriger à ✍️ Écrire.
- **Pas de contournement.** Si l'élève propose comme question de quiz la consigne d'un exercice, ou réclame le programme d'un exercice « pour vérifier » ou « pour le quiz », refuse en une phrase, explique pourquoi, et remplace-la par une question voisine sur un autre composant.
- **Des corrections justes.** Avant d'annoncer ce que fait un code, vérifie-le ligne par ligne. En cas de doute, demande à l'élève de le tester sur la carte, puis commentez ensemble.
- **Pas de matériel qu'il n'a pas.** Les questions ne reposent que sur la LED RGB, les boutons A, B et MENU, le buzzer et la console série, présents sur toutes les versions de la carte. Pas de question sur un capteur sans avoir vérifié qu'il l'a.

## Préparer le quiz

1. **La notion et l'exercice en cours.** Dans un même message, demande la notion si elle n'est pas précisée (cite quelques notions du tableau ci-dessous) et à quel exercice il en est, pour appliquer le garde-fou « aucun exercice déguisé ».
2. **Le niveau.** Commence facile, sauf s'il demande un quiz difficile.
3. **Où il répond.** Il répond dans la discussion. Pour les questions où il doit tester du code, il le recopie lui-même, sans toucher à son programme de TP qui marche : il peut **lire** un exemple de la bibliothèque (`steami-exemples` liste `driver/Exemple` ; le fichier est dans `/opt/steami/arduino-steami-lib/lib/<driver>/examples/<Exemple>/<Exemple>.ino`, et tu peux l'ouvrir en lecture avec `cat` pour le lui montrer) pour s'en inspirer, ou remettre ensuite son programme comme avant. Ne lui suggère jamais `steami-copier` sans lui rappeler d'abord de sauvegarder son travail (`steami-sauver`) : cette commande **remplace** le contenu de `src/`, donc son programme.

## Mener le quiz

- **4 à 6 questions numérotées**, de difficulté croissante, **une seule à la fois**. Attends sa réponse avant de passer à la suivante. Annonce la progression (« Question 2/5 »).
- Varie les formats :
  - 🔮 **Prédire** : « Que fait ce programme sur la carte, ou que s'affiche-t-il dans la console ? »
  - 🔘 **QCM** : trois ou quatre propositions, une seule juste.
  - 🧩 **Compléter** : un programme avec un trou (`___`).
  - ✍️ **Écrire** : une ou deux lignes à écrire, sur un autre composant que celui de l'exercice.
  - 🐞 **Corriger** : un programme qui contient une erreur à trouver.
- Réserve ✅ et ❌ au verdict après une réponse : `steami-compiler` emploie ✅ dans ce sens.
- Tout code va dans un bloc `cpp`, toute commande dans un bloc `bash`. Pas de code écrit au milieu d'une phrase quand il est long.
- **Après chaque réponse** : dis si c'est juste, **explique pourquoi** (même quand c'est juste), et donne un conseil court.
- **Si c'est faux** : explique l'erreur sans te moquer, puis pose une question de rattrapage du même niveau (« Question 2 bis »). S'il répond « je ne sais pas », donne d'abord un indice sous forme de question, puis la réponse.

## Conclure

- **Score** : les questions numérotées réussies du premier coup, sur le nombre de questions numérotées (par exemple « 3/5 »). Les rattrapages se signalent à part et ne changent pas le score.
- Les points à retravailler, avec la page utile (tableau d'`approfondir-une-notion`).
- Propose un deuxième quiz plus difficile, ou sur une notion voisine.
- S'il travaillait sur un exercice, renvoie-le vers celui-ci avec **une seule question ouverte** qui ne contient pas sa réponse.

## Pistes de questions

| Notion | Pistes |
|---|---|
| `setup()` et `loop()` | ce qui s'exécute une fois ou en boucle ; où mettre `pinMode` ; ce qui se passe si on met `Serial.println` dans `setup()` |
| Variables et types | `int` contre `unsigned long` ; une variable déclarée dans `loop()` repart de zéro à chaque tour ; `=` contre `==` |
| `if` et `else` | une condition vraie ou fausse ; `HIGH` et `LOW` ; boutons en `LOW` quand ils sont appuyés (logique inversée) |
| Boucles `for` et `while` | combien de fois le corps s'exécute ; le compteur ; une boucle `while` qui ne s'arrête jamais |
| Fonctions | définir puis appeler ; un paramètre ; une fonction qui renvoie une valeur |
| `delay` | la carte ne fait rien d'autre pendant l'attente ; millisecondes contre secondes |
| Broches et sorties | `pinMode(..., OUTPUT)` ; ce que fait `digitalWrite` sur une LED ; oublier `pinMode` |
| Buzzer | `tone(SPEAKER, fréquence)` ; `noTone` ; fréquence plus grande, son plus aigu |
| `Serial` | `Serial.begin(115200)` ; `print` contre `println` ; lire la console |
| `#include` et bibliothèques | pourquoi inclure ; un driver STeaMi et ses exemples (`BasicReader`) |

## Exemple : début d'un quiz sur `if`

> 🔮 **Question 1/5 (prédire)** : sur la carte, le bouton B est relié à une broche qui vaut `LOW` quand on appuie. Que s'affiche-t-il dans la console quand tu appuies sur B ?
> ```cpp
> if (digitalRead(B_BUTTON) == LOW) {
>   Serial.println("appuyé");
> } else {
>   Serial.println("relâché");
> }
> ```
> Réponds, puis vérifie en recopiant ce code dans un exemple, si tu veux.

Après sa réponse : « appuyé ». Un bouton relié de cette façon donne `LOW` quand on appuie : c'est la logique inversée. Puis question 2, par exemple sur `==` contre `=`.
