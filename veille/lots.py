#!/usr/bin/env python3
"""Lots pour l'analyseur à partir d'un corpus de veille.

Prend le dernier corpus/veille_*.json et écrit deux lots, prêts à coller
dans l'analyseur :
    corpus/lots/lot_ia_AAAA-MM-JJ.json          thème ia
    corpus/lots/lot_politique_AAAA-MM-JJ.json   thèmes immigration et religion

Chaque article garde ses champs ; « texte » reste le titre + chapô (c'est lui
que l'analyseur lit), « texte_complet » n'est gardé que si statut_texte vaut
« complet », et « n_mots » compte les mots de « texte ». Si le fil ne donne
pas de chapô, il est pris dans le premier paragraphe du texte complet qui ne
répète pas le titre (l'article porte alors chapo_du_texte_complet: true).
Sont écartés les articles en « echec », les doublons (même lien ou même titre
dans un lot) et, pour le lot ia, les articles de score inférieur à 2.
Un article qui touche les deux côtés figure dans les deux lots.

Usage :
    python3 lots.py
    python3 lots.py corpus/veille_2026-10-14.json
"""
import argparse
import collections
import json
import re
import sys
from pathlib import Path

from collect_rss import SORTIE

# nom du lot : (thèmes retenus, score minimal)
LOTS = {"ia": ({"ia"}, 2), "politique": ({"immigration", "religion"}, 0)}


def titre(a):
    return a["texte"].partition("\n\n")[0]


def cle_titre(a):
    return re.sub(r"\W+", " ", titre(a).lower()).strip()


def avec_chapo(a):
    """Titre + chapô ; sans chapô dans le fil, le premier paragraphe du texte complet."""
    t, _, chapo = a["texte"].partition("\n\n")
    if chapo.strip() or not a.get("texte_complet"):
        return a["texte"], False
    cle = cle_titre(a)
    for par in a["texte_complet"].split("\n"):
        if par.strip() and re.sub(r"\W+", " ", par.lower()).strip() != cle:
            return f"{t}\n\n{par.strip()}", True
    return a["texte"], False


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("fichier", nargs="?", help="corpus de veille (défaut : le dernier veille_*.json)")
    args = ap.parse_args()

    if args.fichier:
        fichier = Path(args.fichier)
    else:
        fichiers = sorted(SORTIE.glob("veille_*.json"))
        if not fichiers:
            print("Aucun fichier veille_*.json dans corpus/.")
            return 1
        fichier = fichiers[-1]
    jour = fichier.stem.removeprefix("veille_")
    articles = json.loads(fichier.read_text("utf-8"))
    print(f"{fichier.name} : {len(articles)} articles")

    echecs = [a for a in articles if a.get("statut_texte") == "echec"]
    print(f"  {len(echecs)} en echec, écartés")

    dossier = SORTIE / "lots"
    dossier.mkdir(exist_ok=True)
    for nom, (themes, score_min) in LOTS.items():
        lot, vus, doublons, faibles = [], set(), [], 0
        for a in articles:
            if a.get("statut_texte") == "echec" or not themes & set(a["themes"]):
                continue
            if a.get("score", 0) < score_min:
                faibles += 1
                continue
            cles = {("lien", a["lien"]), ("titre", cle_titre(a))}
            if cles & vus:
                doublons.append(a)
                continue
            vus |= cles
            b = {k: v for k, v in a.items() if k != "texte_complet"}
            b["texte"], emprunte = avec_chapo(a)
            if emprunte:
                b["chapo_du_texte_complet"] = True
            if a.get("statut_texte") == "complet":
                b["texte_complet"] = a["texte_complet"]
            b["n_mots"] = len(b["texte"].split())
            lot.append(b)

        sortie = dossier / f"lot_{nom}_{jour}.json"
        sortie.write_text(json.dumps(lot, ensure_ascii=False, indent=2), "utf-8")
        statuts = collections.Counter(a.get("statut_texte", "non traité") for a in lot)
        print(f"\n{sortie.relative_to(SORTIE.parent)} : {len(lot)} articles "
              f"({', '.join(f'{n} {s}' for s, n in statuts.most_common())})")
        for source, n in collections.Counter(a["source"] for a in lot).most_common():
            print(f"  {source:<40} {n:>3}")
        if faibles:
            print(f"  {faibles} article(s) de score < {score_min} écartés")
        emprunts = sum(1 for a in lot if a.get("chapo_du_texte_complet"))
        if emprunts:
            print(f"  {emprunts} chapô(s) pris dans le texte complet")
        for a in doublons:
            print(f"  doublon écarté : {a['source'][:24]} {titre(a)[:60]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
