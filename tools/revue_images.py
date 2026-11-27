"""Page de revue des images : python3 tools/revue_images.py  ->  docs/revue-images.html (ouvrir à côté de docs/img/lieux).
Une ligne par scène, dans l'ordre de l'histoire (parcours depuis le départ) : identifiant, vignette, lieu, origine de l'image,
début du texte (le texte entier se déplie). Filtres : histoire, image, drapeaux. Drapeaux :
  provisoire = image à créer pas encore générée ; défaut = image du lieu (pas de variante propre) ;
  suspect = texte et lieu en désaccord ou image réservée hors contexte (mêmes règles que images_check.py)."""
import os, re, json, glob, html, collections
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); os.chdir(HERE)
src = open("build.py", encoding="utf-8").read().split("\ndef main")[0]
b = {"__file__": os.path.join(HERE, "build.py")}; exec(compile(src, "build.py", "exec"), b)
nodes, order = b["parse"](sorted(glob.glob("src/*.txt")))
L = json.load(open("lieux.json", encoding="utf-8"))
nmap, names, inf = b["resolve_lieux"](L, nodes, order)
for a in L.get("a_creer", []): names[a["image"]] = a["nom"]
ctl = L["controle"]; revues = ctl.get("revues", {})
sig = {i: re.compile(p, re.I) for i, p in ctl["signatures"].items()}
fam = [set(f) for f in ctl.get("familles", [])]
same = lambda a, c: a == c or any(a in f and c in f for f in fam)
files = {os.path.basename(f)[:-5] for f in glob.glob("img/lieux/*.webp")}
HEROES = {"Président": ("gpa_01", "gpa gtr gal gco gfo gfi gmo gpr gnu"), "Ploum": ("ply_01", "ply plu pcm pcr pso pct pha pnu pch pmo"),
          "Pistil": ("pis_01", "pis pne pnc pno"), "Platine": ("pla_01", "pla plt plf")}
def parcours(start):
    seen, q = [], [start]; vu = {start}
    while q:
        n = q.pop(0); seen.append(n)
        for c in nodes[n]["choices"]:
            if c["to"] and c["to"] in nodes and c["to"] not in vu: vu.add(c["to"]); q.append(c["to"])
    return seen
a_creer = {s.strip(): a for a in L.get("a_creer", []) for s in a["scenes"].split(",")}
count = collections.Counter(); data = {}
for h, (start, ps) in HEROES.items():
    ps = ps.split(); lst = [n for n in parcours(start) if n.split("_")[0] in ps or n.startswith("end_")]
    data[h] = lst
    for n in lst: count[nmap.get(n)] += 1
def flags(n):
    img = nmap.get(n); f = []
    if not img: return ["sans image"]
    if n in a_creer and img != a_creer[n]["image"]: f.append("provisoire")
    if n not in inf["singles"] and n not in inf["ranges"] and n not in a_creer: f.append("défaut")
    for i, pats in ctl["reserve"].items():
        if img == i and not any(re.search(p, n) for p in pats): f.append("suspect : image réservée")
    t = " ".join([nodes[n].get("title", "")] + [l["t"] for l in nodes[n]["lines"][:2]])
    if not any(r.search(t) for i, r in sig.items() if same(i, img)):
        ev = [i for i, r in sig.items() if not same(i, img) and r.search(t)]
        if ev and n not in revues: f.append("suspect : le texte évoque " + names.get(ev[0], ev[0]))
    return f
def row(h, n):
    nd = nodes[n]; img = nmap.get(n); fl = flags(n)
    txt = [l["t"] for l in nd["lines"]]
    head = html.escape(" ".join(txt[:2])[:260]); full = "<br>".join(html.escape(t) for t in txt)
    imgtag = f'<img loading="lazy" src="img/lieux/{img}-800.webp" alt="">' if img in files else '<div class="nofile">pas de fichier</div>'
    badges = "".join(f'<span class="b {"s" if "suspect" in x else "p" if x == "provisoire" else "d"}">{html.escape(x)}</span>' for x in fl)
    return (f'<tr data-h="{h}" data-img="{img}" data-f="{"|".join(fl)}"><td class="id">{n}<br><small>{html.escape(nd.get("title", ""))}</small></td>'
            f'<td class="im">{imgtag}<div class="lieu">{img} · {html.escape(names.get(img, ""))} <span class="b n">×{count[img]}</span></div></td>'
            f'<td>{badges}<details><summary>{head}…</summary><p>{full}</p></details></td></tr>')
body = "\n".join(row(h, n) for h in data for n in data[h])
imgs = sorted({nmap[n] for l in data.values() for n in l if n in nmap})
opt = "".join(f'<option value="{i}">{i} · {html.escape(names.get(i, ""))}</option>' for i in imgs)
page = f'''<!doctype html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Revue des images de lieux</title><style>
body{{font:14px/1.4 system-ui,sans-serif;margin:0;background:#14161f;color:#e8e6df}}
header{{position:sticky;top:0;background:#1d2030;padding:8px 12px;z-index:2;display:flex;gap:8px;flex-wrap:wrap;align-items:center}}
select,button{{background:#2a2f45;color:inherit;border:1px solid #444a66;border-radius:6px;padding:4px 8px}}
table{{border-collapse:collapse;width:100%}}td{{vertical-align:top;padding:6px 10px;border-bottom:1px solid #2a2f45}}
.id{{white-space:nowrap;font-family:monospace;width:150px}}.id small{{font-family:system-ui;color:#9aa}}
.im{{width:260px}}.im img{{width:250px;border-radius:6px;display:block}}.lieu{{font-size:12px;color:#aab}}
.nofile{{width:250px;height:90px;background:#522}}.b{{display:inline-block;border-radius:10px;padding:0 8px;margin:0 4px 4px 0;font-size:12px}}
.s{{background:#a33}}.p{{background:#a73}}.d{{background:#345}}.n{{background:#2a2f45}}summary{{cursor:pointer}}
@media(max-width:700px){{.im{{width:130px}}.im img{{width:120px}}.id{{width:90px}}}}
</style></head><body><header><b>Revue des images</b>
<select id="h"><option value="">Toutes les histoires</option><option>Président</option><option>Ploum</option><option>Pistil</option><option>Platine</option></select>
<select id="i"><option value="">Toutes les images</option>{opt}</select>
<select id="f"><option value="">Tous les nœuds</option><option value="suspect">Suspects</option><option value="provisoire">Provisoires</option><option value="défaut">Image du lieu (défaut)</option></select>
<button id="c">Compacter les vignettes</button><span id="n"></span></header>
<table>{body}</table>
<script>
const rows=[...document.querySelectorAll("tr")],g=id=>document.getElementById(id);
function ap(){{let k=0;rows.forEach(r=>{{const ok=(!g("h").value||r.dataset.h==g("h").value)&&(!g("i").value||r.dataset.img==g("i").value)&&(!g("f").value||r.dataset.f.includes(g("f").value));r.hidden=!ok;if(ok)k++}});g("n").textContent=k+" scènes"}}
["h","i","f"].forEach(i=>g(i).onchange=ap);g("c").onclick=()=>document.querySelectorAll(".im img").forEach(x=>x.style.width=x.style.width?"":"110px");ap();
</script></body></html>'''
open("docs/revue-images.html", "w", encoding="utf-8").write(page)
nsus = sum(1 for l in data.values() for n in l if any("suspect" in x for x in flags(n)))
print("écrit docs/revue-images.html :", {h: len(v) for h, v in data.items()}, "scènes ;", nsus, "suspectes")
