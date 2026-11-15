"""Copies autonomes (doctype + Cytoscape intégré) dans dist/ (ou le dossier DIST)."""
import os, shutil, glob
HERE = os.path.dirname(os.path.abspath(__file__))
DST = os.environ.get("DIST", os.path.join(HERE, "dist"))
os.makedirs(DST, exist_ok=True)
HEAD = ('<!doctype html>\n<html lang="fr">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n')
TAG = '<script src="https://cdnjs.cloudflare.com/ajax/libs/cytoscape/3.28.1/cytoscape.min.js"></script>'
cy = open(os.path.join(HERE, "vendor_cytoscape.min.js"), encoding="utf-8").read()
for name in ("la-lune-vendue.html", "arbre-de-decision.html"):
    s = open(os.path.join(HERE, "out", name), encoding="utf-8").read()
    if TAG in s:
        s = s.replace(TAG, "<script>" + cy.replace("</script", "<\\/script") + "</script>")
    if not s.lstrip().lower().startswith("<!doctype"):
        s = HEAD + s
    open(os.path.join(DST, name), "w", encoding="utf-8").write(s)
    print("écrit", name, len(s))
