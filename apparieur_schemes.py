# -*- coding: utf-8 -*-
"""Appariement de schèmes de pensée — couche par-dessus les opérations d'AnalyserV9.
Câblage réel : notion_id (→ notions.termes) pour ops_ref ; pec_ref (→ pec[].adhesion) pour σ.
Ajouts v0.2 : score de filature (carte_operations) et degré de réalisation du θ5.
Usage : python3 apparieur_schemes.py resultats_batch.json schemes.json
"""
import json, re, sys, collections

CHAMPS_TEXTE = ("titre", "chapo", "texte", "texte_complet", "texte_analyse")

def _borne(motif):
    """Encadre un déclencheur de bornes de mots pour éviter les sous-chaînes
    (« séquence » ⊂ « conséquences »). N'ajoute pas de borne si le motif
    commence/finit déjà par une ancre ou une classe non alphabétique."""
    g = r"(?<![0-9A-Za-zÀ-ÿ])" if motif[:1].isalnum() or motif[0] in "[(" else ""
    d = r"(?![0-9A-Za-zÀ-ÿ])" if motif[-1:].isalnum() or motif[-1] in "])?+*" else ""
    return g + "(?:" + motif + ")" + d

def charger_schemes(path="schemes.json"):
    schemes = json.load(open(path, encoding="utf-8"))["schemes"]
    for s in schemes:                       # pré-compile les déclencheurs bornés
        s["_decl_re"] = [re.compile(_borne(d), re.I) for d in s["declencheurs"]]
    return schemes

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
    """Opérations co-présentes : internes (operations, notion_id) + relationnelles
    (determinations, notion_ids — c'est là que vivent ρ et θ5)."""
    nids = notions_dans(phrase, art.get("notions", []))
    pecs = art.get("pec", [])
    refs = []
    for o in art.get("operations", []):
        if o.get("notion_id") in nids:
            pr = o.get("pec_ref")
            adh = pecs[pr].get("adhesion") if isinstance(pr, int) and 0 <= pr < len(pecs) else None
            refs.append({"op": o.get("op"), "notion": o.get("notion"),
                         "ajout": o.get("ajout"), "adhesion": adh})
    for d in art.get("determinations", []):
        dids = d.get("notion_ids") or ([d["notion_id"]] if d.get("notion_id") else [])
        if nids.intersection(dids):
            pr = d.get("pec_ref")
            adh = pecs[pr].get("adhesion") if isinstance(pr, int) and 0 <= pr < len(pecs) else None
            co = (d.get("classe_objet") or {})
            refs.append({"op": d.get("op"), "notion": d.get("notion"),
                         "ajout": d.get("ajout"), "adhesion": adh,
                         "hyperonyme": co.get("hyperonyme")})
    return refs

def theta5_reel(phrase, art, sch=None):
    """Le θ5 que l'analyseur a DÉJÀ posé (determinations op θ5), s'il recoupe la
    phrase ET qu'il relève bien de CE schème. Le filtre schème évite de prendre
    un θ5 étranger (p. ex. « Claude/ChatGPT → les deux IA ») pour le θ5 de
    l'analogie en cours. Renvoie l'hyperonyme (ou une marque) sinon None."""
    nids = notions_dans(phrase, art.get("notions", []))
    for d in art.get("determinations", []):
        if not str(d.get("op", "")).startswith("θ5"):
            continue
        co = d.get("classe_objet") or {}
        cib = set(co.get("co_notions") or d.get("notion_ids") or [])
        if not nids.intersection(cib):
            continue
        if sch is not None:                 # le θ5 doit être CELUI du schème
            hyper = (co.get("hyperonyme") or "") + " " + (d.get("ajout") or "")
            cles = sch.get("hyperonyme", []) + sch.get("declencheurs", [])
            if not any(re.search(k, hyper, re.I) for k in cles):
                continue
        return co.get("hyperonyme") or "(classe posée)"
    return None

# Vocabulaire unique de prise en charge (σ) : 3 niveaux.
#   assume   : le locuteur prend en charge (assertion non marquée, adhésion totale)
#   suspendu : engagement retenu (conditionnel, soupçon, adhésion suspendue/partielle/contestée)
#   attribue : reporté à une source (citation, « selon X », adhésion attribuée)
_SIGMA = {
    "totale": "assume", "assumee": "assume", "assumée": "assume",
    "suspendue": "suspendu", "partielle": "suspendu", "contestee": "suspendu",
    "contestée": "suspendu", "neutralisee": "suspendu", "neutralisée": "suspendu",
    "attribuee": "attribue", "attribuée": "attribue", "citee": "attribue", "citée": "attribue",
}

def marquage_occurrence(refs):
    """Niveau de PEC lu sur la σ réelle de l'analyseur (pec.adhesion)."""
    adh = [_SIGMA.get(r["adhesion"], r["adhesion"]) for r in refs if r.get("adhesion")]
    if not adh:
        return None
    c = collections.Counter(adh)
    for a in ("suspendu", "attribue"):     # suspension > attribution > assomption
        if a in c:
            return a
    return c.most_common(1)[0][0]

def marquage_regex(phrase):
    """Repli quand aucune σ ne couvre la phrase — même vocabulaire à 3 niveaux."""
    pl = phrase.lower()
    if re.search(r"\b(aurait|serait|suspect\w+|soupçonn\w+|présum\w+|all[ée]gu\w+|all[ée]gation|pourrait)", pl):
        return "suspendu"
    if re.search(r"«[^»]{0,160}»", phrase) or re.search(r"\b(selon|d['’]après|rapporte|affirme|dément)\b", pl):
        return "attribue"
    return "assume"

# --- degré de réalisation du θ5 ----------------------------------------------
RE_APPOS = re.compile(r",\s+(?:cette?|un|une|le|la|les)\s+[A-ZÉÈÀ]")
def degre_theta5(phrase, sch, art=None):
    pl = phrase.lower()
    # 0. θ5 RÉEL du schème, déjà posé par l'analyseur (determinations) → le plus fiable
    if art is not None and theta5_reel(phrase, art, sch):
        return "theta5_complet"
    # 1. classe nommée du catalogue présente dans la phrase
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

# --- moisson des determinations de l'analyseur (proposeur) -------------------
def moissonner_determinations(art):
    """Récolte ce que l'analyseur a DÉJÀ posé, indépendamment du catalogue :
    - θ5 à pôle « inflation » = candidats de CAPTURE (co-hyperonyme qui subsume) ;
    - antiphrases / σ-inversions = retournements d'énonciation.
    C'est ce qui fait de la post-passe un *proposeur* : elle montre un schème de
    capture même quand aucune entrée du catalogue ne correspond encore."""
    noms = {n["id"]: n.get("label", n["id"]) for n in art.get("notions", [])}
    t5, iro = [], []
    for d in art.get("determinations", []):
        co = d.get("classe_objet") or {}
        if str(d.get("op", "")).startswith("θ5") and co.get("pole") == "inflation":
            r = d.get("risk") or {}
            t5.append({
                "hyperonyme": co.get("hyperonyme"),
                "co_notions": [noms.get(i, i) for i in (co.get("co_notions") or d.get("notion_ids") or [])],
                "intension": co.get("intension"),
                "source_classe": co.get("source_classe"),
                "ajout": d.get("ajout"),
                "risk": r.get("label") or r.get("level"),
            })
    for a in art.get("antiphrase", []) or []:        # bloc dédié de l'analyseur
        paire = a.get("paire") or {}
        iro.append({
            "notion": a.get("notion") or noms.get(a.get("notion_id"), a.get("notion_id")),
            "positif": (paire.get("positif") or {}).get("ajout"),
            "negatif": (paire.get("negatif") or {}).get("ajout"),
            "marqueurs": [m.get("extrait") for m in a.get("marqueurs", []) if m.get("extrait")],
        })
    if not iro:                                       # repli : pec marquées antiphrase
        for pc in art.get("pec", []):
            if pc.get("fonction") == "antiphrase" or pc.get("inversion_sigma"):
                iro.append({"text": pc.get("text"), "adhesion": pc.get("adhesion"),
                            "notion": noms.get(pc.get("notion_id"), pc.get("notion_id"))})
    return {"theta5_inflation": t5, "antiphrases": iro}

# --- appariement -------------------------------------------------------------
def apparier(art, schemes):
    t = texte(art); ph = phrases(t); hits = []
    for sch in schemes:
        occ = []; vus = set()
        decls = sch.get("_decl_re") or [re.compile(_borne(d), re.I) for d in sch["declencheurs"]]
        for p in ph:
            if p in vus:                      # dédoublonne les phrases identiques
                continue
            if any(r.search(p) for r in decls):
                vus.add(p)
                refs = ops_ref(p, art)
                occ.append({
                    "phrase": p[:220], "source": art.get("source", "?"),
                    # AXE 1 — construction notionnelle (pré-énoncé) :
                    "construction": {"degre_theta5": degre_theta5(p, sch, art),
                                     "ops_ref": refs[:6]},
                    # AXE 2 — prise en charge (énonciation, en aval) :
                    "prise_en_charge": {"marquage": marquage_occurrence(refs) or marquage_regex(p)},
                })
        if occ:
            ops_agg = collections.Counter()
            for o in occ:
                for r in o["construction"]["ops_ref"]:
                    ops_agg[r["op"]] += 1
            hits.append({
                "id": sch["id"], "valence": sch["valence"], "n": len(occ),
                # les deux axes, séparés, au niveau du schème :
                "construction": {
                    "filature": score_filature(art, sch),
                    "operations": dict(ops_agg.most_common()),   # la signature (ρ3/γ1 vs γ3/θ2)
                    "degres_theta5": dict(collections.Counter(
                        o["construction"]["degre_theta5"] for o in occ)),
                },
                "prise_en_charge": {
                    "marquage": dict(collections.Counter(
                        o["prise_en_charge"]["marquage"] for o in occ)),
                },
                "occurrences": occ[:8],
            })
    return {"schemes": hits,
            "candidats_theta5": candidats_theta5(t),
            "candidats_analyseur": moissonner_determinations(art)}

def traiter(corpus, schemes):
    r = corpus if isinstance(corpus, list) else next(v for v in corpus.values() if isinstance(v, list))
    for a in r:
        a["analyse_schemes"] = apparier(a, schemes)
    return r

if __name__ == "__main__":
    import argparse, os
    p = argparse.ArgumentParser(description="Post-passe schèmes sur un batch de l'analyseur.")
    p.add_argument("batch"); p.add_argument("schemes", nargs="?", default="schemes.json")
    p.add_argument("--out", default=None, help="fichier enrichi (défaut : <batch>__schemes.json)")
    a = p.parse_args()
    corpus = json.load(open(a.batch, encoding="utf-8"))
    schemes = charger_schemes(a.schemes)
    arts = traiter(corpus, schemes)
    out = a.out or os.path.splitext(a.batch)[0] + "__schemes.json"
    json.dump(arts, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    g = collections.Counter(); ct5 = 0; cir = 0
    for x in arts:
        asx = x["analyse_schemes"]
        for h in asx["schemes"]:
            g[h["id"]] += h["n"]
        ca = asx.get("candidats_analyseur", {})
        ct5 += len(ca.get("theta5_inflation", []))
        cir += len(ca.get("antiphrases", []))
    print("schèmes catalogue:", dict(g) or "(aucun)")
    print(f"candidats analyseur: θ5-inflation={ct5}, antiphrases={cir}", "→", out)
