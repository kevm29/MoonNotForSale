import sys, json, random, glob
sys.path.insert(0, '.')
import build as B
from collections import Counter
meta = json.load(open("meta.json"))
nodes, order = B.parse(sorted(glob.glob("src/*.txt")))
empty = Counter(); few = Counter()
random.seed(11)
for pol in ("random", "explore"):
    for pc in meta["playables"]:
        for _ in range(500):
            st = {"pc": pc["id"], "comp": set(), "flags": set(),
                  "vars": {"pan": pc["stats"][0], "rus": pc["stats"][1], "coe": pc["stats"][2], "equ": meta["start"]["equ"], "mor": meta["start"]["mor"]}}
            cur = pc["start"]; steps = 0
            while steps < 400:
                n = nodes[cur]; B.apply(n["fx"], st)
                vis = [l for l in n["lines"] if all(B.check(c, st) for c in l["if"])]
                if not vis: empty[(cur, st.get("prev"), st.get("last"))] += 1
                if "end" in n: break
                avail = [c for c in n["choices"] if all(B.check(cc, st) for cc in c["if"])]
                if pol == "explore":
                    g = [c for c in avail if c["if"]]
                    ch = random.choice(g) if g and random.random() < .7 else random.choice(avail)
                else:
                    ch = random.choice(avail)
                ok = B.roll_ok(st, ch, meta)
                d = meta["defaults"]
                B.apply((ch["okfx"] or d["okfx"]) if ok else (ch["kofx"] or d["kofx"]), st)
                st["last"] = "ok" if ok else "ko"; st["prev"] = cur
                cur = ch["to"]; steps += 1
print("nœuds sans texte visible :", len(empty))
for k, v in empty.most_common(30): print(" ", k, v)
