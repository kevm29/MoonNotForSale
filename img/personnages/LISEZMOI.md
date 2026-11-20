# Portraits des personnages jouables

Un fichier carré par personnage, au format WebP, nommé d'après l'identifiant du personnage :

ondine.webp, basile.webp, pistil.webp, brisefer.webp, zephyrin.webp, griselidis.webp, pelagie.webp, barnabe.webp, anatole.webp, president.webp, platine.webp, ploum.webp

`build.py` les intègre dans le HTML (le jeu reste un fichier autonome). Un personnage sans fichier garde un visuel provisoire (initiale sur fond coloré).

Pour ajouter ou remplacer un portrait : réduire l'image à 448 × 448 px, WebP qualité 74 environ (60 Ko), puis `python3 build.py && python3 pack.py`.
