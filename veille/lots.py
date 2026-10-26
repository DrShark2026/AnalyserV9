#!/usr/bin/env python3
"""Lots pour l'analyseur à partir d'un corpus de veille.

Prend le dernier corpus/veille_*.json et écrit deux lots, prêts à coller
dans l'analyseur :
    corpus/lots/lot_ia_AAAA-MM-JJ.json          thème ia
    corpus/lots/lot_politique_AAAA-MM-JJ.json   thèmes immigration, religion et mouvements_sociaux

Chaque article garde ses champs ; « texte » reste le titre + chapô (c'est lui
que l'analyseur lit), « texte_complet » n'est gardé que si statut_texte vaut
« complet », « n_mots » compte les mots de « texte » et « n_mots_complet »
ceux de « texte_complet » quand il est gardé. Si le fil ne donne
pas de chapô, il est pris dans le premier paragraphe du texte complet qui ne
répète pas le titre (l'article porte alors chapo_du_texte_complet: true).
Un article en « echec » (anti-robot, robots.txt, 403, extraction vide, bandeau)
reste dans le lot avec son résumé RSS : statut_texte y vaut « resume ».
Sont écartés les doublons (même lien ou même titre
dans un lot) et les articles de score trop faible : inférieur à 2 pour le lot
ia, à 1 pour le lot politique ; dans le lot ia, les articles des sources à
posture_ia renseignée sont exemptés de ce seuil, sauf ceux qui n'ont le thème
que par défaut (theme_par_defaut: true, aucun mot repère). La règle de sélection d'un lot est dans
candidat(), que complet.py reprend : tout article qui peut entrer dans un lot
a son texte complet cherché. Chaque source garde au plus 6
articles dans le lot ia et 3 dans le lot politique (groupe témoin) : d'abord
le meilleur article de chaque thème du lot (immigration, religion,
mouvements_sociaux), pour qu'un jour de manifestations n'efface pas les deux
autres, puis les suivants par score ; à score égal, le texte complet le plus long passe devant. Les articles de categorie « sponsorise » (marqués par
collect_rss.py) et ceux marqués hors_lots (rubrique exclue du fil, comme les jeux
vidéo de Numerama) n'entrent dans aucun lot, et complet.py ne cherche pas leur texte.
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

# nom du lot : (thèmes retenus, score minimal, articles par source au plus, les mieux notés,
#               sources à posture_ia renseignée exemptées du score minimal, hors thème par défaut)
LOTS = {"ia": ({"ia"}, 2, 6, True), "politique": ({"immigration", "religion", "mouvements_sociaux"}, 1, 3, False)}


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


def candidat(a, themes, score_min, exempte_posture_ia):
    """Règle de sélection d'un lot, avant l'écart des doublons et du plafond par source."""
    if not themes & set(a["themes"]) or a.get("categorie") == "sponsorise" or a.get("hors_lots"):
        return False
    if a.get("score", 0) >= score_min:
        return True
    return exempte_posture_ia and bool(a.get("posture_ia")) and not a.get("theme_par_defaut")


def pour_un_lot(a):
    """Vrai si l'article peut entrer dans au moins un lot : complet.py cherche alors son texte."""
    return any(candidat(a, themes, score_min, exempte) for themes, score_min, _, exempte in LOTS.values())


def plafonner(bs, themes, n):
    """Les n articles gardés d'une source : le meilleur de chaque thème du lot, puis les suivants par score."""
    tries = sorted(bs, key=lambda b: (-b.get("score", 0), -b.get("n_mots_complet", 0)))
    gardes, couverts = [], set()
    for b in tries:
        if len(gardes) < n and themes & set(b["themes"]) - couverts:
            gardes.append(b)
            couverts |= set(b["themes"])
    gardes += [b for b in tries if b not in gardes][:n - len(gardes)]
    return gardes


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
    print(f"  {len(echecs)} en echec, gardés avec leur résumé RSS (statut_texte resume)")

    dossier = SORTIE / "lots"
    dossier.mkdir(exist_ok=True)
    for nom, (themes, score_min, par_source_max, exempte) in LOTS.items():
        lot, vus, doublons, faibles, sponsorises, rubriques = [], set(), [], 0, 0, 0
        for a in articles:
            if not themes & set(a["themes"]):
                continue
            if a.get("categorie") == "sponsorise":
                sponsorises += 1
                continue
            if a.get("hors_lots"):
                rubriques += 1
                continue
            if not candidat(a, themes, score_min, exempte):
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
            elif a.get("statut_texte") == "echec":
                b["statut_texte"] = "resume"     # extraction ratée : on garde le résumé RSS de « texte »
            b["n_mots"] = len(b["texte"].split())
            if "texte_complet" in b:
                b["n_mots_complet"] = len(b["texte_complet"].split())
            lot.append(b)

        par_source = collections.defaultdict(list)
        for b in lot:
            par_source[b["source"]].append(b)
        gardes = {id(b) for bs in par_source.values() for b in plafonner(bs, themes, par_source_max)}
        plafonnes = collections.Counter(b["source"] for b in lot if id(b) not in gardes)
        lot = [b for b in lot if id(b) in gardes]

        sortie = dossier / f"lot_{nom}_{jour}.json"
        sortie.write_text(json.dumps(lot, ensure_ascii=False, indent=2), "utf-8")
        statuts = collections.Counter(a.get("statut_texte", "non traité") for a in lot)
        print(f"\n{sortie.relative_to(SORTIE.parent)} : {len(lot)} articles "
              f"({', '.join(f'{n} {s}' for s, n in statuts.most_common())})")
        for source, n in collections.Counter(a["source"] for a in lot).most_common():
            print(f"  {source:<40} {n:>3}")
        if sponsorises:
            print(f"  {sponsorises} article(s) sponsorisé(s) écartés")
        if rubriques:
            print(f"  {rubriques} article(s) d'une rubrique exclue (hors_lots) écartés")
        if faibles:
            print(f"  {faibles} article(s) de score < {score_min} écartés")
        exemptes = sum(1 for a in lot if a.get("score", 0) < score_min)
        if exemptes:
            print(f"  {exemptes} article(s) de score < {score_min} gardés (source à posture_ia)")
        if plafonnes:
            print(f"  {sum(plafonnes.values())} article(s) au-delà de {par_source_max} par source écartés "
                  f"({', '.join(f'{s} {n}' for s, n in plafonnes.most_common())})")
        emprunts = sum(1 for a in lot if a.get("chapo_du_texte_complet"))
        if emprunts:
            print(f"  {emprunts} chapô(s) pris dans le texte complet")
        for a in doublons:
            print(f"  doublon écarté : {a['source'][:24]} {titre(a)[:60]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
