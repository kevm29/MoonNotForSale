import glob, sys
sys.path.insert(0, ".")
sys.setrecursionlimit(10000)
from build import parse
nodes, order = parse(sorted(glob.glob("src/*.txt")))
idx = {}; low = {}; st = []; on = set(); sccs = []; c = [0]
def sc(v):
    idx[v] = low[v] = c[0]; c[0] += 1; st.append(v); on.add(v)
    for ch in nodes[v]["choices"]:
        w = ch["to"]
        if w not in idx: sc(w); low[v] = min(low[v], low[w])
        elif w in on: low[v] = min(low[v], idx[w])
    if low[v] == idx[v]:
        comp = []
        while True:
            w = st.pop(); on.discard(w); comp.append(w)
            if w == v: break
        if len(comp) > 1: sccs.append(comp)
for v in order:
    if v not in idx: sc(v)
for s in sccs:
    print(len(s), sorted(s, key=order.index))
