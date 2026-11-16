"""Prépare les médaillons : python3 tools/medaillons.py <dossier des images> compagnons|objets

Chaque image (png, jpg ou webp) est recadrée au carré, réduite à 256 px et écrite en WebP
dans img/<compagnons|objets>/<id>.webp. Le nom du fichier source doit commencer par l'identifiant
(bartho.png, obj_aiguille.png) ou par le nom affiché dans le jeu (« Zouzou.png », « La boussole des choses perdues.png »).
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
dst = os.path.join(HERE, "img", kind); os.makedirs(dst, exist_ok=True)
for f in sorted(os.listdir(src)):
    base, ext = os.path.splitext(f)
    if ext.lower() not in (".png", ".jpg", ".jpeg", ".webp"): continue
    key = base if base in table or base == "croissant" else by_name.get(norm(base.split(" - ")[-1]))
    if not key: print("ignoré (nom inconnu) :", f); continue
    im = Image.open(os.path.join(src, f)).convert("RGB"); s = min(im.size)
    im = im.crop(((im.width - s) // 2, (im.height - s) // 2, (im.width + s) // 2, (im.height + s) // 2)).resize((256, 256), Image.LANCZOS)
    im.save(os.path.join(dst, key + ".webp"), "WEBP", quality=78); print(f, "->", key)
