# -*- coding: utf-8 -*-
"""Appariement de schèmes de pensée — couche par-dessus les opérations d'AnalyserV9.
Câblage réel : notion_id (→ notions.termes) pour ops_ref ; pec_ref (→ pec[].adhesion) pour σ.
Ajouts v0.2 : score de filature (carte_operations) et degré de réalisation du θ5.
Usage : python3 apparieur_schemes.py resultats_batch.json schemes.json
"""
import json, re, sys, collections

CHAMPS_TEXTE = ("titre", "chapo", "texte", "texte_complet", "texte_analyse")

def charger_schemes(path="schemes.json"):
    return json.load(open(path, encoding="utf-8"))["schemes"]

def texte(a):
    return "  ".join(str(a[k]) for k in CHAMPS_TEXTE if isinstance(a.get(k), str))

def phrases(t):
    return [re.sub(r"\s+", " ", s).strip() for s in re.split(r"(?<=[.!?»])\s+", t)]

# --- câblage opérations (notion_id / pec_ref) --------------------------------
def notions_dans(phrase, notions):
    pl, out = phrase.lower(), []
    for n in notions:
        formes = list(n.get("termes", [])) + [n.get("label", "").strip("/")]
        if any(f and f.lower() in pl for f in formes):
            out.append(n["id"])
    return set(out)

def ops_ref(phrase, art):
    nids = notions_dans(phrase, art.get("notions", []))
    pecs = art.get("pec", [])
    refs = []
    for o in art.get("operations", []):
        if o.get("notion_id") in nids:
            pr = o.get("pec_ref")
            adh = pecs[pr].get("adhesion") if isinstance(pr, int) and 0 <= pr < len(pecs) else None
            refs.append({"op": o.get("op"), "notion": o.get("notion"),
                         "ajout": o.get("ajout"), "adhesion": adh})
    return refs

def marquage_occurrence(refs):
    adh = [r["adhesion"] for r in refs if r["adhesion"]]
    if not adh:
        return None
    c = collections.Counter(adh)
    for a in ("suspendue", "attribuee", "attribuée", "contestee", "partielle"):
        if a in c:
            return a
    return c.most_common(1)[0][0]

def marquage_regex(phrase):
    pl = phrase.lower()
    if re.search(r"«[^»]{0,120}»", phrase): return "cite"
    if re.search(r"\b(aurait|serait|suspect\w+|soupçonn\w+|présum\w+|accus\w+|dément|selon|all[ée]gation)", pl):
        return "attribue"
    return "non_marque"

# --- degré de réalisation du θ5 ----------------------------------------------
RE_APPOS = re.compile(r",\s+(?:cette?|un|une|le|la|les)\s+[A-ZÉÈÀ]")
def degre_theta5(phrase, sch):
    pl = phrase.lower()
    # 1. classe nommée présente ? → θ5 complet
    for h in sch.get("hyperonyme", []):
        if h.lower() in pl:
            return "theta5_complet"
    # 2. figure appliquée en apposition (« X, cette Mata Hari »)
    if RE_APPOS.search(phrase):
        return "figure"
    # 3. comparaison explicite
    if re.search(r"\b(comme|tel(?:le)?s?|à la manière de|ainsi qu[e'])\b", pl):
        return "comparaison"
    # 4. simple évocation du déclencheur
    return "evocation"

# --- score de filature (carte_operations) ------------------------------------
def score_filature(art, sch):
    carte = sch.get("carte_operations")
    if not carte:
        return None
    t = texte(art).lower()
    inst = [c for c in carte if any(cle.lower() in t for cle in c.get("cles", []))]
    return {"score": round(len(inst) / len(carte), 2),
            "instanciees": len(inst), "total": len(carte),
            "ops": [c["op"] for c in inst]}

# --- candidats θ5 lexicalisés ------------------------------------------------
RE_T5 = re.compile(r"\b(?:une?|la|le|les)\s+([A-ZÉÈÀ][\w'’-]+(?:\s[A-ZÉÈÀ][\w'’-]+)?)\s+(?:du|de la|des|de)\s+([\w'’-]+)")
_STOP = {"affaire","relation","chine","nvidia","monde","face","plupart","série","suite","question"}
def candidats_theta5(t):
    out = [f"{m.group(1)} / {m.group(2)}" for m in RE_T5.finditer(t) if m.group(1).lower() not in _STOP]
    return sorted(set(out))[:10]

# --- appariement -------------------------------------------------------------
def apparier(art, schemes):
    t = texte(art); ph = phrases(t); hits = []
    for sch in schemes:
        occ = []
        for p in ph:
            if any(re.search(d, p, re.I) for d in sch["declencheurs"]):
                refs = ops_ref(p, art)
                occ.append({"phrase": p[:220],
                            "marquage": marquage_occurrence(refs) or marquage_regex(p),
                            "degre_theta5": degre_theta5(p, sch),
                            "source": art.get("source", "?"), "ops_ref": refs[:6]})
        if occ:
            hits.append({"id": sch["id"], "valence": sch["valence"], "n": len(occ),
                         "marquage": dict(collections.Counter(o["marquage"] for o in occ)),
                         "degres": dict(collections.Counter(o["degre_theta5"] for o in occ)),
                         "filature": score_filature(art, sch),
                         "occurrences": occ[:8]})
    return {"schemes": hits, "candidats_theta5": candidats_theta5(t)}

def traiter(corpus, schemes):
    r = corpus if isinstance(corpus, list) else next(v for v in corpus.values() if isinstance(v, list))
    for a in r:
        a["analyse_schemes"] = apparier(a, schemes)
    return r

if __name__ == "__main__":
    corpus = json.load(open(sys.argv[1], encoding="utf-8"))
    schemes = charger_schemes(sys.argv[2] if len(sys.argv) > 2 else "schemes.json")
    arts = traiter(corpus, schemes)
    g = collections.Counter()
    for a in arts:
        for h in a["analyse_schemes"]["schemes"]:
            g[h["id"]] += h["n"]
    print("schèmes repérés:", dict(g) or "(aucun)")
