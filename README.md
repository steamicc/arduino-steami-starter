# Starter STeaMi pour Arduino

Modèle de dépôt pour programmer la carte [STeaMi](https://github.com/steamicc) en Arduino depuis un Codespace, sans rien installer : tout est dans l'image du Codespace, et compiler ne demande pas d'accès réseau.

## 1. Créer votre dépôt

1. Sur cette page, cliquez sur **« Use this template »**.
2. Choisissez **« Create a new repository »**, donnez-lui un nom, puis validez.

N'utilisez **pas** « Open in a codespace » : votre travail ne serait pas sauvegardé dans un dépôt à vous.

## 2. Ouvrir un Codespace

Dans **votre** nouveau dépôt : **Code** → onglet **Codespaces** → **Create codespace on main**. Le premier démarrage prend un moment.

## 3. Les commandes

À taper dans le terminal du Codespace :

| Commande | Rôle |
| --- | --- |
| `steami-exemples [filtre]` | liste les exemples, sous la forme `driver/Exemple` (par exemple `steami-exemples lis2mdl`) |
| `steami-compiler [driver/Exemple]` | compile votre programme (`src/`), ou un exemple tel quel (`steami-compiler lis2mdl/BasicReader`) |
| `steami-copier [--remplacer] driver/Exemple` | copie un exemple dans `src/` pour le modifier |
| `steami-televerser` | prépare l'envoi du programme vers la carte |
| `steami-sauver ["message"]` | sauvegarde votre travail sur GitHub |

Ces actions existent aussi dans le menu **Terminal** → **Run Task…** (« STeaMi : compiler », etc.).

Pour commencer : lancez `steami-compiler`. Le programme de départ (`src/main.cpp`) fait clignoter la LED verte et écrit `Bonjour STeaMi !` puis un compteur sur la liaison série.

## 4. Envoyer le programme sur la carte

Après `steami-compiler`, lancez `steami-televerser`, puis choisissez l'une des deux méthodes :

- **La page « Téléverser »** (Chrome ou Edge) : ouvrez l'adresse affichée, branchez la carte en USB et suivez la page. Elle affiche aussi la console série.
- **Le glisser-déposer** : dans l'explorateur de fichiers, clic droit sur `.steami/firmware.bin` → **Download**, puis glissez le fichier sur le lecteur **STEAMI**.

## 5. Sauvegarder et arrêter

- `steami-sauver "mon message"` enregistre votre travail sur GitHub.
- En fin de séance, arrêtez le Codespace (indicateur « Codespaces » en bas à gauche, puis « Stop Current Codespace ») : un Codespace allumé consomme votre quota.

## Aller plus loin

Documentation complète : <https://wiki.steami.cc/docs/software/arduino/codespace>
