"""Page HTML du tableau de couverture, à partir de out/couverture.json (tools/couverture.py)."""
import json, os, html
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = json.load(open(os.path.join(HERE, "out", "couverture.json"), encoding="utf-8"))
H = D["heros"]
E = html.escape
SHORT = {"ondine":"Ondine","basile":"Basile","pistil":"Pistil","brisefer":"Brisefer","zephyrin":"Zéphyrin","griselidis":"Grisélidis","pelagie":"Pélagie","barnabe":"Barnabé","anatole":"Anatole","president":"Le Président","platine":"Platine","ploum":"Ploum"}

def cell(p, extra=""):
    if not p:
        return '<td class="no" aria-label="non"></td>'
    lvl = 3 if p >= 50 else 2 if p >= 10 else 1
    return f'<td class="yes l{lvl}" title="{p} % des parties">✕{extra}</td>'

def head():
    return "<tr><th class='row'></th>" + "".join(
        f"<th class='h' title='{E(h['nom'])}'><span>{E(SHORT.get(h['id'], h['nom']))}</span>{'<small>après ' + str(h['deblocage']) + ' partie' + ('s' if h['deblocage'] > 1 else '') + '</small>' if h['deblocage'] else ''}</th>" for h in H) + "</tr>"

def block(title, rows, note=""):
    out = [f"<tr class='sec'><th class='row' colspan='{len(H) + 1}'>{E(title)}{('<span>' + E(note) + '</span>') if note else ''}</th></tr>"]
    out += rows
    return "".join(out)

# résumé
summary = []
for label, f in [
    ("Longueur moyenne (choix)", lambda h: f"<b>{h['longueur']['moy']}</b>"),
    ("Plus court, plus long", lambda h: f"{h['longueur']['min']}–{h['longueur']['max']}"),
    ("Scènes différentes vues", lambda h: str(h["noeuds"])),
    ("Lieux", lambda h: str(len(h["lieux"]))),
    ("Compagnons possibles", lambda h: str(len(h["comp"]))),
    ("Objets possibles", lambda h: str(len(h["obj"]))),
    ("Fins possibles", lambda h: str(len(h["fins"]))),
]:
    summary.append(f"<tr><th class='row'>{label}</th>" + "".join(f"<td class='num{' short' if h['longueur']['moy'] < 80 else ''}'>{f(h)}</td>" for h in H) + "</tr>")

lieux = [l for l in D["lieux"] if any(l in h["lieux"] for h in H)]
rows_l = [f"<tr><th class='row'>{E(l)}</th>" + "".join(cell(h["lieux"].get(l, 0)) for h in H) + "</tr>" for l in lieux]
comps = sorted([c for c in D["comp"] if any(c in h["comp"] for h in H)], key=lambda c: D["comp"][c])
rows_c = [f"<tr><th class='row'>{E(D['comp'][c])}</th>" + "".join(cell(h["comp"].get(c, 0)) for h in H) + "</tr>" for c in comps]
objs = sorted([o for o in D["obj"] if any(o in h["obj"] for h in H)], key=lambda o: D["obj"][o])
rows_o = [f"<tr><th class='row'>{E(D['obj'][o])}</th>" + "".join(cell(h["obj"].get(o, 0)) for h in H) + "</tr>" for o in objs]
fins = sorted(D["fins"], key=int)
rows_f = []
for f in fins:
    meta = D["fins"][f]
    tds = "".join(cell(h["fins"][f]["part"], f"<i>{h['fins'][f]['moy']}</i>") if f in h["fins"] else cell(0) for h in H)
    rows_f.append(f"<tr><th class='row'><em class='k {meta['ton'].replace(' ', '-')}'>{f}</em>{E(meta['titre'])}</th>{tds}</tr>")

never = [f"{f} « {D['fins'][f]['titre']} »" for f in fins if not any(f in h["fins"] for h in H)]
rare = []
for h in H:
    for f, v in h["fins"].items():
        if v["part"] < 1:
            rare.append(f"{h['nom']} : fin {f} ({v['part']} %)")

page = f"""<title>Couverture des héros</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Young+Serif&family=Spectral:ital,wght@0,400;0,600;1,400&family=IBM+Plex+Mono:wght@400;600&display=swap">
<style>
/* Mise en page : un registre d'astronome, une grille héros × éléments du monde, en-tête collant à gauche */
:root{{--bg:#f4f2ec;--ink:#1b2135;--muted:#5d6479;--line:#d6d3c8;--gold:#9a7a2c;--tide:#2f7d86;--fill1:#e3eef0;--fill2:#b9d9dd;--fill3:#7fbcc4;--warn:#b5523b;
--f-disp:"Young Serif",Georgia,serif;--f-body:"Spectral",Georgia,serif;--f-data:"IBM Plex Mono",ui-monospace,monospace}}
@media (prefers-color-scheme:dark){{:root:not([data-theme="light"]){{--bg:#0d1120;--ink:#ece7da;--muted:#a3a8bb;--line:#2a3150;--gold:#e0c27a;--tide:#7cc6cf;--fill1:#16283a;--fill2:#1d4656;--fill3:#2f7486;--warn:#ef8d72;color-scheme:dark}}}}
:root[data-theme="dark"]{{--bg:#0d1120;--ink:#ece7da;--muted:#a3a8bb;--line:#2a3150;--gold:#e0c27a;--tide:#7cc6cf;--fill1:#16283a;--fill2:#1d4656;--fill3:#2f7486;--warn:#ef8d72;color-scheme:dark}}
body{{background:var(--bg);color:var(--ink);font-family:var(--f-body);font-size:16px;line-height:1.5;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px));padding-block:28px 48px}}
.wrap{{max-width:1240px;margin:0 auto;display:grid;gap:28px}}
h1{{font-family:var(--f-disp);font-weight:400;font-size:clamp(28px,4vw,40px);margin:0;text-wrap:balance}}
h2{{font-family:var(--f-disp);font-weight:400;font-size:22px;margin:0 0 10px}}
.lede{{max-width:68ch;color:var(--muted);margin:6px 0 0}}
.legend{{display:flex;flex-wrap:wrap;gap:8px 18px;font-family:var(--f-data);font-size:12px;color:var(--muted)}}
.legend span{{display:inline-flex;align-items:center;gap:6px}}
.sw{{width:18px;height:14px;border:1px solid var(--line);display:inline-block}}
.scroll{{overflow-x:auto;border:1px solid var(--line);border-radius:4px;min-width:0}}
table{{border-collapse:collapse;font-family:var(--f-data);font-size:12.5px;font-variant-numeric:tabular-nums;width:100%}}
th,td{{border-bottom:1px solid var(--line);padding:5px 8px;text-align:center;white-space:nowrap}}
th.row{{text-align:left;font-family:var(--f-body);font-size:14px;font-weight:400;position:sticky;left:0;background:var(--bg);z-index:1;max-width:300px;white-space:normal;min-width:220px}}
th.h{{width:76px;font-family:var(--f-body);font-weight:600;font-size:13px;vertical-align:bottom;padding-top:12px;position:sticky;top:0;background:var(--bg)}}
th.h span{{display:block}} th.h small{{display:block;font-family:var(--f-data);font-weight:400;font-size:10.5px;color:var(--gold)}}
tr.sec th{{background:var(--bg);font-family:var(--f-data);font-size:11px;letter-spacing:.12em;text-transform:uppercase;color:var(--tide);padding-top:18px;border-bottom:2px solid var(--tide)}}
tr.sec th span{{margin-left:12px;letter-spacing:0;text-transform:none;color:var(--muted)}}
td.yes{{color:var(--ink);font-weight:600}} td.l1{{background:var(--fill1)}} td.l2{{background:var(--fill2)}} td.l3{{background:var(--fill3)}}
td.yes i{{font-style:normal;font-weight:400;font-size:11px;color:var(--muted);margin-left:6px}}
td.num b{{font-size:15px}} td.short b{{color:var(--warn)}}
em.k{{font-style:normal;font-family:var(--f-data);font-size:11px;display:inline-block;min-width:22px;margin-right:8px;color:var(--muted)}}
em.k.lumineuse{{color:var(--tide)}} em.k.sombre{{color:var(--warn)}} em.k.ironique,em.k.douce-amère{{color:var(--gold)}}
.notes{{display:grid;gap:8px;max-width:75ch}} .notes ul{{margin:0;padding-left:20px}} .notes li{{margin:4px 0}}
</style>
<div class="wrap">
<header>
<h1>La Lune vendue, héros par héros</h1>
<p class="lede">Pour chaque héros jouable : les lieux traversés, les compagnons qu'on peut avoir, les objets qu'on peut trouver et les fins qu'on peut atteindre. Mesuré sur {2 * 1500} parties simulées par héros, avec les vraies règles du jeu (dés, conditions, compagnons) : la moitié en choisissant au hasard, l'autre moitié en préférant les choix rares.</p>
</header>
<div class="legend"><span><i class="sw" style="background:var(--fill3)"></i>dans plus de la moitié des parties</span><span><i class="sw" style="background:var(--fill2)"></i>de 10 à 50 %</span><span><i class="sw" style="background:var(--fill1)"></i>moins de 10 %</span><span>Fins : le petit nombre est la longueur moyenne du chemin, en choix</span><span>Survoler une case donne le pourcentage</span></div>
<div class="scroll"><table>
<thead>{head()}</thead>
<tbody>
{block("Résumé", summary, "en rouge : les histoires trop courtes")}
{block("Lieux", rows_l)}
{block("Compagnons", rows_c)}
{block("Objets", rows_o)}
{block("Fins", rows_f)}
</tbody></table></div>
<section class="notes">
<h2>À retenir</h2>
<ul>
<li>Les neuf héros de départ font de {min(h['longueur']['moy'] for h in H[:9])} à {max(h['longueur']['moy'] for h in H[:9])} choix par partie. Le Président, Platine et Ploum en font {', '.join(str(h['longueur']['moy']) for h in H[9:])} : ce sont eux qu'il faut rallonger.</li>
<li>Les nouveaux héros ne passent que par quelques lieux et n'ont presque pas d'objets : leurs histoires ne croisent pas encore le reste du monde.</li>
{''.join('<li>Fin jamais atteinte en simulation : ' + E(x) + '.</li>' for x in never)}
{('<li>Fins très rares (moins d’une partie sur cent) : ' + E('; '.join(rare)) + '.</li>') if rare else ''}
</ul>
</section>
</div>
"""
open(os.path.join(HERE, "out", "couverture.html"), "w", encoding="utf-8").write(page)
print("écrit out/couverture.html")
