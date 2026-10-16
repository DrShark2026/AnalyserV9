#!/usr/bin/env python3
"""Concordance (KWIC) d'une expression régulière sur tout le corpus de veille.

Parcourt corpus/veille_*.json et écrit un CSV, une ligne par occurrence :
    id, date, source, categorie, langue, champ (titre | chapô | texte_complet),
    guillemets : autour (le terme est dans un passage entre guillemets « », “ ”
    ou " " de 5 mots au plus), citation (passage plus long : discours rapporté)
    ou non,
    gauche, terme, droite (60 caractères de contexte de chaque côté), lien
Avec --avant-apres AAAA-MM-JJ, une colonne periode (avant | apres) est ajoutée
selon la date de l'article, et le bilan sépare les deux périodes.

Dans texte_complet, les paragraphes qui répètent le titre ou le chapô sont
sautés, pour ne pas compter deux fois la même occurrence.

La recherche tient compte des majuscules (sinon \\bSI\\b prendrait « si ») ;
-i l'en dispense, (?i:...) le fait pour une partie seulement.

Usage :
    python3 concordance.py 'frontier|fronti[eè]re' -i
    python3 concordance.py '(?i:superintelligen|super intelligence)|\\bSI\\b' --avant-apres 2026-09-01
    python3 concordance.py 'Vichy' -o corpus/vichy.csv
"""
import argparse
import collections
import csv
import json
import re
import sys
from pathlib import Path

from collect_rss import SORTIE

CONTEXTE = 60
MOTS_AUTOUR = 5          # au-delà, le passage entre guillemets est une citation
PAIRES = [("«", "»"), ("“", "”")]


def norm(t):
    return re.sub(r"\W+", " ", t.lower()).strip()


def guillemets(par, debut, fin):
    """autour | citation | non, selon le passage entre guillemets qui contient par[debut:fin]."""
    gauche, droite = par[:debut], par[fin:]
    passage = None
    for ouv, ferm in PAIRES:
        i = gauche.rfind(ouv)
        if i >= 0 and ferm not in gauche[i:] and ferm in droite:
            passage = par[i + 1:fin + droite.find(ferm)]
            break
    if passage is None and gauche.count('"') % 2 == 1 and '"' in droite:
        passage = par[gauche.rfind('"') + 1:fin + droite.find('"')]
    if passage is None:
        return "non"
    return "autour" if len(passage.split()) <= MOTS_AUTOUR else "citation"


def champs(a):
    """(champ, paragraphe) pour le titre, le chapô et le texte complet de l'article."""
    titre, _, chapo = a["texte"].partition("\n\n")
    yield "titre", titre
    for par in chapo.split("\n"):
        if par.strip():
            yield "chapô", par
    deja = {norm(titre), norm(chapo)}
    for par in (a.get("texte_complet") or "").split("\n"):
        if par.strip() and norm(par) not in deja:
            yield "texte_complet", par


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("motif", help="expression régulière (syntaxe Python)")
    ap.add_argument("-i", action="store_true", help="ignorer les majuscules")
    ap.add_argument("--avant-apres", metavar="AAAA-MM-JJ", help="séparer les occurrences avant et après cette date")
    ap.add_argument("-o", default=str(SORTIE / "concordance.csv"), help="fichier CSV (défaut : corpus/concordance.csv)")
    args = ap.parse_args()

    if args.avant_apres and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", args.avant_apres):
        ap.error("--avant-apres attend une date AAAA-MM-JJ")
    rx = re.compile(args.motif, re.I if args.i else 0)

    articles, vus = [], set()
    fichiers = sorted(SORTIE.glob("veille_*.json"))
    for f in fichiers:
        for a in json.loads(f.read_text("utf-8")):
            if a["id"] not in vus:
                vus.add(a["id"])
                articles.append(a)
    dates = sorted(a["date"] for a in articles if a.get("date"))
    print(f"{len(fichiers)} fichiers, {len(articles)} articles"
          + (f", du {dates[0]} au {dates[-1]}" if dates else ""))

    colonnes = ["id", "date", "source", "categorie", "langue", "champ", "guillemets", "gauche", "terme", "droite", "lien"]
    if args.avant_apres:
        colonnes.insert(2, "periode")
    lignes = []
    for a in articles:
        for champ, par in champs(a):
            for m in rx.finditer(par):
                d, f = m.span()
                ligne = {
                    "id": a["id"], "date": a.get("date") or "", "source": a["source"],
                    "categorie": a.get("categorie", ""), "langue": a.get("langue", ""), "champ": champ,
                    "guillemets": guillemets(par, d, f),
                    "gauche": par[max(0, d - CONTEXTE):d], "terme": m.group(), "droite": par[f:f + CONTEXTE],
                    "lien": a.get("lien", ""),
                }
                if args.avant_apres:
                    ligne["periode"] = "avant" if ligne["date"] and ligne["date"] < args.avant_apres else "apres"
                lignes.append(ligne)

    sortie = Path(args.o)
    with sortie.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=colonnes)
        w.writeheader()
        w.writerows(lignes)

    print(f"{len(lignes)} occurrence(s) dans {len({l['id'] for l in lignes})} article(s) → {sortie}")
    groupes = [("tout", lignes)]
    if args.avant_apres:
        groupes = [(f"{p} le {args.avant_apres}" if p == "avant" else f"à partir du {args.avant_apres}",
                    [l for l in lignes if l["periode"] == p]) for p in ("avant", "apres")]
    for nom, ls in groupes:
        if args.avant_apres:
            print(f"\n{nom} : {len(ls)} occurrence(s)")
        for cle in ("champ", "guillemets", "langue", "source"):
            c = collections.Counter(l[cle] for l in ls)
            if c:
                print(f"  {cle:<10} " + ", ".join(f"{k} {n}" for k, n in c.most_common()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
