# Moon ~~not~~ for Sale

Un récit à choix dans le style du théâtre de l'absurde. Un promoteur venu d'Aldébaran a acheté la Lune, légalement, avec des pâtisseries. Il y a planté un crochet et commence à l'emporter. Sur la Terre, les marées s'affolent, les rêves s'éteignent et l'Axe penche. Quelqu'un doit monter.

- 9 personnages jouables, 21 compagnons, 38 objets
- environ 770 nœuds à choix, plus de 1 550 choix, 15 fins
- un d20 pour les actions risquées, de l'expérience, deux jauges (Équilibre de la Terre, Moral)

## Jouer

En ligne : **https://kevm29.github.io/MoonNotForSale/** (la carte des embranchements : https://kevm29.github.io/MoonNotForSale/carte.html).

Hors ligne : ouvrez `docs/index.html` dans un navigateur. Le fichier est autonome.

`docs/carte.html` est la carte de tous les embranchements. Elle sert à vérifier la cohérence de l'histoire : cliquez un nœud pour lire son texte, ses choix et d'où l'on y arrive.

## Organisation

| Chemin | Contenu |
|---|---|
| `src/*.txt` | L'histoire, écrite dans un petit langage (voir plus bas) |
| `meta.json` | Personnages, compagnons, objets, fins, réglages des dés |
| `build.py` | Valide l'histoire, simule des milliers de parties, écrit `out/` |
| `game.html`, `tree.html` | Gabarits du jeu et de la carte |
| `img/` | Image d'accueil (`accueil.webp`) et portraits des fiches (`personnages/<id>.webp`), intégrés au HTML par `build.py` |
| `pack.py` | Écrit les pages autonomes dans `docs/` (Cytoscape intégré) |
| `docs/` | Ce que publie GitHub Pages : `index.html` (le jeu) et `carte.html` |
| `vendor_cytoscape.min.js` | Cytoscape.js 3.28.1 (licence MIT), pour la carte hors ligne |
| `lieux.json` | Image de lieu de chaque scène. Les histoires du Président, de Ploum et de Pistil sont « strictes » : une scène sans entrée prend l'image de son préfixe, jamais celle de la scène précédente |
| `tools/images_check.py` | Garde-fou des images, lancé par `build.py` (bloquant) : images réservées, texte et lieu en désaccord, orphelines, provisoires ; écrit `index/images.tsv` |
| `lieux_a_creer.md` | Prompts complets des images de lieux qui manquent (provisoires dans `lieux.json`, clé `a_creer`) |
| `tools/` | Outils d'audit et de relecture |
| `index/` | Index des scènes, régénéré par `tools/index.py` (voir « Trouver une scène ») |
| `tests/` | Tests Playwright dans le navigateur |

## Construire

```sh
python3 build.py   # validation, simulation, out/la-lune-vendue.html et out/arbre-de-decision.html
python3 pack.py    # pages autonomes dans docs/, à committer pour mettre le site à jour
```

## Vérifier

Tous les outils se lancent depuis la racine du dépôt.

```sh
python3 tools/audit2.py 1200        # rejoue des parties : compagnon ou objet cité à tort, blocages, boucles
python3 tools/junctions.py 'cap_'   # nœuds où plusieurs chemins se rejoignent, avec les choix qui y mènent
python3 tools/intro.py              # noms cités sur un chemin où ils n'ont pas été présentés
python3 tools/cycles.py             # boucles du graphe
python3 tools/textcheck.py          # nœuds dont aucun texte ne s'affiche
python3 tools/compscan.py           # compagnons nommés sans condition sur leur présence
python3 tools/dump.py '^hub_0[1-3]$' full   # afficher des nœuds

node tests/parties_hasard.js "$PWD"   # 9 parties au hasard jusqu'à une fin
node tests/parties_ecrans.js "$PWD"   # une partie à 1200 px et une à 390 px
node tests/carte.js "$PWD"            # la carte, sur grand et petit écran
```

## Trouver une scène

`python3 tools/index.py` régénère `index/` (à relancer après toute modification de `src/`). Il ne touche pas à l'histoire.

| Fichier | Une ligne par… |
|---|---|
| `index/scenes.tsv` | nœud : fichier et lignes de chaque morceau (`@` puis `@+`), section, héros, lieu (image), titre, fin, compagnons, objets (`+donné -retiré ?requis`), suites, début du texte |
| `index/scenes.json` | nœud, en détail (une fiche par ligne) : chaque ligne de texte, choix et réplique avec son numéro de ligne, drapeaux posés et testés, d'où l'on vient |
| `index/repliques.tsv` | réplique de compagnon : ligne, nœud, lieu, compagnon, duo (autre compagnon requis), conditions |
| `index/objets.tsv` | usage d'un objet : donné, retiré ou requis, où |
| `index/drapeaux.tsv` | drapeau : posé où, testé où, « jamais testé » / « jamais posé » |
| `index/sections.md` | préfixe d'identifiant → héros, section, lieu par défaut, fichiers |

Pour éditer sans relire les fichiers entiers :

```sh
grep -P '^cot_05\t' index/scenes.tsv            # où est le nœud : 11_cotes.txt:30-34 (+ morceaux @+)
sed -n '30,34p' src/11_cotes.txt                 # lire seulement ces lignes
grep '"id": "cot_05"' index/scenes.json          # la fiche détaillée
awk -F'\t' '$6=="bartho" && $3=="cot"' index/repliques.tsv   # répliques de Bartholomé aux Côtes
awk -F'\t' '$7!=""' index/repliques.tsv         # tous les duos de compagnons
grep obj_gamelle index/objets.tsv                # où l'objet est donné, requis, retiré
```

Les numéros de ligne valent pour l'état des fichiers au moment de la génération : après une modification, relancer `tools/index.py`.

## Le langage de l'histoire

```
@id                       un nœud ; @+id ajoute à un nœud existant
!title: Titre             titre affiché
!fx: effet effet          effets appliqués à l'arrivée
!end: N                   fin numéro N
?cond ?cond texte         ligne affichée si toutes les conditions sont vraies
~compagnon ?cond: texte   réplique d'un compagnon présent
* cible statDIFF ?cond | libellé | texte réussite | texte échec | effets réussite | effets échec
```

- Conditions : `comp:x`, `flag:x`, `pc:x`, `var>=n`, `var<n`, `last:ok|ko`, `from:nœud`, `!` pour la négation.
- **Une virgule veut dire OU** (`?flag:a,flag:b`). Deux conditions séparées (`?flag:a ?flag:b`) veulent dire ET.
- Effets : `+flag:x`, `-flag:x`, `+comp:x`, `-comp:x`, `var+n`, `cond=>effet`.
- Un choix sans caractéristique ou sans texte d'échec se fait sans jet de dé.

## Publication sur GitHub Pages

Le site est servi depuis le dossier `docs/` de la branche `main` (Settings → Pages → Deploy from a branch → `main` / `/docs`). Pour mettre le jeu en ligne après une modification : `python3 build.py && python3 pack.py`, puis committer `docs/` et pousser.

## Images des lieux

`img/lieux/<n°>.webp` (1600 × 600) et `<n°>-800.webp` (800 × 300), numérotées comme le document des prompts des lieux (35-doux / 35-rouge : bureau de Platine, calme ou compte à rebours). `lieux.json` dit quelle image va avec quels nœuds ; un nœud absent garde l'image en cours, ou prend celle de sa section. Les images restent des fichiers à part (chargées à la demande) : `build.py` les copie dans out/, `pack.py` dans docs/.
