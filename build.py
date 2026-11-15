#!/usr/bin/env python3
"""Compile les fichiers src/*.txt (DSL) en données JSON, valide le graphe,
simule des parties, et injecte le tout dans les gabarits HTML."""
import json, re, sys, random, glob, os
from collections import defaultdict, deque, Counter

HERE = os.path.dirname(os.path.abspath(__file__))
STATS = ("pan", "rus", "coe")
XP_STEP, STAT_MAX, COMP_BONUS, COMP_MAX = 3, 5, 1, 2
HEAVY = 6
# difficulté ajoutée selon l'avancée : le monde se dérègle, tout devient plus dur
DIFF_OFFSET = {"ond": 1, "bas": 1, "pis": 1, "bri": 1, "zep": 1, "gri": 1, "pel": 1, "lyc": 1, "ana": 1, "hub": 1, "foi": 2, "nua": 2, "com": 2, "nui": 3, "cot": 2, "for": 2, "son": 2, "pro": 2, "cap": 2, "asc": 3, "cha": 4, "neg": 4, "fin": 3}
DRIFT_PREFIXES = ("nua_", "com_", "cot_", "for_", "son_", "pro_", "cap_", "asc_", "cha_", "neg_", "fin_")

def parse_conds(tokens):
    out = []
    for t in tokens:
        assert t.startswith("?"), t
        out.append(t[1:])
    return out

def parse_fx(s):
    s = s.strip()
    return s.split() if s else []

def parse(files):
    nodes, order = {}, []
    cur = None
    for f in files:
        for ln, raw in enumerate(open(f, encoding="utf-8"), 1):
            line = raw.rstrip("\n")
            where = f"{os.path.basename(f)}:{ln}"
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            if line.startswith("@+"):
                nid = line[2:].strip()
                if nid not in nodes: sys.exit(f"Extension d'un nœud inconnu {nid} ({where})")
                cur = nodes[nid]; continue
            if line.startswith("@"):
                nid = line[1:].strip()
                if nid in nodes:
                    sys.exit(f"Doublon {nid} ({where})")
                cur = {"id": nid, "tags": [], "fx": [], "lines": [], "quips": [], "choices": [], "src": where}
                nodes[nid] = cur; order.append(nid)
                continue
            if cur is None:
                sys.exit(f"Texte hors nœud {where}")
            if line.startswith("!tags:"):
                cur["tags"] = [t.strip() for t in line[6:].split(",") if t.strip()]
            elif line.startswith("!fx:"):
                cur["fx"] += parse_fx(line[4:])
            elif line.startswith("!end:"):
                cur["end"] = int(line[5:].strip())
            elif line.startswith("!title:"):
                cur["title"] = line[7:].strip()
            elif line.startswith("~"):
                m = re.match(r"~(\w+)((?:\s+\?\S+)*)\s*:\s*(.*)", line)
                if not m: sys.exit(f"Réplique mal formée {where}")
                q = {"c": m.group(1), "if": [x[1:] for x in m.group(2).split()], "t": m.group(3)}
                # une réplique conditionnelle passe avant la réplique générale du même compagnon
                pos = next((i for i, o in enumerate(cur["quips"]) if q["if"] and o["c"] == q["c"] and not o["if"]), None)
                if pos is None: cur["quips"].append(q)
                else: cur["quips"].insert(pos, q)
            elif line.startswith("*"):
                parts = [p.strip() for p in line[1:].split("|")]
                head = parts[0].split()
                to = head[0]
                stat, diff = None, 11
                conds = []
                for t in head[1:]:
                    if t.startswith("?"):
                        conds.append(t[1:])
                    else:
                        m = re.match(r"(pan|rus|coe|any)(\d+)$", t)
                        if not m: sys.exit(f"Jet mal formé '{t}' {where}")
                        stat, diff = m.group(1), int(m.group(2))
                parts += [""] * (6 - len(parts))
                # un jet n'a lieu que s'il y a un vrai risque, raconté : caractéristique ET texte d'échec
                if stat is None or not parts[3]: stat, diff = "auto", 0
                ch = {"to": to, "stat": stat, "diff": diff, "if": conds, "label": parts[1],
                      "ok": parts[2], "ko": parts[3], "okfx": parse_fx(parts[4]), "kofx": parse_fx(parts[5])}
                if not ch["label"]: sys.exit(f"Choix sans libellé {where}")
                cur["choices"].append(ch)
            else:
                toks = line.split(" ")
                conds = []
                while toks and toks[0].startswith("?") and len(toks[0]) > 1:
                    conds.append(toks.pop(0)[1:])
                cur["lines"].append({"if": conds, "t": " ".join(toks)})
    for nid in order:
        off = DIFF_OFFSET.get(nid.split("_")[0], 0)
        for c in nodes[nid]["choices"]:
            if c["stat"] != "auto": c["diff"] += off
    for nid in order:
        if nid.startswith(DRIFT_PREFIXES) and "end" not in nodes[nid]:
            drift = 1
            nodes[nid]["fx"] = [f"equ-{drift}"] + nodes[nid]["fx"]
    return nodes, order

# ---------- évaluation (miroir du moteur JS) ----------
def check(cond, st):
    if "," in cond:
        if cond.startswith("!"):
            return not any(check(c, st) for c in cond[1:].split(","))
        return any(check(c, st) for c in cond.split(","))
    neg = cond.startswith("!")
    c = cond[1:] if neg else cond
    if ":" in c:
        k, v = c.split(":", 1)
        if k == "comp": r = v in st["comp"]
        elif k == "flag": r = v in st["flags"]
        elif k == "pc": r = st["pc"] == v
        elif k == "last": r = st.get("last") == v
        elif k == "from": r = st.get("prev") == v
        else: raise ValueError(cond)
    else:
        m = re.match(r"(\w+)(>=|<=|>|<|==)(-?\d+)$", c)
        if not m: raise ValueError(cond)
        a = st["vars"].get(m.group(1), 0); b = int(m.group(3)); op = m.group(2)
        r = {">=": a >= b, "<=": a <= b, ">": a > b, "<": a < b, "==": a == b}[op]
    return (not r) if neg else r

def apply(fx, st):
    for e in fx:
        if "=>" in e:
            cond, eff = e.split("=>", 1)
            if check(cond, st): apply([eff], st)
            continue
        if e[0] in "+-" and ":" in e:
            k, v = e[1:].split(":", 1)
            target = st["comp"] if k == "comp" else st["flags"]
            (target.add if e[0] == "+" else target.discard)(v)
            continue
        m = re.match(r"(\w+)([+\-=])(\d+)$", e)
        if not m: raise ValueError(e)
        k, op, n = m.group(1), m.group(2), int(m.group(3))
        v = st["vars"].get(k, 0)
        v = v + n if op == "+" else v - n if op == "-" else n
        if k == "equ": v = max(0, min(100, v))
        if k == "mor": v = max(0, min(10, v))
        if k in STATS and op == "+":
            # progression lente : 3 points d'expérience = +1 dans la caractéristique (max STAT_MAX)
            xp = st.setdefault("xp", {}).get(k, 0) + n
            while xp >= XP_STEP and st["vars"].get(k, 0) < STAT_MAX:
                xp -= XP_STEP; st["vars"][k] = st["vars"].get(k, 0) + 1
            st["xp"][k] = xp if st["vars"].get(k, 0) < STAT_MAX else 0
            continue
        if k in STATS: v = max(0, min(STAT_MAX, v))
        st["vars"][k] = v

def validate(nodes, order, meta):
    errs, warns = [], []
    ends = {n["end"]: nid for nid, n in nodes.items() if "end" in n}
    for nid in order:
        n = nodes[nid]
        if "end" not in n and not n["choices"]:
            errs.append(f"Impasse sans choix : {nid} ({n['src']})")
        for c in n["choices"]:
            if c["to"] not in nodes:
                errs.append(f"Cible inconnue {c['to']} depuis {nid} ({n['src']})")
            for cc in c["if"]:
                try: check(cc, {"comp": set(), "flags": set(), "pc": "", "vars": {}})
                except Exception: errs.append(f"Condition invalide {cc} dans {nid}")
            for fx in c["okfx"] + c["kofx"]:
                try: apply([fx], {"comp": set(), "flags": set(), "vars": {}})
                except Exception: errs.append(f"Effet invalide {fx} dans {nid}")
        for q in n["quips"]:
            if q["c"] not in meta["companions"]:
                errs.append(f"Réplique d'un compagnon inconnu {q['c']} dans {nid}")
            for cc in q["if"]:
                try: check(cc, {"comp": set(), "flags": set(), "pc": "", "vars": {}})
                except Exception: errs.append(f"Condition de réplique invalide {cc} dans {nid}")
        for c in n["choices"]:
            if not c["ok"].strip(): errs.append(f"Choix sans texte de résultat dans {nid} : {c['label'][:40]}")
            for fx in c["okfx"] + c["kofx"]:
                if "=>" in fx:
                    try:
                        check(fx.split('=>')[0], {"comp": set(), "flags": set(), "pc": "", "vars": {}}); apply([fx.split('=>')[1]], {"comp": set(), "flags": set(), "vars": {}})
                    except Exception: errs.append(f"Effet conditionnel invalide {fx} dans {nid}")
        for c in n["choices"]:
            for cc in c["if"]:
                for part in cc.lstrip("!").split(","):
                    if part.startswith("comp:") and part.split(":")[1] not in meta["companions"]:
                        errs.append(f"Compagnon inconnu {part} dans {nid}")
        for ln in n["lines"]:
            for cc in ln["if"]:
                try: check(cc, {"comp": set(), "flags": set(), "pc": "", "vars": {}})
                except Exception: errs.append(f"Condition de texte invalide {cc} dans {nid}")
    preds = defaultdict(set)
    for nid in order:
        for c in nodes[nid]["choices"]: preds[c["to"]].add(nid)
    for nid in order:
        n = nodes[nid]
        for cc in [x for ln in n["lines"] for x in ln["if"]] + [x for c in n["choices"] for x in c["if"]]:
            for part in cc.lstrip("!").split(","):
                part = part.lstrip("!")
                if part.startswith("from:") and part[5:] not in preds[nid]:
                    errs.append(f"Condition from:{part[5:]} impossible dans {nid} (pas un prédécesseur)")
                if part.startswith("last:") and part[5:] not in ("ok", "ko"):
                    errs.append(f"Condition {part} invalide dans {nid}")
    items = meta.get("items", {})
    for nid in order:
        n = nodes[nid]
        allfx = list(n["fx"]) + [e for c in n["choices"] for e in c["okfx"] + c["kofx"]]
        allcond = [x for ln in n["lines"] for x in ln["if"]] + [x for c in n["choices"] for x in c["if"]]
        for e in allfx:
            if e[1:].startswith("flag:obj_") and e[6:] not in items: errs.append(f"Objet inconnu {e} dans {nid}")
            if e[1:].startswith("comp:") and e[6:] not in meta["companions"]: errs.append(f"Compagnon inconnu {e} dans {nid}")
        for cc in allcond:
            for part in cc.lstrip("!").split(","):
                part = part.lstrip("!")
                if part.startswith("flag:obj_") and part[5:] not in items: errs.append(f"Objet inconnu {part} dans {nid}")
    for i in range(1, 16):
        if i not in ends: errs.append(f"Fin {i} absente")
    # accessibilité structurelle depuis chaque départ (en respectant ?pc:)
    reach_by_pc = {}
    for pc in meta["playables"]:
        seen = set(); dq = deque([pc["start"]])
        while dq:
            x = dq.popleft()
            if x in seen or x not in nodes: continue
            seen.add(x)
            for c in nodes[x]["choices"]:
                ok = True
                for cc in c["if"]:
                    if cc.startswith("pc:") and cc[3:] != pc["id"]: ok = False
                    if cc.startswith("!pc:") and cc[4:] == pc["id"]: ok = False
                if ok: dq.append(c["to"])
        reach_by_pc[pc["id"]] = seen
    allreach = set().union(*reach_by_pc.values())
    for nid in order:
        if nid not in allreach: errs.append(f"Nœud inaccessible : {nid} ({nodes[nid]['src']})")
    return errs, warns, reach_by_pc

def roll_ok(st, ch, meta):
    stat = ch["stat"]
    if stat == "auto":
        st["_heavy"] = False; return True
    if stat == "any":
        stat = max(STATS, key=lambda s: st["vars"].get(s, 0))
    bonus = st["vars"].get(stat, 0)
    bonus += min(COMP_MAX, COMP_BONUS * sum(1 for cid in st["comp"] if meta["companions"][cid]["stat"] == stat))
    m = st["vars"].get("mor", 5)
    bonus += 1 if m >= 8 else -1 if m <= 2 else 0
    d = random.randint(1, 20)
    ok = d == 20 or (d != 1 and d + bonus >= ch["diff"])
    # échec cuisant : un 1, ou raté de HEAVY points ou plus -> seul cas où le malus par défaut (Moral -1) s'applique
    st["_heavy"] = (not ok) and (d == 1 or d + bonus <= ch["diff"] - HEAVY)
    return ok

STATS_OK = defaultdict(Counter); DOUBLE_RECRUIT = Counter()
def simulate(nodes, meta, runs=4000, policy="random"):
    res = defaultdict(Counter); visits = Counter(); lengths = []
    for pc in meta["playables"]:
        for _ in range(runs):
            st = {"pc": pc["id"], "comp": set(), "flags": set(),
                  "vars": {"pan": pc["stats"][0], "rus": pc["stats"][1], "coe": pc["stats"][2], "equ": meta["start"]["equ"], "mor": meta["start"]["mor"]}}
            cur = pc["start"]; steps = 0
            while True:
                n = nodes[cur]; visits[cur] += 1
                apply(n["fx"], st)
                if "end" in n:
                    res[pc["id"]][n["end"]] += 1; lengths.append(steps); break
                avail = [c for c in n["choices"] if all(check(cc, st) for cc in c["if"])]
                if not avail:
                    res[pc["id"]]["BLOQUÉ:" + cur] += 1; break
                if policy == "explore":
                    gated = [c for c in avail if c["if"]]
                    ch = random.choice(gated) if gated and random.random() < 0.7 else random.choice(avail)
                else:
                    ch = random.choice(avail)
                d = meta["defaults"]
                ok = roll_ok(st, ch, meta)
                if ch["stat"] != "auto": STATS_OK[ch["to"][:3]][ok] += 1
                fx = (ch["okfx"] or d.get("autofx", [])) if ch["stat"] == "auto" else (ch["okfx"] or d["okfx"]) if ok else (ch["kofx"] or (d["kofx"] if st.get("_heavy") else []))
                for e in fx:
                    if e.startswith("+comp:") and e[6:] in st["comp"]:
                        DOUBLE_RECRUIT[(cur, e[6:])] += 1
                apply(fx, st)
                st["last"] = "ok" if ok else "ko"; st["prev"] = cur
                if not ch["okfx"] and not ch["kofx"]:
                    pass
                cur = ch["to"]; steps += 1
                if steps > 400:
                    res[pc["id"]]["BOUCLE"] += 1; break
    return res, visits, lengths

def layout(nodes, order, meta):
    """Positions pré-calculées : bandes par section, groupes de sections de gauche à droite."""
    groups = [["ond", "bas", "pis", "bri", "zep", "gri", "pel", "lyc", "ana"], ["hub", "foi"], ["cot", "for", "son", "pro", "cap", "nua", "com"], ["nui"], ["asc"], ["cha"], ["neg"], ["fin"], ["end"]]
    bysec = defaultdict(list)
    for nid in order: bysec[nid.split("_")[0]].append(nid)
    DX, DY = 84, 58
    blocks = {}
    for s, ids in bysec.items():
        idset = set(ids)
        depth = {ids[0]: 0}; dq = deque([ids[0]])
        while dq:
            x = dq.popleft()
            for c in nodes[x]["choices"]:
                t = c["to"]
                if t in idset and t not in depth:
                    depth[t] = depth[x] + 1; dq.append(t)
        for nid in ids:
            if nid not in depth:
                preds = [depth[p] for p in ids if p in depth and any(c["to"] == nid for c in nodes[p]["choices"])]
                depth[nid] = (max(preds) + 1) if preds else 0
        if s == "end":
            depth = {nid: i for i, nid in enumerate(ids)}
        cols = defaultdict(list)
        for nid in ids: cols[depth[nid]].append(nid)
        blocks[s] = (cols, max(cols) + 1, max(len(v) for v in cols.values()))
    pos = {}; bands = []
    columns = [groups[:3], groups[3:]]
    widths = [max(blocks[s][1] for g in col for s in g if s in blocks) for col in columns]
    cx = [0, (widths[0] - 1) * DX / 2 + (widths[1] - 1) * DX / 2 + 420]
    for ci, col in enumerate(columns):
        y0 = 0
        for g in col:
            g = [s for s in g if s in blocks]
            if not g: continue
            for s in g:
                cols, w, h = blocks[s]
                x0 = cx[ci] - (w - 1) * DX / 2
                for d, v in cols.items():
                    for i, nid in enumerate(v):
                        pos[nid] = {"x": x0 + d * DX, "y": y0 + 50 + (h - len(v)) * DY / 2 + i * DY}
                bands.append({"sec": s, "x": x0 - 40, "y": y0 + 10, "w": (w - 1) * DX + 80, "h": (h - 1) * DY + 80})
                y0 += (h - 1) * DY + 80 + 70
            y0 += 110
    return pos, bands

def flag_index(nodes, order):
    idx = defaultdict(lambda: {"set": [], "need": []})
    for nid in order:
        n = nodes[nid]
        for e in n["fx"]:
            if e.startswith("+flag:"): idx[e[6:]]["set"].append(nid)
        for c in n["choices"]:
            for e in c["okfx"] + c["kofx"]:
                if e.startswith("+flag:") and nid not in idx[e[6:]]["set"]: idx[e[6:]]["set"].append(nid)
            for cc in c["if"]:
                for part in cc.lstrip("!").split(","):
                    part = part.lstrip("!")
                    if part.startswith("flag:") and nid not in idx[part[5:]]["need"]: idx[part[5:]]["need"].append(nid)
        for ln in n["lines"]:
            for cc in ln["if"]:
                for part in cc.lstrip("!").split(","):
                    part = part.lstrip("!")
                    if part.startswith("flag:") and nid not in idx[part[5:]]["need"]: idx[part[5:]]["need"].append(nid)
    return dict(idx)

def main():
    files = sorted(glob.glob(os.path.join(HERE, "src", "*.txt")))
    meta = json.load(open(os.path.join(HERE, "meta.json"), encoding="utf-8"))
    nodes, order = parse(files)
    errs, warns, reach = validate(nodes, order, meta)
    choice_nodes = [n for n in order if "end" not in nodes[n]]
    print(f"Nœuds à choix : {len(choice_nodes)} | fins : {len(order) - len(choice_nodes)} | choix : {sum(len(nodes[n]['choices']) for n in order)}")
    for e in errs: print("ERREUR", e)
    if errs and "--force" not in sys.argv:
        sys.exit(1)
    random.seed(7)
    report = {}
    for policy in ("random", "explore"):
        res, visits, lengths = simulate(nodes, meta, runs=1500, policy=policy)
        report[policy] = {pc: dict(c) for pc, c in res.items()}
        tot = Counter()
        for c in res.values(): tot.update(c)
        print(f"\n[{policy}] longueur moyenne {sum(lengths)/max(1,len(lengths)):.1f} choix")
        for k in sorted(tot, key=str): print(f"  fin {k}: {tot[k]}")
        report[policy + "_visits"] = {n: visits[n] for n in order}
        report[policy + "_runs"] = 1500
    print("\ntaux de réussite des jets par section :")
    for sec in ["ond","bas","pis","bri","zep","gri","pel","lyc","ana","hub","foi","cot","for","son","pro","cap","nua","com","nui","asc","cha","neg","fin","end"]:
        c = STATS_OK.get(sec)
        if c: print(f"  {sec}: {100*c[True]/max(1,c[True]+c[False]):.0f} %")
    allc = Counter()
    for c in STATS_OK.values(): allc.update(c)
    print(f"  global: {100*allc[True]/max(1,sum(allc.values())):.0f} %")
    if DOUBLE_RECRUIT: print("RECRUTEMENT EN DOUBLE:", dict(DOUBLE_RECRUIT))
    never = [n for n in order if not report["random_visits"][n] and not report["explore_visits"][n]]
    print("nœuds jamais visités en simulation:", never)
    data = {"nodes": {nid: nodes[nid] for nid in order}, "order": order, "meta": meta}
    for nid in order: nodes[nid].pop("src", None)
    tree = dict(data)
    tree["layout"], tree["bands"] = layout(nodes, order, meta)
    tree["flags"] = flag_index(nodes, order)
    tree["reach"] = {k: sorted(v) for k, v in reach.items()}
    tree["sim"] = report
    # portraits des fiches, intégrés au HTML pour qu'il reste autonome
    import base64
    data["portraits"] = {os.path.splitext(os.path.basename(f))[0]: "data:image/webp;base64," + base64.b64encode(open(f, "rb").read()).decode()
                         for f in sorted(glob.glob(os.path.join(HERE, "img", "personnages", "*.webp")))}
    acc = os.path.join(HERE, "img", "accueil.webp")
    if os.path.exists(acc): data["accueil"] = "data:image/webp;base64," + base64.b64encode(open(acc, "rb").read()).decode()
    out = os.environ.get("OUT", os.path.join(HERE, "out"))
    os.makedirs(out, exist_ok=True)
    for tpl, name, payload in (("game.html", "la-lune-vendue.html", data), ("tree.html", "arbre-de-decision.html", tree)):
        p = os.path.join(HERE, tpl)
        if not os.path.exists(p): continue
        html = open(p, encoding="utf-8").read().replace("/*__DATA__*/null", json.dumps(payload, ensure_ascii=False))
        open(os.path.join(out, name), "w", encoding="utf-8").write(html)
        print("écrit", name)

if __name__ == "__main__":
    main()
