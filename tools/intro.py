"""Noms propres cités dans un nœud (lignes sans condition) qu'un chemin peut atteindre sans les avoir jamais lus avant,
alors qu'ils sont présentés ailleurs en amont."""
import json, glob, re, sys
from collections import defaultdict, deque
src = open("build.py", encoding="utf-8").read().split("\ndef main")[0]
B = {"__file__": "build.py"}
exec(compile(src, "build.py", "exec"), B)
meta = json.load(open("meta.json", encoding="utf-8"))
nodes, order = B["parse"](sorted(glob.glob("src/*.txt")))
WORD = re.compile(r"(?<![.!?«:…] )(?<!^)\b([A-ZÉÈÀÂÎÔ][a-zéèêàâîôûçï]{3,}(?:-[A-ZÉ][a-zéèêàâîôûç]+)*)")
STOP = set((sys.argv[1] if len(sys.argv) > 1 else "").split(","))
allt, unc = {}, {}
for nid in order:
    n = nodes[nid]
    t = " ".join(l["t"] for l in n["lines"]) + " " + " ".join(c["label"] + " " + c["ok"] + " " + (c["ko"] or "") for c in n["choices"]) + " " + n.get("title", "")
    allt[nid] = set(WORD.findall(t))
    unc[nid] = set(WORD.findall(" ".join(l["t"] for l in n["lines"] if not l["if"])))
succ = {nid: {c["to"] for c in nodes[nid]["choices"]} for nid in order}
starts = [p["start"] for p in meta["playables"]]
# le texte du choix qui mène à N compte comme lu
inlab = defaultdict(set)
for nid in order:
    for c in nodes[nid]["choices"]:
        inlab[(nid, c["to"])] |= set(WORD.findall(c["label"] + " " + c["ok"] + " " + (c["ko"] or "")))
def reach_avoiding(W, target):
    seen = set(); q = deque(s for s in starts)
    while q:
        u = q.popleft()
        if u in seen: continue
        seen.add(u)
        if u == target: return True
        if W in allt[u]: continue
        for v in succ[u]:
            q.append(v)
    return False
anc = {}
pred = defaultdict(set)
for u in order:
    for v in succ[u]: pred[v].add(u)
def ancestors(n):
    s = set(); q = [n]
    while q:
        u = q.pop()
        for p in pred[u]:
            if p not in s: s.add(p); q.append(p)
    return s
for nid in order:
    A = None
    for W in sorted(unc[nid]):
        if W in STOP: continue
        if A is None: A = ancestors(nid) - {nid}
        ment = [a for a in A if W in allt[a]]
        if not ment: continue
        if reach_avoiding(W, nid):
            print(nid, W, "| présenté en", sorted(ment)[:4])
