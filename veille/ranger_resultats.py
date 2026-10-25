#!/usr/bin/env python3
"""Range les résultats de l'analyseur dans corpus/resultats/.

Prend les fichiers resultats_batch_*.json du dossier de téléchargements et
les copie sous le nom AAAA-MM-JJ_ia.json ou AAAA-MM-JJ_politique.json :
    jour   celui du lot, lu dans l'id des articles (AAAA-MM-JJ-…, le jour de
           la collecte) ; à défaut, la date la plus fréquente des articles
    thème  ia si tous les articles ont le thème ia, politique si tous ont
           immigration, religion ou mouvements_sociaux (comme dans lots.py)
Un fichier qu'on ne sait pas classer (résultats d'un dossier, thème mêlé,
fichier illisible) est laissé de côté et signalé. S'il y a déjà un fichier
pour ce jour et ce thème, le plus récent (date de modification) est gardé et
le doublon est signalé ; la copie garde la date de modification de l'original.
Les téléchargements ne sont jamais modifiés ni supprimés.

Usage :
    python3 ranger_resultats.py
    python3 ranger_resultats.py ~/Bureau     # autre dossier de téléchargements
"""
import argparse
import collections
import json
import shutil
import sys
from pathlib import Path

from collect_rss import SORTIE
from lots import LOTS

RESULTATS = SORTIE / "resultats"


def classer(articles):
    """(jour, thème) d'un fichier de résultats, ou (None, raison) s'il ne se laisse pas classer."""
    if not isinstance(articles, list) or not articles or not all(isinstance(a, dict) for a in articles):
        return None, "pas une liste d'articles"
    jours = collections.Counter(a["id"][:10] for a in articles
                                if isinstance(a.get("id"), str) and a["id"][:4].isdigit() and a["id"][10:11] == "-")
    if not jours:
        jours = collections.Counter(a["date"] for a in articles if a.get("date"))
    if not jours:
        return None, "ni id daté ni date d'article"
    jour = jours.most_common(1)[0][0]
    themes = [set(a.get("themes") or []) for a in articles]
    for nom, (lot_themes, *_) in LOTS.items():
        if all(t & lot_themes for t in themes):
            return jour, nom
    vus = sorted(set().union(*themes))
    return None, f"thèmes hors des lots ({', '.join(vus) or 'aucun'})"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("dossier", nargs="?", default=Path.home() / "Téléchargements",
                    help="où chercher les resultats_batch_*.json (défaut : ~/Téléchargements)")
    args = ap.parse_args()

    fichiers = sorted(Path(args.dossier).expanduser().glob("resultats_batch_*.json"), key=lambda f: f.stat().st_mtime)
    if not fichiers:
        print(f"Aucun resultats_batch_*.json dans {args.dossier}.")
        return 0
    RESULTATS.mkdir(parents=True, exist_ok=True)

    copies, deja, ecartes, doublons = [], 0, [], []
    for f in fichiers:
        try:
            jour, theme = classer(json.loads(f.read_text("utf-8")))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            jour, theme = None, f"illisible ({str(e)[:60]})"
        if jour is None:
            ecartes.append((f.name, theme))
            continue
        cible = RESULTATS / f"{jour}_{theme}.json"
        if cible.exists():
            if cible.read_bytes() == f.read_bytes():
                deja += 1
                continue
            if cible.stat().st_mtime >= f.stat().st_mtime:
                doublons.append(f"{cible.name} : gardé, plus récent que {f.name}")
                continue
            doublons.append(f"{cible.name} : remplacé par {f.name}, plus récent")
        shutil.copy2(f, cible)
        copies.append((f.name, cible.name))

    print(f"{len(fichiers)} fichier(s) dans {args.dossier}")
    for src, dst in copies:
        print(f"  {src:<45} → {dst}")
    if deja:
        print(f"  {deja} fichier(s) déjà rangé(s), identiques")
    if doublons:
        print("\nPlusieurs résultats pour un même jour et un même thème :")
        for d in doublons:
            print(f"  {d}")
    if ecartes:
        print("\nLaissés de côté :")
        for nom, raison in ecartes:
            print(f"  {nom:<45} {raison}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
