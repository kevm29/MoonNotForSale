#!/usr/bin/env python3
"""Index des scènes : une fiche par nœud, avec fichier et lignes, pour trouver
et éditer une scène sans relire les fichiers src/*.txt en entier.

    python3 tools/index.py          # régénère index/ (à relancer après chaque modification de src/)

Écrit dans index/ :
  scenes.tsv      une ligne par nœud : où il est (fichier:début-fin, plusieurs morceaux si @+),
                  section, héros, lieu, titre, compagnons, objets, suites, début du texte
  scenes.json     la même chose en détail (chaque choix et chaque réplique avec sa ligne)
  repliques.tsv   une ligne par réplique de compagnon (~x) : nœud, lieu, compagnon, duo, ligne
  objets.tsv      une ligne par usage d'un objet (obj_*) : donné, retiré, requis
  drapeaux.tsv    une ligne par drapeau : posé où, testé où (repère les drapeaux morts)
  sections.md     les sections (préfixes), leur héros, leur lieu par défaut, leurs fichiers

Ensuite : grep dans index/*.tsv, puis `sed -n 'DEBUT,FINp' src/FICHIER` sur les lignes indiquées.
Ne modifie rien dans src/.
"""
import json, os, re, glob
from collections import defaultdict

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(HERE, "index")

# préfixe -> héros (ou « commun »), libellé de la section
SECTIONS = {
    "ond": ("ondine", "Prologue d'Ondine"), "bas": ("basile", "Prologue de Basile"),
    "pis": ("pistil", "Prologue de Pistil"), "bri": ("brisefer", "Prologue de Brisefer"),
    "zep": ("zephyrin", "Prologue de Zéphyrin"), "gri": ("griselidis", "Prologue de Griselidis"),
    "pel": ("pelagie", "Prologue de Sœur Pélagie"), "lyc": ("barnabe", "Prologue de Barnabé"),
    "ana": ("anatole", "Prologue d'Anatole"),
    "hub": ("commun", "Carrefour"), "foi": ("commun", "Foire"), "cot": ("commun", "Côtes Hagardes"),
    "for": ("commun", "Forêt-Réseau"), "son": ("commun", "Pays des Songes"),
    "pro": ("commun", "Profondeurs"), "cap": ("commun", "Capitale"), "nua": ("commun", "Hauts-Nuages"),
    "com": ("commun", "Comète"), "nui": ("commun", "La nuit"), "asc": ("commun", "Ascension"),
    "cha": ("commun", "Chantier lunaire"), "neg": ("commun", "Négociation"), "fin": ("commun", "Final"),
    "end": ("commun", "Fins"),
    "gpa": ("president", "Président : palais"), "gtr": ("president", "Président : train"),
    "gal": ("president", "Président : Grande Panique / Carrefour"), "gco": ("president", "Président : Côtes Hagardes"),
    "gfo": ("president", "Président : Forêt-Réseau"), "gpr": ("president", "Président : Grand Puits"),
    "gnu": ("president", "Président : Hauts-Nuages"), "gfi": ("president", "Président : dernière nuit"),
    "gmo": ("president", "Président : navette et Lune"),
    "pla": ("platine", "Platine : Aldébaran"), "plt": ("platine", "Platine : incognito sur Terre"),
    "plf": ("platine", "Platine : navette et fin"),
    "plu": ("ploum", "Ploum : début et Carrefour"), "ply": ("ploum", "Ploum : la Lyre"),
    "pha": ("ploum", "Ploum : Hauts-Nuages"), "pcm": ("ploum", "Ploum : Marché des Comètes"),
    "pso": ("ploum", "Ploum : Dortoir / Songes"), "pct": ("ploum", "Ploum : Côtes Hagardes"),
    "pcr": ("ploum", "Ploum : caisse de velours"), "pnu": ("ploum", "Ploum : dernière nuit"),
    "pch": ("ploum", "Ploum : chantier lunaire"), "pmo": ("ploum", "Ploum : Promontoire"),
    "pne": ("pistil", "Pistil, Nuit d'encre : départ"), "pnc": ("pistil", "Pistil, Nuit d'encre : insomnie"),
    "pno": ("pistil", "Pistil, Nuit d'encre : rêve de Platine"),
}

def short(s, n=90):
    s = re.sub(r"\s+", " ", s).strip()
    return s if len(s) <= n else s[: n - 1] + "…"

def conds_of(tokens):
    """Éclate des conditions (virgule = OU, ! = non) en atomes « k:v » ou « var>=n »."""
    out = []
    for c in tokens:
        for part in c.lstrip("!").split(","):
            out.append(part.lstrip("!"))
    return out

def parse(files):
    nodes, order = {}, []
    cur, seg = None, None
    for f in files:
        base = os.path.basename(f)
        lines = open(f, encoding="utf-8").read().split("\n")
        def close(seg):
            if seg is None: return
            seg["end"] = seg["last"]; del seg["last"]
        for ln, line in enumerate(lines, 1):
            if line.startswith("@"):
                close(seg)
                ext = line.startswith("@+")
                nid = line[2 if ext else 1:].strip()
                if not ext and nid not in nodes:
                    nodes[nid] = {"id": nid, "title": "", "end": None, "segments": [], "lines": [],
                                  "quips": [], "choices": [], "fx": []}
                    order.append(nid)
                elif nid not in nodes:  # extension d'un nœud défini plus loin (build.py le refuse)
                    nodes[nid] = {"id": nid, "title": "", "end": None, "segments": [], "lines": [],
                                  "quips": [], "choices": [], "fx": [], "orphan_ext": True}
                    order.append(nid)
                cur = nodes[nid]
                seg = {"file": base, "start": ln, "last": ln, "ext": ext}
                cur["segments"].append(seg)
                continue
            if cur is None or not line.strip() or line.lstrip().startswith("#"):
                continue
            seg["last"] = ln
            where = ln
            if line.startswith("!title:"):
                cur["title"] = line[7:].strip()
            elif line.startswith("!end:"):
                cur["end"] = line[5:].strip()
            elif line.startswith("!fx:"):
                cur["fx"] += [{"e": e, "file": base, "line": where} for e in line[4:].split()]
            elif line.startswith("!"):
                pass
            elif line.startswith("~"):
                m = re.match(r"~(\w+)((?:\s+\?\S+)*)\s*:\s*(.*)", line)
                if m:
                    cur["quips"].append({"c": m.group(1), "if": [x[1:] for x in m.group(2).split()],
                                         "t": m.group(3), "file": base, "line": where})
            elif line.startswith("*"):
                parts = [p.strip() for p in line[1:].split("|")] + [""] * 6
                head = parts[0].split()
                if not head: continue
                stat = None
                conds = []
                for t in head[1:]:
                    if t.startswith("?"): conds.append(t[1:])
                    elif re.match(r"(pan|rus|coe|any)\d+$", t): stat = t
                cur["choices"].append({"to": head[0], "stat": stat if parts[3] else None, "if": conds,
                                       "label": parts[1], "okfx": parts[4].split(), "kofx": parts[5].split(),
                                       "file": base, "line": where})
            else:
                toks = line.split(" ")
                conds = []
                while toks and toks[0].startswith("?") and len(toks[0]) > 1:
                    conds.append(toks.pop(0)[1:])
                cur["lines"].append({"if": conds, "t": " ".join(toks), "file": base, "line": where})
        close(seg); seg = None; cur = None
    return nodes, order

def lieux_map(order, nodes):
    lj = os.path.join(HERE, "lieux.json")
    if not os.path.exists(lj): return {}, {}, {}
    L = json.load(open(lj, encoding="utf-8"))
    nmap, names = {}, {}
    for lieu in L["lieux"]:
        names[lieu["image"]] = lieu["nom"]
        for part in lieu["scenes"].split(","):
            part = part.strip()
            if " à " in part:
                a, b = part.split(" à "); pre = a.split("_")[0]
                lo, hi = int(a.split("_")[1]), int(b.split("_")[1])
                for nid in order:
                    p, _, num = nid.partition("_")
                    if p == pre and num.isdigit() and lo <= int(num) <= hi: nmap[nid] = lieu["image"]
            elif part in nodes: nmap[part] = lieu["image"]
    return nmap, L.get("defauts", {}), names

def name_tokens(full):
    """Mots distinctifs d'un nom, pour repérer qu'il est cité dans un texte."""
    generic = {"Madame", "Monsieur", "Docteur", "Tante", "Oncle", "Grand-Père", "Grand-Mère", "Dame", "Sœur",
               "Frère", "Comtesse", "Maître", "Capitaine", "Petit", "Petite", "Vieux", "Vieille", "Lune"}
    return [w for w in re.findall(r"[A-ZÀ-Ý][\w\-]+", full) if len(w) >= 4 and w not in generic]

def main():
    files = sorted(glob.glob(os.path.join(HERE, "src", "*.txt")))
    nodes, order = parse(files)
    meta = json.load(open(os.path.join(HERE, "meta.json"), encoding="utf-8"))
    comps = meta.get("companions", {})
    items = meta.get("items", {})
    pcs = {p["id"] for p in meta.get("playables", [])}
    nmap, defauts, lnames = lieux_map(order, nodes)
    who = {cid: name_tokens(c.get("name", cid)) for cid, c in comps.items()}
    for n in meta.get("npcs", []):
        who["pnj:" + n["name"]] = name_tokens(n["name"]) or [n["name"]]

    preds = defaultdict(list)
    for nid in order:
        for c in nodes[nid]["choices"]:
            if nid not in preds[c["to"]]: preds[c["to"]].append(nid)

    flags = defaultdict(lambda: {"pose": [], "retire": [], "teste": []})
    objs = []  # (obj, usage, nœud, fichier:ligne, détail)
    fiches = []
    for nid in order:
        n = nodes[nid]
        pre = nid.split("_")[0]
        hero, sec = SECTIONS.get(pre, ("?", pre))
        img = nmap.get(nid)
        img_src = "explicite" if img else "défaut de section"
        img = img or defauts.get(pre, "")
        all_conds, all_fx = [], []
        for x in n["lines"]: all_conds += [(c, x["file"], x["line"]) for c in x["if"]]
        for q in n["quips"]: all_conds += [(c, q["file"], q["line"]) for c in q["if"]]
        for c in n["choices"]:
            all_conds += [(cc, c["file"], c["line"]) for cc in c["if"]]
            all_fx += [(e, c["file"], c["line"], "réussite") for e in c["okfx"]]
            all_fx += [(e, c["file"], c["line"], "échec") for e in c["kofx"]]
        all_fx += [(f["e"], f["file"], f["line"], "arrivée") for f in n["fx"]]
        req_flags, req_comp, req_pc, req_var = set(), set(), set(), set()
        for c, f, l in all_conds:
            for a in conds_of([c]):
                k, _, v = a.partition(":")
                if k == "flag":
                    req_flags.add(v); flags[v]["teste"].append(f"{nid} {f}:{l}")
                    if v.startswith("obj_"): objs.append((v, "requis", nid, f"{f}:{l}", c))
                elif k == "comp": req_comp.add(v)
                elif k == "pc": req_pc.add(v)
                elif a and not v: req_var.add(a)
        set_flags, rm_flags, add_comp, rm_comp = set(), set(), set(), set()
        for e, f, l, quand in all_fx:
            eff = e
            if "=>" in e:
                cond, eff = e.split("=>", 1)
                for a in conds_of([cond]):
                    k, _, v = a.partition(":")
                    if k == "flag": flags[v]["teste"].append(f"{nid} {f}:{l}")
                    elif k == "comp": req_comp.add(v)
            if eff[:1] in "+-" and ":" in eff:
                k, v = eff[1:].split(":", 1)
                if k == "comp": (add_comp if eff[0] == "+" else rm_comp).add(v)
                else:
                    (set_flags if eff[0] == "+" else rm_flags).add(v)
                    flags[v]["pose" if eff[0] == "+" else "retire"].append(f"{nid} {f}:{l}")
                    if v.startswith("obj_"):
                        objs.append((v, "donné" if eff[0] == "+" else "retiré", nid, f"{f}:{l}", quand))
        text = " ".join(x["t"] for x in n["lines"]) + " " + " ".join(q["t"] for q in n["quips"])
        cites = sorted(k for k, toks in who.items() if any(re.search(r"\b" + re.escape(t) + r"\b", text) for t in toks))
        quip_comps = sorted({q["c"] for q in n["quips"]})
        present = sorted(set(quip_comps) | req_comp | add_comp)
        first = next((x["t"] for x in n["lines"] if not x["if"]), n["lines"][0]["t"] if n["lines"] else "")
        segs = [f"{s['file']}:{s['start']}-{s['end']}" + ("+" if s["ext"] else "") for s in n["segments"]]
        fiche = {
            "id": nid, "section": pre, "section_nom": sec, "heros": hero, "titre": n["title"],
            "fin": n["end"], "morceaux": segs,
            "image": img, "image_source": img_src, "lieu": lnames.get(img, ""),
            "compagnons": present, "repliques_de": quip_comps, "cites": cites,
            "pc_requis": sorted(req_pc), "comp_requis": sorted(req_comp),
            "objets_donnes": sorted(x for x in set_flags if x.startswith("obj_")),
            "objets_retires": sorted(x for x in rm_flags if x.startswith("obj_")),
            "objets_requis": sorted(x for x in req_flags if x.startswith("obj_")),
            "drapeaux_poses": sorted(x for x in set_flags if not x.startswith("obj_")),
            "drapeaux_retires": sorted(x for x in rm_flags if not x.startswith("obj_")),
            "drapeaux_testes": sorted(x for x in req_flags if not x.startswith("obj_")),
            "variables_testees": sorted(req_var),
            "comp_ajoutes": sorted(add_comp), "comp_retires": sorted(rm_comp),
            "suites": list(dict.fromkeys(c["to"] for c in n["choices"])),
            "venant_de": preds.get(nid, []),
            "texte": short(first, 160),
            "lignes": [{"l": f"{x['file']}:{x['line']}", "if": x["if"], "t": short(x["t"], 70)} for x in n["lines"]],
            "choix": [{"l": f"{c['file']}:{c['line']}", "vers": c["to"], "jet": c["stat"], "if": c["if"],
                       "libelle": short(c["label"], 70)} for c in n["choices"]],
            "repliques": [{"l": f"{q['file']}:{q['line']}", "c": q["c"], "if": q["if"], "t": short(q["t"], 70)}
                          for q in n["quips"]],
        }
        if n.get("orphan_ext"): fiche["alerte"] = "extension @+ sans définition @"
        fiches.append(fiche)

    os.makedirs(OUT, exist_ok=True)
    J = lambda xs: ",".join(xs)
    with open(os.path.join(OUT, "scenes.json"), "w", encoding="utf-8") as f:
        # une fiche par ligne : grep '"id": "cot_05"' index/scenes.json donne la fiche entière
        f.write("[\n" + ",\n".join(json.dumps(x, ensure_ascii=False) for x in fiches) + "\n]\n")
    with open(os.path.join(OUT, "scenes.tsv"), "w", encoding="utf-8") as f:
        f.write("id\tmorceaux\tsection\theros\tlieu\ttitre\tfin\tcompagnons\tobjets(+donné -retiré ?requis)\tpc\tsuites\ttexte\n")
        for x in fiches:
            o = [f"+{v}" for v in x["objets_donnes"]] + [f"-{v}" for v in x["objets_retires"]] + [f"?{v}" for v in x["objets_requis"]]
            lieu = f"{x['image']} {x['lieu']}" + ("" if x["image_source"] == "explicite" else " (défaut)")
            f.write("\t".join([x["id"], " ".join(x["morceaux"]), x["section"], x["heros"], lieu, x["titre"],
                               x["fin"] or "", J(x["compagnons"]), J(o), J(x["pc_requis"]), J(x["suites"]),
                               short(x["texte"], 90)]) + "\n")
    with open(os.path.join(OUT, "repliques.tsv"), "w", encoding="utf-8") as f:
        f.write("ligne\tnoeud\tsection\theros\tlieu\tcompagnon\tduo_avec\tconditions\ttexte\n")
        for x in fiches:
            for q in x["repliques"]:
                duo = [a.split(":", 1)[1] for a in conds_of([c for c in q["if"] if not c.startswith("!")])
                       if a.startswith("comp:") and a.split(":", 1)[1] != q["c"]]
                f.write("\t".join([q["l"], x["id"], x["section"], x["heros"], f"{x['image']} {x['lieu']}", q["c"],
                                   J(duo), " ".join(q["if"]), q["t"]]) + "\n")
    with open(os.path.join(OUT, "objets.tsv"), "w", encoding="utf-8") as f:
        f.write("objet\tnom\tusage\tnoeud\tligne\tdetail\n")
        for o, u, nid, l, d in sorted(objs):
            f.write("\t".join([o, items.get(o, {}).get("name", "INCONNU"), u, nid, l, d]) + "\n")
    with open(os.path.join(OUT, "drapeaux.tsv"), "w", encoding="utf-8") as f:
        f.write("drapeau\tetat\tnb_poses\tnb_testes\tposes\tretires\ttestes\n")
        for k in sorted(flags):
            v = flags[k]
            etat = "ok" if v["pose"] and v["teste"] else ("jamais testé" if v["pose"] else "jamais posé")
            f.write("\t".join([k, etat, str(len(v["pose"])), str(len(v["teste"])),
                               " ; ".join(v["pose"]), " ; ".join(v["retire"]), " ; ".join(v["teste"])]) + "\n")
    bysec = defaultdict(list)
    for x in fiches: bysec[x["section"]].append(x)
    with open(os.path.join(OUT, "sections.md"), "w", encoding="utf-8") as f:
        f.write("# Sections du jeu\n\nGénéré par `python3 tools/index.py`. Une section = un préfixe d'identifiant.\n\n")
        f.write("| Préfixe | Héros | Section | Lieu par défaut | Nœuds | Fichiers (nb de morceaux) |\n|---|---|---|---|---|---|\n")
        for pre, xs in bysec.items():
            hero, sec = SECTIONS.get(pre, ("?", pre))
            fc = defaultdict(int)
            for x in xs:
                for m in x["morceaux"]: fc[m.split(":")[0]] += 1
            img = defauts.get(pre, "")
            f.write(f"| {pre} | {hero} | {sec} | {img} {lnames.get(img, '')} | {len(xs)} | "
                    + ", ".join(f"{k} ({v})" for k, v in sorted(fc.items())) + " |\n")
        f.write("\n## Fichiers\n\n| Fichier | Nœuds définis | Extensions @+ | Répliques |\n|---|---|---|---|\n")
        fstat = defaultdict(lambda: [0, 0, 0])
        for nid in order:
            for s in nodes[nid]["segments"]: fstat[s["file"]][1 if s["ext"] else 0] += 1
            for q in nodes[nid]["quips"]: fstat[q["file"]][2] += 1
        for k in sorted(fstat):
            a, b, c = fstat[k]; f.write(f"| {k} | {a} | {b} | {c} |\n")
        unknown = sorted({x["section"] for x in fiches if x["section"] not in SECTIONS})
        if unknown: f.write(f"\nPréfixes sans libellé dans tools/index.py : {', '.join(unknown)}\n")
    nq = sum(len(x["repliques"]) for x in fiches)
    print(f"index/ : {len(fiches)} nœuds, {nq} répliques, {len(objs)} usages d'objets, {len(flags)} drapeaux")

if __name__ == "__main__":
    main()
