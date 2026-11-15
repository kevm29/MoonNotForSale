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
| `img/personnages/` | Portraits des fiches (`<id>.webp`, intégrés au HTML par `build.py`) |
| `pack.py` | Écrit les pages autonomes dans `docs/` (Cytoscape intégré) |
| `docs/` | Ce que publie GitHub Pages : `index.html` (le jeu) et `carte.html` |
| `vendor_cytoscape.min.js` | Cytoscape.js 3.28.1 (licence MIT), pour la carte hors ligne |
| `tools/` | Outils d'audit et de relecture |
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
