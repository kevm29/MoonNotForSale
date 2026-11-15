"""Liste les nœuds où plusieurs chemins se rejoignent, avec le début de leur texte et les choix qui y mènent,
pour relire si le texte suppose un seul des chemins."""
import json, glob, re, sys
from collections import defaultdict
src = open("build.py", encoding="utf-8").read().split("\ndef main")[0]
B = {"__file__": "build.py"}
exec(compile(src, "build.py", "exec"), B)
nodes, order = B["parse"](sorted(glob.glob("src/*.txt")))
inc = defaultdict(list)
for nid in order:
    for c in nodes[nid]["choices"]:
        inc[c["to"]].append((nid, c))
pat = sys.argv[1]
W = int(sys.argv[2]) if len(sys.argv) > 2 else 230
for nid in order:
    if not re.match(pat, nid): continue
    preds = {p for p, _ in inc[nid]}
    if len(preds) < 2: continue
    n = nodes[nid]
    print(f"\n@{nid} [{n.get('title','')}]")
    for l in n["lines"]:
        cond = " ".join("?" + x for x in l["if"])
        sens = any(x.lstrip("!").startswith(("from:", "last:")) for x in l["if"])
        if not l["if"] or sens:
            print("   ", cond, l["t"][:W])
    for p, c in inc[nid]:
        print(f"   <- {p} {'jet' if c['stat']!='auto' else 'auto'} {' '.join('?'+x for x in c['if'])[:40]} | {c['label'][:60]}")
