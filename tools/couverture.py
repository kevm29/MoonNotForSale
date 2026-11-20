"""Couverture par héros jouable : lieux, compagnons, objets, fins, longueur des chemins.
Simule des parties (au hasard, et en explorant les choix conditionnels) avec les règles du jeu.
Écrit out/couverture.json. Usage : python3 tools/couverture.py [parties_par_heros]"""
import glob, json, os, random, re, sys
from collections import Counter, defaultdict
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
import build as B

# lieu de chaque nœud : motifs essayés dans l'ordre
LIEUX = [
    (r"^plt_cot", "Les Côtes Hagardes"), (r"^plt_cap", "Tamponville, la Capitale"), (r"^plt_bri", "Les Magmas Paisibles"),
    (r"^plt_ana", "La Serre des Belles-de-Nuit"), (r"^plt_nuit", "Le Pays des Songes"), (r"^plt_", "Le Carrefour des Espèces"),
    (r"^ond_", "Le phare de Grève-Molle"), (r"^bas_", "Tamponville, la Capitale"), (r"^pis_", "Le Pays des Songes"),
    (r"^bri_", "Les Magmas Paisibles"), (r"^zep_", "Le Promontoire de Platine"), (r"^gri_", "Le Centre de tri des Vents"),
    (r"^pel_", "La Maternité des Marées"), (r"^lyc_", "Le Club des Lycanthropes"), (r"^ana_", "La Serre des Belles-de-Nuit"),
    (r"^(hub|gal|plu)_", "Le Carrefour des Espèces"), (r"^foi_", "La Foire aux Rencontres"),
    (r"^(cot|gco|pct)_", "Les Côtes Hagardes"), (r"^(for|gfo)_", "La Forêt-Réseau"), (r"^(son|pso)_", "Le Pays des Songes"),
    (r"^(pro|gpr)_", "Les Profondeurs"), (r"^(cap|gpa)_", "Tamponville, la Capitale"), (r"^(nua|gnu|pha)_", "Les Hauts-Nuages"),
    (r"^(com|pcm)_", "Le Marché des Comètes"), (r"^(nui|pnu|gfi)_", "La dernière nuit, au camp"), (r"^asc_", "La montée vers la Lune"),
    (r"^(cha|pch|gmo)_", "Le chantier lunaire"), (r"^gtr_", "Le train de nuit"), (r"^(neg|fin|plf|pmo|pla|pcr)_", "Le Promontoire de Platine"),
    (r"^(pne|pnc|pno)_", "Le Pays des Songes"), (r"^ply_", "La Lyre, très loin"),
]
def lieu(nid):
    for pat, nom in LIEUX:
        if re.match(pat, nid): return nom
    return None

def run(nodes, meta, pc, runs, policy):
    out = {"lieux": Counter(), "comp": Counter(), "obj": Counter(), "fins": defaultdict(list), "len": [], "nodes": set(), "bloque": 0}
    items = set(meta["items"])
    for _ in range(runs):
        st = {"pc": pc["id"], "comp": set(), "flags": set(),
              "vars": {"pan": pc["stats"][0], "rus": pc["stats"][1], "coe": pc["stats"][2], "equ": meta["start"]["equ"], "mor": meta["start"]["mor"]}}
        cur, steps = pc["start"], 0
        seen_l, seen_c, seen_o = set(), set(), set()
        while True:
            n = nodes[cur]; out["nodes"].add(cur)
            l = lieu(cur)
            if l: seen_l.add(l)
            B.apply(n["fx"], st)
            seen_c |= st["comp"]; seen_o |= (st["flags"] & items)
            if "end" in n:
                out["fins"][n["end"]].append(steps); out["len"].append(steps); break
            avail = [c for c in n["choices"] if all(B.check(cc, st) for cc in c["if"])]
            if not avail or steps > 500:
                out["bloque"] += 1; out.setdefault("bloque_at", Counter())[cur] += 1; break
            if policy == "explore":
                gated = [c for c in avail if c["if"]]
                ch = random.choice(gated) if gated and random.random() < 0.7 else random.choice(avail)
            else:
                ch = random.choice(avail)
            d = meta["defaults"]; ok = B.roll_ok(st, ch, meta)
            fx = (ch["okfx"] or d.get("autofx", [])) if ch["stat"] == "auto" else (ch["okfx"] or d["okfx"]) if ok else (ch["kofx"] or (d["kofx"] if st.get("_heavy") else []))
            B.apply(fx, st); seen_c |= st["comp"]; seen_o |= (st["flags"] & items)
            st["last"] = "ok" if ok else "ko"; st["prev"] = cur
            cur = ch["to"]; steps += 1
        for x in seen_l: out["lieux"][x] += 1
        for x in seen_c: out["comp"][x] += 1
        for x in seen_o: out["obj"][x] += 1
    return out

def main():
    runs = int(sys.argv[1]) if len(sys.argv) > 1 else 2000
    meta = json.load(open(os.path.join(HERE, "meta.json"), encoding="utf-8"))
    nodes, order = B.parse(sorted(glob.glob(os.path.join(HERE, "src", "*.txt"))))
    random.seed(11)
    res = {"heros": [], "lieux": [], "comp": {}, "obj": {}, "fins": {}}
    all_l = []
    for pat, nom in LIEUX:
        if nom not in all_l: all_l.append(nom)
    res["lieux"] = all_l
    res["comp"] = {k: v["name"] for k, v in meta["companions"].items()}
    res["obj"] = {k: v["name"] for k, v in meta["items"].items()}
    res["fins"] = {k: {"titre": v["title"], "ton": v["kind"]} for k, v in meta["endings"].items()}
    for pc in meta["playables"]:
        a = run(nodes, meta, pc, runs, "random"); b = run(nodes, meta, pc, runs, "explore")
        tot = 2 * runs
        fins = {}
        for e in set(a["fins"]) | set(b["fins"]):
            L = a["fins"].get(e, []) + b["fins"].get(e, [])
            fins[str(e)] = {"part": round(100 * len(L) / tot, 1), "moy": round(sum(L) / len(L)), "min": min(L), "max": max(L)}
        lens = a["len"] + b["len"]
        res["heros"].append({
            "id": pc["id"], "nom": pc["name"], "espece": pc["species"], "deblocage": pc.get("unlock", 0),
            "lieux": {k: round(100 * (a["lieux"][k] + b["lieux"][k]) / tot, 1) for k in set(a["lieux"]) | set(b["lieux"])},
            "comp": {k: round(100 * (a["comp"][k] + b["comp"][k]) / tot, 1) for k in set(a["comp"]) | set(b["comp"])},
            "obj": {k: round(100 * (a["obj"][k] + b["obj"][k]) / tot, 1) for k in set(a["obj"]) | set(b["obj"])},
            "fins": fins,
            "longueur": {"moy": round(sum(lens) / len(lens)), "min": min(lens), "max": max(lens)},
            "noeuds": len(a["nodes"] | b["nodes"]),
            "bloque": a["bloque"] + b["bloque"],
        })
    json.dump(res, open(os.path.join(HERE, "out", "couverture.json"), "w"), ensure_ascii=False, indent=1)
    for h in res["heros"]:
        print(f'{h["id"]:11} long {h["longueur"]["moy"]:3} ({h["longueur"]["min"]}-{h["longueur"]["max"]})  lieux {len(h["lieux"]):2}  comp {len(h["comp"]):2}  obj {len(h["obj"]):2}  fins {sorted(h["fins"], key=int)}  noeuds {h["noeuds"]}  bloque {h["bloque"]}')

if __name__ == "__main__":
    main()
