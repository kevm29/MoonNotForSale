"""Prépare les médaillons : python3 tools/medaillons.py <dossier des images> compagnons|objets

Chaque image (png, jpg ou webp) est recadrée au carré, réduite à 256 px et écrite en WebP
dans img/<compagnons|objets>/<id>.webp. Le nom du fichier source doit commencer par l'identifiant
(bartho.png, obj_aiguille.png), par le nom des dessins (Obj_Croc.png, Perso_Ysolde.png) ou par le nom affiché dans le jeu (« Zouzou.png », « La boussole des choses perdues.png »).
"""
import json, os, sys, unicodedata
from PIL import Image

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src, kind = sys.argv[1], sys.argv[2]
meta = json.load(open(os.path.join(HERE, "meta.json"), encoding="utf-8"))
table = meta["companions"] if kind == "compagnons" else meta["items"]
norm = lambda s: "".join(c for c in unicodedata.normalize("NFD", s.lower()) if c.isalnum())
by_name = {norm(v["name"]): k for k, v in table.items()}
by_name[norm("Le petit Croissant")] = "croissant"
# Noms des fichiers dessinés par Kevin (Obj_Xxx.png, Perso_Xxx.png)
ALIAS = {
 "obj_couverture": "obj_couverture", "obj_croc": "obj_croc_argent", "obj_dernieregoutte": "obj_goutte",
 "obj_echobouteille": "obj_echo", "obj_eclateclipse": "obj_eclipse", "obj_etoilefilante": "obj_etoile",
 "obj_facettequartz": "obj_facette", "obj_fleurcactus": "obj_fleur_epine", "obj_glandchene": "obj_graine_lune",
 "obj_herbier": "obj_herbier", "obj_lanternemeduse": "obj_lanterne", "obj_lettrevent": "obj_lettre_vent",
 "obj_metre": "obj_metre", "obj_miroirplatine": "obj_miroir_platine", "obj_mouton": "obj_mouton",
 "obj_neveupresident": "obj_neveu_galet", "obj_oreiller": "obj_oreiller", "obj_plumeheron": "obj_plume",
 "obj_racine": "obj_brin_toile", "obj_sablier": "obj_sablier", "obj_tampon": "obj_tampon_vu",
 "obj_ticketzero": "obj_ticket_zero", "obj_aiguille": "obj_aiguille", "obj_aurorepliee": "obj_aurore",
 "obj_ballonsoie": "obj_ballon", "obj_beignet": "obj_beignet", "obj_berceau": "obj_berceau_nuage",
 "obj_billemarbre": "obj_bille", "obj_boussole": "obj_boussole", "obj_braise": "obj_braise",
 "obj_cartepostale": "obj_carte", "obj_casquechantier": "obj_casque", "obj_cauchemarplatine": "obj_cauchemar",
 "obj_clefgrue": "obj_cle_grue", "obj_cleremontage": "obj_cle_remontage", "obj_coquillageenvers": "obj_coquillage",
 "obj_coquilledecroissant": "obj_coquille", "obj_cornebrume": "obj_corne_brume",
 "perso_brumelucie": "brume", "perso_choeurmeduses": "meduses", "perso_coquille": "coquille",
 "perso_croissant": "croissant", "perso_echo": "echo", "perso_fernand": "fernand", "perso_fulgence": "fulgence",
 "perso_melusine": "melusine", "perso_ombrelune": "gaspard", "perso_ondee": "ondee", "perso_pardon": "pardon",
 "perso_pli": "pli", "perso_plumard": "plumard", "perso_remontoir": "remontoir", "perso_rocambole": "rocambole",
 "perso_tampon": "penelope", "perso_taupinel": "taupinel", "perso_vasequeuse": "bartho",
 "perso_vesperine": "vesperine", "perso_ysaline": "ysaline", "perso_ysolde": "quartz", "perso_zouzou": "zouzou",
}
dst = os.path.join(HERE, "img", kind); os.makedirs(dst, exist_ok=True)
for f in sorted(os.listdir(src)):
    base, ext = os.path.splitext(f)
    if ext.lower() not in (".png", ".jpg", ".jpeg", ".webp"): continue
    a = "".join(c for c in unicodedata.normalize("NFD", base.lower()) if c.isalnum() or c == "_")
    key = base if base in table or base == "croissant" else ALIAS.get(a) or by_name.get(norm(base.split(" - ")[-1]))
    if key and key not in table and key != "croissant": key = None
    if not key: print("ignoré (nom inconnu) :", f); continue
    im = Image.open(os.path.join(src, f)).convert("RGB"); s = min(im.size)
    im = im.crop(((im.width - s) // 2, (im.height - s) // 2, (im.width + s) // 2, (im.height + s) // 2)).resize((256, 256), Image.LANCZOS)
    im.save(os.path.join(dst, key + ".webp"), "WEBP", quality=78); print(f, "->", key)
