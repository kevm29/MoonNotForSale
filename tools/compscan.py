"""Repère les textes (lignes non conditionnées ou choix) qui nomment un compagnon
sans condition sur sa présence, dans les nœuds où il n'est pas forcément là."""
import json, glob, re, sys
sys.path.insert(0, ".")
import build as B
meta = json.load(open("meta.json"))
nodes, order = B.parse(sorted(glob.glob("src/*.txt")))
short = {}
for cid, c in meta["companions"].items():
    w = [x for x in c["name"].split() if x not in ("Madame", "Monsieur", "Sire", "Comtesse", "Dame", "Colonel", "Grand-Père", "Tante", "Dr", "Capitaine", "Le", "Chœur", "des")]
    short[cid] = w[-1] if cid in ("quartz",) else w[0]
short["meduses"] = "Méduses"
prefixes = sys.argv[1:] or ["nua", "com", "foi", "nui", "asc_2", "cha_4", "cha_5", "neg_4", "fin_2"]
for nid in order:
    if not nid.startswith(tuple(prefixes)): continue
    n = nodes[nid]
    for cid, nm in short.items():
        pat = re.compile(r"\b" + re.escape(nm) + r"\b")
        for ln in n["lines"]:
            if pat.search(ln["t"]) and not any(cid in c for c in ln["if"]) and not any(cid in c for ch in n["choices"] for c in ch["if"]):
                print(f"{nid} ligne : {nm} :: {ln['t'][:90]}")
        for ch in n["choices"]:
            if pat.search(ch["label"]) and not any(cid in c for c in ch["if"]):
                print(f"{nid} choix : {nm} :: {ch['label'][:90]}")
