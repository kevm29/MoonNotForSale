import sys, glob, re
sys.argv_saved = sys.argv[:]
import importlib.util
spec = importlib.util.spec_from_file_location("b", "build.py")
b = importlib.util.module_from_spec(spec)
src = open("build.py", encoding="utf-8").read().split("\ndef main")[0]
exec(compile(src, "build.py", "exec"), b.__dict__)
nodes, order = b.parse(sorted(glob.glob("src/*.txt")))
pat = sys.argv[1]
full = len(sys.argv) > 2
W = 400 if full else 110
for nid in order:
    if not re.match(pat, nid): continue
    n = nodes[nid]
    print(f"@{nid} [{n.get('title','')}] fx={' '.join(n['fx'])}")
    for l in n["lines"][: (99 if full else 1)]:
        print("   ", " ".join("?"+x for x in l["if"]), l["t"][:(W if full else 80)])
    for c in n["choices"]:
        print(f"  * {c['to']} {c['stat']}{c['diff'] if c['stat']!='auto' else ''} {' '.join('?'+x for x in c['if'])} | {c['label'][:70]} | fx {' '.join(c['okfx'])}")
