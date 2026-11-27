"""Garde-fou des images de lieux. Lancé par build.py (bloquant) ; seul : python3 tools/images_check.py [--ecrire] [préfixe...]

Pourquoi : une image de lieu est choisie par lieux.json. Deux pièges l'ont déjà faussée :
  1. une ligne de lieux.json écrite pour le mauvais nœud (les archives affichaient le bureau de Platine en rouge) ;
  2. l'héritage : un nœud sans entrée garde l'image du nœud précédent, donc une erreur se propage à toute la suite.

Ce que le script vérifie :
  - réserve : une image « spéciale » (bureau de Platine, alarme rouge, Lune, rêve de Platine...) n'est affichée que par les
    nœuds dont l'identifiant correspond aux motifs de controle.reserve ;
  - signatures : si le titre ou le début du texte d'un nœud nomme un lieu qui a son image (archives, géode, station de pompage...)
    et que le nœud affiche une autre image, c'est une erreur pour les histoires vérifiées (préfixes « stricts »),
    sauf si le nœud est listé dans controle.revues après examen ;
  - nœuds listés pour deux images, nœuds inconnus, fichiers manquants ;
  - images orphelines (fichier jamais affiché) et images à créer encore provisoires (voir lieux_a_creer.md) ;
  - héritage restant (préfixes non stricts) : nombre de nœuds dont l'image dépend du chemin, pour information.
Écrit index/images.tsv (nœud, image, nom du lieu, origine) avec --ecrire ou en exécution seule."""
import os, sys, re, json, glob, collections

def _texte(n):
    return " ".join([n.get("title", "")] + [l["t"] for l in n["lines"][:2]])

def controler(L, nodes, order, nmap, infos, HERE, ecrire=False):
    ctl = L.get("controle", {})
    stricts = set(L.get("stricts", []))
    names = {l["image"]: l["nom"] for l in L["lieux"]}
    names.update({a["image"]: a["nom"] for a in L.get("a_creer", [])})
    fam = {}
    for f in ctl.get("familles", []):
        for i in f: fam[i] = tuple(f)
    errs, warns = [], []
    for m in infos["avert"]:
        pre = m.split()[2].split("_")[0] if m.startswith("nœud ") and len(m.split()) > 2 else ""
        grave = "inconnu" in m or "préfixe strict" in m or ("deux images" in m and pre in stricts)
        (errs if grave else warns).append("lieux.json : " + m)
    # 1. images réservées
    for img, pats in ctl.get("reserve", {}).items():
        rx = [re.compile(p) for p in pats]
        for nid in order:
            if nmap.get(nid) == img and not any(r.search(nid) for r in rx):
                errs.append(f"{nid} affiche l'image réservée {img} ({names.get(img, '?')}) hors de son contexte")
    # 2. signatures texte -> lieu
    sig = {i: re.compile(p, re.I) for i, p in ctl.get("signatures", {}).items()}
    revues = set(ctl.get("revues", []))
    nsig_info = 0
    for nid in order:
        img = nmap.get(nid)
        if not img: continue
        t = _texte(nodes[nid])
        own = fam.get(img, (img,))
        if any(i in sig and sig[i].search(t) for i in own): continue
        evoque = [i for i, r in sig.items() if i not in own and r.search(t) and not any(i in f and img in f for f in ctl.get("familles", []))]
        if not evoque or nid in revues: continue
        msg = f"{nid} affiche {img} ({names.get(img, '?')}) mais son texte évoque {', '.join(evoque)} ({names.get(evoque[0], '?')})"
        if nid.split("_")[0] in stricts: errs.append(msg + " [à corriger, ou à lister dans controle.revues après examen]")
        else: nsig_info += 1
    if nsig_info: warns.append(f"{nsig_info} nœud(s) d'histoires non vérifiées (préfixes hors « stricts ») affichent une image dont le lieu diffère de celui que leur texte nomme")
    # 3. fichiers, orphelines, images à créer
    used = collections.Counter(nmap.values())
    for p in infos.get("ranges", {}).values(): used[p] += 0
    files = {os.path.basename(f)[:-5] for f in glob.glob(os.path.join(HERE, "img", "lieux", "*.webp")) if "-800" not in f}
    for img in sorted(files):
        if used[img] == 0 and img not in ctl.get("orphelines_tolerees", []) and not any(img == d for d in L["defauts"].values()):
            warns.append(f"image orpheline : {img} ({names.get(img, '?')}) n'est affichée par aucun nœud")
        if img + "-800" not in {os.path.basename(f)[:-5] for f in glob.glob(os.path.join(HERE, "img", "lieux", "*-800.webp"))}:
            errs.append(f"image {img} sans version -800")
    for a in L.get("a_creer", []):
        if a["image"] not in files:
            warns.append(f"image à créer {a['image']} « {a['nom']} » : les scènes {a['scenes']} affichent {a['provisoire']} en attendant (prompt dans {a.get('prompt', 'lieux_a_creer.md')})")
    # 4. héritage restant hors stricts
    heri = collections.Counter(nid.split("_")[0] for nid in order if nid not in nmap)
    if heri:
        warns.append("nœuds sans image fixe (ils reprennent l'image du nœud précédent, donc dépendent du chemin) : " +
                     ", ".join(f"{p} {c}" for p, c in sorted(heri.items(), key=lambda x: -x[1])))
    for w in warns: print("  attention :", w)
    for e in errs: print("  ERREUR image :", e)
    print(f"images : {len(errs)} erreur(s), {len(warns)} avertissement(s)")
    if ecrire:
        d = os.path.join(HERE, "index"); os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "images.tsv"), "w", encoding="utf-8") as f:
            f.write("noeud\timage\tlieu\torigine\ttitre\n")
            for nid in order:
                img = nmap.get(nid)
                if img: org = "isolé" if nid in infos["singles"] else ("plage" if nid in infos["ranges"] else "défaut de préfixe")
                else: org = "hérite du nœud précédent"
                f.write(f"{nid}\t{img or ''}\t{names.get(img, '')}\t{org}\t{nodes[nid].get('title', '')}\n")
    return errs

if __name__ == "__main__":
    HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(HERE)
    src = open("build.py", encoding="utf-8").read().split("\ndef main")[0]
    b = {"__file__": os.path.join(HERE, "build.py")}
    exec(compile(src, "build.py", "exec"), b)
    nodes, order = b["parse"](sorted(glob.glob("src/*.txt")))
    L = json.load(open("lieux.json", encoding="utf-8"))
    nmap, names, infos = b["resolve_lieux"](L, nodes, order)
    errs = controler(L, nodes, order, nmap, infos, HERE, ecrire=True)
    sys.exit(1 if errs else 0)
