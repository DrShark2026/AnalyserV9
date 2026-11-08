#!/usr/bin/env python3
"""Dossier orelien_denouement : tri, codage OR-DEN-xx et sortie pour l'analyseur (17.11).

S'enchaîne avec dossier.py, d'après la fiche corpus/dossiers/orelien_denouement/meta_orelien_denouement.json :

    python3 dossier.py orelien_denouement <requêtes> --jusqu-au … --jours … --garder   # étape 1
    python3 denouement.py --amorcer                                                  # avant l'étape 2
    .venv/bin/python dossier.py orelien_denouement --textes                          # étape 2
    python3 denouement.py                                                            # tri et codage

--amorcer : les articles du lot déjà présents dans le corpus Orélien (lots orelien et orelien_maj_1026,
pièces OR-ADD-xx) reçoivent dans textes.json le texte déjà récupéré pour le cœur : l'étape 2 ne les
rouvre pas.

Sans option : écarte ces doublons du cœur (même URL normalisée, comme dossier.py, ou même titre dans
la même source ; pour les pièces OR-ADD, même titre), relève les mnémoniques de la fiche
(mnemoniques_fiche : indices, n'influent pas sur la sélection), rattache chaque article aux actes de la
fiche par des indices lexicaux (actes, actes_indices : I soupçon, II Jaenada, III Fitoussi), reconnaît
les cibles connues (OR-DEN-01 à 07) et numérote les autres articles à partir de OR-DEN-08, par date.

Garde-fous de la fiche : les pièces réservées aux abonnés marquées vo_manuelle (Fitoussi du 07/11,
phrase d'IA de Jaenada du 04/11) ont un texte vide et texte_a_fournir « VO à fournir manuellement »,
même quand Google Actualités les trouve ; une cible introuvable a une entrée du même type, avec
les seules métadonnées de la fiche. Aucun texte n'est traduit ni reconstitué. Les verdicts de détecteurs
(Pangram) sont repérés (mentionne_detecteur), jamais validés.

Sortie, dans corpus/dossiers/orelien_denouement/ :
    resultats_orelien_denouement_AAAA-MM-JJ.json   méta (fiche, doublons écartés, cibles, décomptes) + toutes les entrées
    lot_17-11_orelien_denouement_AAAA-MM-JJ.json   les seules entrées qui ont un texte, à coller dans l'analyseur
"""
import argparse
import collections
import datetime as dt
import json
import re
from pathlib import Path

from collect_rss import normaliser, sans_accents
from dossier import SORTIE, cle_titre, ecrire_json

NOM = "orelien_denouement"
DOSSIER = SORTIE / "dossiers" / NOM
FICHE = DOSSIER / f"meta_{NOM}.json"
COEUR = [SORTIE / "dossiers" / "orelien", SORTIE / "dossiers" / "orelien_maj_1026"]
VO_A_FOURNIR = "VO à fournir manuellement"

ACTES = {   # indices lexicaux, cherchés sans accents ni majuscules dans titre, texte et texte complet
    "I": r"\borelien\b|c.etait ca ou mourir|\bnothomb\b|\bbeigbeder\b",
    "II": r"\bjaenada\b|\bgoncourt\b|inconnue du quai de javel",
    "III": r"\bfitoussi\b|\bpangram\b|balance ton claude",
}
DETECTEUR = r"\bpangram\b|detecteur|detector|gptzero|originality"

# Cibles connues de la fiche. source : fragment du nom de la source ; date : à un jour près ;
# titre : motifs qui doivent TOUS figurer dans le titre ; corps : motifs qui doivent TOUS figurer
# dans le titre ou le texte. vo_manuelle : texte jamais versé depuis la collecte.
CIBLES = {
    "OR-DEN-01": {"acte": "III", "source": "figaro", "date": "2026-11-07", "titre": [r"fitoussi|genie humain|admirera"],
                  "vo_manuelle": True, "source_fiche": "Le Figaro / Vox Culture", "auteur": "Samuel Fitoussi",
                  "titre_fiche": "À l'ère des productions culturelles générées par l'IA, qui admirera encore le génie humain ?"},
    "OR-DEN-02": {"acte": "I", "source": "figaro", "date": "2026-10-21",
                  "titre": [r"editeur canadien|a bien ete utilisee"], "source_fiche": "Le Figaro",
                  "titre_fiche": "L'IA a bien été utilisée dans l'écriture du roman de Thélyson Orélien, annonce son éditeur canadien"},
    "OR-DEN-03": {"acte": "II", "source": "figaro", "date": "2026-11-04", "titre": [r"jaenada", r"\bia\b|phrase|intelligence artificielle"],
                  "vo_manuelle": True, "source_fiche": "Le Figaro",
                  "titre_fiche": "Philippe Jaenada (Goncourt 2026) a écrit une phrase avec l'IA dans son livre pour jouer avec le lecteur"},
    "OR-DEN-04": {"acte": "II", "date": "2026-11-03", "titre": [r"goncourt", r"jaenada|inconnue du quai de javel"],
                  "titre_fiche": "Couverture de la remise du Goncourt 2026 à Philippe Jaenada pour « L'Inconnue du quai de Javel »"},
    "OR-DEN-05": {"acte": "I", "corps": [r"nothomb|beigbeder", r"orelien"],
                  "titre_fiche": "Défenses d'Amélie Nothomb et Frédéric Beigbeder (« le texte de Thélyson est très bien ») — source à retrouver"},
    "OR-DEN-06": {"acte": None, "corps": [r"kasparov"],
                  "titre_fiche": "Le contre-texte « moment Kasparov » (fil Reddit/X : échecs, ping-pong, théâtre/cinéma, peinture/photographie) — à archiver"},
    "OR-DEN-07": {"acte": "III", "corps": [r"balance ton claude|pangram", r"orelien|fitoussi"],
                  "titre_fiche": "Le compte X « Balance ton Claude » (Fitoussi) et la révélation du verdict Pangram sur le roman d'Orélien"},
}


def lire(f):
    return json.loads(Path(f).read_text("utf-8"))


def titre_de(a):
    return a.get("texte", "").partition("\n\n")[0] or a.get("titre", "")


def plein(a):
    return sans_accents(" ".join(filter(None, [a.get("titre"), a.get("texte"), a.get("texte_complet")])))


def coeur():
    """Index du corpus Orélien déjà collecté : URL normalisées, (source, titre), titres seuls des pièces OR-ADD,
    et les entrées de textes.json par URL normalisée."""
    urls, titres, titres_add, textes = {}, {}, {}, {}
    for d in COEUR:
        lot = lire(d / f"lot_{d.name}.json")
        cache = lire(d / "textes.json") if (d / "textes.json").exists() else {}
        for a in lot:
            urls[normaliser(a["lien"])] = a["id"]
            titres[(sans_accents(a["source"]), cle_titre(titre_de(a)))] = a["id"]
            if a["id"] in cache:
                textes[normaliser(a["lien"])] = cache[a["id"]]
        for f in sorted(d.glob("OR-ADD-*.json")):
            for a in (lambda x: x if isinstance(x, list) else [x])(lire(f)):
                titres_add[cle_titre(titre_de(a))] = a["id"]
    return urls, titres, titres_add, textes


def dans_coeur(a, idx):
    urls, titres, titres_add, _ = idx
    t = cle_titre(titre_de(a))
    return urls.get(normaliser(a["lien"])) or titres.get((sans_accents(a["source"]), t)) or titres_add.get(t)


def amorcer():
    idx = coeur()
    lot = lire(DOSSIER / f"lot_{NOM}.json")
    cache_f = DOSSIER / "textes.json"
    cache = lire(cache_f) if cache_f.exists() else {}
    n = 0
    for a in lot:
        if a["id"] in cache or not dans_coeur(a, idx):
            continue
        c = idx[3].get(normaliser(a["lien"]))
        cache[a["id"]] = dict(c) if c else {"texte_complet": None, "statut": "echec",
                                            "raison": "déjà dans le corpus Orélien : non rouvert", "passager": False}
        n += 1
    ecrire_json(cache_f, cache)
    print(f"{n} article(s) déjà dans le corpus Orélien : textes.json amorcé, l'étape 2 ne les rouvrira pas")


def correspond(a, c):
    t, p = sans_accents(titre_de(a)), plein(a)
    if c.get("source") and c["source"] not in sans_accents(a["source"]):
        return None
    if c.get("date"):
        if not a.get("date"):
            return None
        ecart = abs((dt.date.fromisoformat(a["date"]) - dt.date.fromisoformat(c["date"])).days)
        if ecart > 1:
            return None
    else:
        ecart = 0
    if not all(re.search(m, t) for m in c.get("titre", [])) or not all(re.search(m, p) for m in c.get("corps", [])):
        return None
    return (ecart, -len(p))    # date exacte d'abord, puis le texte le plus long


def entree_vide(code, c):
    return {"id": code, "code": code, "cible": True, "trouve": False, "source": c.get("source_fiche", ""),
            "auteur": c.get("auteur", ""), "categorie": "", "pays": "", "orientation": "", "degre": "", "posture_ia": "",
            "langue": "fr", "date": c.get("date", ""), "lien": "", "themes": [NOM], "titre_fiche": c["titre_fiche"],
            "texte": "", "texte_a_fournir": VO_A_FOURNIR, "statut_texte": "a_fournir", "verite_terrain": None,
            "actes": [c["acte"]] if c["acte"] else [], "actes_indices": {}, "mnemoniques_fiche": [],
            "mentionne_detecteur": False, "n_mots": 0}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--amorcer", action="store_true", help="avant dossier.py --textes : reprendre les textes du cœur")
    args = ap.parse_args()
    if args.amorcer:
        return amorcer()

    fiche = lire(FICHE)
    meta_dossier = lire(DOSSIER / "meta.json")
    raisons = meta_dossier.get("textes", {}).get("raisons", {})
    idx = coeur()
    mnemo = [(m, re.compile(r"(?<!\w)" + re.escape(sans_accents(m)) + r"(?!\w)")) for m in fiche["mnemoniques_collecte"]]

    articles, ecartes = [], []
    for a in lire(DOSSIER / f"lot_{NOM}.json"):
        if (deja := dans_coeur(a, idx)):
            ecartes.append({"id": a["id"], "doublon_de": deja, "source": a["source"], "titre": titre_de(a)})
            continue
        p = plein(a)
        a["id_dossier"] = a["id"]
        a["mnemoniques_fiche"] = sorted(m for m, rx in mnemo if rx.search(p))
        indices = {n: sorted(set(re.findall(rx, p))) for n, rx in ACTES.items()}
        a["actes"] = [n for n in ACTES if indices[n]]
        a["actes_indices"] = {n: v for n, v in indices.items() if v}
        a["mentionne_detecteur"] = bool(re.search(DETECTEUR, p))
        if raisons.get(a["id"], "").startswith("réservé aux abonnés"):
            a["reserve_abonnes"] = True
        articles.append(a)

    codes, cibles_meta = {}, {}
    for code, c in CIBLES.items():
        cands = sorted((k, i) for i, a in enumerate(articles) if i not in codes.values() and (k := correspond(a, c)))
        if cands:
            codes[code] = cands[0][1]
        cibles_meta[code] = {"titre_fiche": c["titre_fiche"], "trouve": bool(cands),
                             "candidats": [articles[i]["id_dossier"] for _, i in cands]}

    entrees = []
    for code, c in CIBLES.items():
        if code not in codes:
            entrees.append(entree_vide(code, c))
            continue
        a = articles[codes[code]]
        a.update(id=code, code=code, cible=True, trouve=True, titre_fiche=c["titre_fiche"])
        if c.get("vo_manuelle"):
            a["titre"] = titre_de(a)
            a["texte"], a["texte_a_fournir"], a["statut_texte"], a["n_mots"] = "", VO_A_FOURNIR, "a_fournir", 0
            a.pop("texte_complet", None)
            a.pop("n_mots_complet", None)
        entrees.append(a)
    reste = sorted((a for i, a in enumerate(articles) if i not in codes.values()),
                   key=lambda a: (a.get("date") or "9999", sans_accents(a["source"])))
    for n, a in enumerate(reste, start=len(CIBLES) + 1):
        a.update(id=f"OR-DEN-{n:02d}", code=f"OR-DEN-{n:02d}", cible=False)
        entrees.append(a)

    a_analyser = [a for a in entrees if a.get("texte")]
    jour = dt.date.today().isoformat()
    compte_actes = collections.Counter(n for a in entrees for n in a["actes"])
    resultats = {
        "dossier": NOM,
        "produit": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        "analyseur": "17.11 (à passer : lot_17-11_" + NOM + f"_{jour}.json)",
        "fiche": {k: fiche[k] for k in ("titre", "date_debut", "date_fin", "langues", "note")},
        "collecte": {"date": meta_dossier.get("collecte"), "requetes": meta_dossier.get("requetes"),
                     "editions": list(meta_dossier.get("editions", {})), "jours": meta_dossier.get("jours"),
                     "jusqu_au": meta_dossier.get("jusqu_au"), "textes": meta_dossier.get("textes", {}).get("statuts")},
        "garde_fous": ["VO seule, jamais de rétrotraduction ni de texte reconstitué",
                       f"pièces réservées aux abonnés de la fiche : texte vide, « {VO_A_FOURNIR} »",
                       "verdicts de détecteurs (Pangram) décrits, non validés ; Fitoussi partie à l'affaire, "
                       "Anthropic/Claude partie au débat (conflit d'intérêts)",
                       "actes : indices lexicaux automatiques, à relire"],
        "doublons_du_coeur_ecartes": ecartes,
        "cibles": cibles_meta,
        "decomptes": {"entrees": len(entrees), "articles_collectes": len(articles), "a_analyser": len(a_analyser),
                      "vo_a_fournir": sum(1 for a in entrees if a.get("texte_a_fournir")),
                      "doublons_du_coeur": len(ecartes),
                      "par_acte": {n: compte_actes.get(n, 0) for n in ACTES},
                      "hors_actes": sum(1 for a in entrees if not a["actes"]),
                      "par_source": dict(collections.Counter(a["source"] for a in entrees if a.get("lien")).most_common()),
                      "statuts_texte": dict(collections.Counter(a.get("statut_texte", "") for a in entrees))},
        "articles": entrees,
    }
    sortie = DOSSIER / f"resultats_{NOM}_{jour}.json"
    ecrire_json(sortie, resultats)
    ecrire_json(DOSSIER / f"lot_17-11_{NOM}_{jour}.json", a_analyser)

    d = resultats["decomptes"]
    print(f"{sortie.name} : {d['entrees']} entrées ({d['articles_collectes']} articles collectés hors cœur, "
          f"{d['doublons_du_coeur']} doublons du cœur écartés), {d['a_analyser']} à analyser, {d['vo_a_fournir']} VO à fournir")
    print("  actes : " + ", ".join(f"{n} {k}" for n, k in d["par_acte"].items()) + f", hors actes {d['hors_actes']}")
    for code, c in cibles_meta.items():
        print(f"  {code} {'trouvée ' if c['trouve'] else 'MANQUANTE'} {c['titre_fiche'][:70]}")


if __name__ == "__main__":
    main()
