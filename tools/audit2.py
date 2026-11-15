"""Audit de cohérence du déroulement : rejoue des parties au hasard et relève ce que le joueur LIT
qui contredit son état (compagnon absent, parti ou jamais rencontré ; objet absent ; nœud revu)."""
import json, glob, re, sys, random
from collections import Counter, defaultdict
src = open("build.py", encoding="utf-8").read().split("\ndef main")[0]
B = {"__file__": "build.py"}
exec(compile(src, "build.py", "exec"), B)
meta = json.load(open("meta.json", encoding="utf-8"))
nodes, order = B["parse"](sorted(glob.glob("src/*.txt")))
check, apply, roll_ok = B["check"], B["apply"], B["roll_ok"]
random.seed(7)

NAMES = {"bartho": r"Bartholomé", "penelope": r"Pénélope", "melusine": r"Mélusine", "echo": r"\bÉcho\b", "quartz": r"Quartz",
         "brume": r"Brume-Lucie", "rocambole": r"Rocambole", "meduses": r"Méduses|le Chœur", "fernand": r"Fernand", "zouzou": r"Zouzou",
         "coquille": r"Coquille", "vesperine": r"Vespérine|la Comtesse", "ondee": r"Ondée", "gaspard": r"Gaspard", "fulgence": r"Fulgence",
         "ysaline": r"Ysaline", "pardon": r"\bPardon (?:te|se|a|est|flotte|range|regarde|tend|court|hoche|mesure)\b", "pli": r"Monsieur Pli|\bPli\b", "taupinel": r"Taupinel",
         "plumard": r"Plumard", "remontoir": r"Remontoir"}
NAMES = {k: re.compile(v) for k, v in NAMES.items()}
ITEMS = {"obj_lettre_vent": r"lettre bleue|enveloppe bleue", "obj_cle_remontage": r"clé de laiton", "obj_berceau_nuage": r"berceau", "obj_miroir_platine": r"miroir",
         "obj_graine_lune": r"\bgraine\b", "obj_corne_brume": r"\bcorne\b", "obj_croc_argent": r"\bcroc\b", "obj_beignet": r"beignet perpétuel", "obj_couverture": r"couverture de pierre",
         "obj_carte": r"carte postale", "obj_coquillage": r"coquillage", "obj_lanterne": r"lanterne", "obj_sablier": r"sablier", "obj_aiguille": r"aiguille de Mélusine",
         "obj_brin_toile": r"brin de la Toile|\bbrin\b", "obj_metre": r"mètre du petit|mètre ruban du petit", "obj_oreiller": r"oreiller", "obj_cauchemar": r"cauchemar",
         "obj_mouton": r"mouton numéro", "obj_bille": r"\bbille\b", "obj_facette": r"\bfacette\b", "obj_echo": r"bouteille", "obj_neveu_galet": r"neveu",
         "obj_ticket_zero": r"ticket numéro zéro", "obj_tampon_vu": r"« VU »", "obj_fleur_epine": r"fleur", "obj_goutte": r"dé à coudre", "obj_ballon": r"\bballon\b",
         "obj_plume": r"plume du héron", "obj_aurore": r"\baurore\b", "obj_eclipse": r"éclipse", "obj_etoile": r"étoile filante", "obj_boussole": r"boussole",
         "obj_coquille": r"éclat de coquille", "obj_braise": r"\bbraise\b", "obj_casque": r"casque doré", "obj_cle_grue": r"clé de Bobinot|clé de la grue"}
ITEMS = {k: re.compile(v) for k, v in ITEMS.items()}

home = defaultdict(set)   # sections où un compagnon peut être recruté (il y est un personnage du lieu)
give = defaultdict(set)   # nœuds où un objet se gagne
for nid in order:
    n = nodes[nid]
    for ch in n["choices"]:
        for e in ch["okfx"] + ch["kofx"]:
            e = e.split("=>")[-1]
            if e.startswith("+comp:"): home[e[6:]].add(nid.split("_")[0]); home[e[6:]].add(ch["to"].split("_")[0])
            if e.startswith("+flag:obj_"): give[e[6:]] |= {nid, ch["to"]}
    for e in n["fx"]:
        e = e.split("=>")[-1]
        if e.startswith("+flag:obj_"): give[e[6:]].add(nid)

rep = Counter(); ex = {}
revisit = Counter()
def note(kind, nid, who, text, extra=""):
    k = (kind, nid, who, text[:110])
    rep[k] += 1; ex.setdefault(k, extra)

def scan(text, nid, st, ever, left_at, steps, where):
    for cid, pat in NAMES.items():
        if cid in st["comp"] or not pat.search(text): continue
        sec = nid.split("_")[0]
        if cid in ever:
            if steps - left_at.get(cid, -99) <= 1: continue
            note("PARTI", nid, cid, text, where)
        elif sec not in home[cid]:
            note("JAMAIS", nid, cid, text, where)
    for it, pat in ITEMS.items():
        if it in st["flags"] or not pat.search(text) or nid in give[it]: continue
        note("OBJ_EU" if it in ever else "OBJ_JAMAIS", nid, it, text, where)

RUNS = int(sys.argv[1]) if len(sys.argv) > 1 else 1500
for pc in meta["playables"]:
    for _ in range(RUNS):
        st = {"pc": pc["id"], "comp": set(), "flags": set(), "vars": {"pan": pc["stats"][0], "rus": pc["stats"][1], "coe": pc["stats"][2], "equ": meta["start"]["equ"], "mor": meta["start"]["mor"]}}
        cur = pc["start"]; steps = 0; ever = set(); left_at = {}; seen = Counter()
        while True:
            n = nodes[cur]; seen[cur] += 1
            if seen[cur] == 2: revisit[cur] += 1
            before = set(st["comp"])
            apply(n["fx"], st)
            ever |= st["comp"] | {f for f in st["flags"] if f.startswith("obj_")}
            for l in n["lines"]:
                if all(check(c, st) for c in l["if"]): scan(l["t"], cur, st, ever, left_at, steps, "ligne")
            if "end" in n: break
            avail = [c for c in n["choices"] if all(check(cc, st) for cc in c["if"])]
            if not avail: note("BLOQUE", cur, "", ""); break
            for c in avail: scan(c["label"], cur, st, ever, left_at, steps, "libellé")
            gated = [c for c in avail if c["if"]]
            ch = random.choice(gated) if gated and random.random() < 0.6 else random.choice(avail)
            ok = roll_ok(st, ch, meta); d = meta["defaults"]
            fx = (ch["okfx"] or d.get("autofx", [])) if ch["stat"] == "auto" else (ch["okfx"] or d["okfx"]) if ok else (ch["kofx"] or (d["kofx"] if st.get("_heavy") else []))
            pre = set(st["comp"]); preflags = set(st["flags"])
            apply(fx, st)
            for c in pre - st["comp"]: left_at[c] = steps + 1
            ever |= st["comp"] | {f for f in st["flags"] if f.startswith("obj_")}
            # le texte du résultat se lit avec l'état d'avant OU d'après (recrutement, objet gagné ou donné)
            tmp = {"comp": pre | st["comp"], "flags": preflags | st["flags"]}
            scan(ch["ok"] if ok else ch["ko"], cur, tmp, ever, left_at, steps, "résultat " + ch["label"][:30])
            st["last"] = "ok" if ok else "ko"; st["prev"] = cur
            cur = ch["to"]; steps += 1
            if steps > 400: note("BOUCLE", cur, "", ""); break

for kind in ("BLOQUE", "BOUCLE", "PARTI", "JAMAIS", "OBJ_EU", "OBJ_JAMAIS"):
    rows = sorted([(k, v) for k, v in rep.items() if k[0] == kind], key=lambda x: (x[0][1], x[0][2]))
    print(f"\n===== {kind} : {len(rows)}")
    for (k, nid, who, t), v in rows:
        print(f"{nid} [{who}] x{v} ({ex[(k, nid, who, t)]}) :: {t}")
print("\n===== NŒUDS REVUS DANS UNE MÊME PARTIE")
print(sorted(revisit.items(), key=lambda x: -x[1]))
