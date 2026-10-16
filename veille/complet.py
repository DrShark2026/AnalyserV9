#!/usr/bin/env python3
"""Texte complet des articles retenus par la veille.

Prend le dernier corpus/veille_*.json, ouvre le lien de chaque article dont
le score est d'au moins 2, extrait le corps de l'article avec trafilatura et
ajoute deux champs :
    texte_complet  le corps de l'article (None en cas d'échec)
    statut_texte   complet | partiel | echec

Règles de politesse : robots.txt est respecté, au plus une requête toutes les
3 secondes (davantage si le site demande un Crawl-delay), et aucune tentative
de contourner un paywall ou une protection anti-robot : une page réservée
aux abonnés donne « partiel » (le début public), une page anti-robot « echec ».
Si plusieurs articles d'une même source donnent exactement le même texte,
c'est un bandeau ou une page générique, pas l'article : ils passent en « echec ».

Les articles en « echec » sont retentés à chaque passage ; les articles
« complet » ou « partiel » ne le sont qu'avec --refaire.

Usage :
    .venv/bin/python complet.py                  # dernier fichier, score >= 2
    .venv/bin/python complet.py --score 1        # seuil différent
    .venv/bin/python complet.py --refaire        # retente aussi les articles complets ou partiels
    .venv/bin/python complet.py corpus/veille_2026-10-12.json

Dépendance : trafilatura (installée dans veille/.venv).
"""
import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.request
import urllib.robotparser
from pathlib import Path
from urllib.parse import urlsplit

import trafilatura

from collect_rss import SORTIE, UA

DELAI_MIN = 3.0          # secondes entre deux requêtes, tous sites confondus
MOTS_COMPLET = 150       # en dessous, le texte extrait est jugé partiel
MOTS_ECHEC = 30          # en dessous, l'extraction est jugée ratée

# Signes qu'une page est réservée aux abonnés : on les constate, on ne les contourne pas.
PAYWALL_JSONLD = re.compile(r'"isAccessibleForFree"\s*:\s*"?false"?', re.I)
PAYWALL_TEXTE = re.compile(
    r"réservé aux abonnés|article réservé|il vous reste \d+ ?% de cet article|abonnez-vous pour lire"
    r"|subscribe to continue|subscribers only|already a subscriber", re.I)

# Page de protection anti-robot servie à la place de l'article : échec, sans tentative de la franchir.
ANTI_ROBOT = re.compile(r"please enable javascript to proceed|javascript is disabled in your browser"
                        r"|verify you are human|captcha-delivery\.com", re.I)

_derniere = 0.0
_robots = {}


def attendre(delai=DELAI_MIN):
    global _derniere
    reste = _derniere + delai - time.monotonic()
    if reste > 0:
        time.sleep(reste)
    _derniere = time.monotonic()


def telecharger(url, delai=DELAI_MIN, timeout=20):
    attendre(delai)
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "fr,en;q=0.8"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        brut = r.read()
        return brut.decode(r.headers.get_content_charset() or "utf-8", errors="replace")


def robots_pour(url):
    """robots.txt du site, lu une fois par site. 401/403 : tout interdit ; absent : tout permis."""
    p = urlsplit(url)
    site = f"{p.scheme}://{p.netloc}"
    if site not in _robots:
        rp = urllib.robotparser.RobotFileParser()
        try:
            rp.parse(telecharger(site + "/robots.txt").splitlines())
        except urllib.error.HTTPError as e:
            if e.code in (401, 403):
                rp.disallow_all = True
            else:
                rp.allow_all = True
        except Exception:
            rp.allow_all = True
        _robots[site] = rp
    return _robots[site]


def traiter(article):
    """Renvoie (texte_complet, statut, raison)."""
    url = article["lien"]
    rp = robots_pour(url)
    if not rp.can_fetch(UA, url):
        return None, "echec", "interdit par robots.txt"
    delai = max(DELAI_MIN, float(rp.crawl_delay(UA) or 0))
    try:
        page = telecharger(url, delai)
    except urllib.error.HTTPError as e:
        return None, "echec", f"HTTP {e.code}"
    except Exception as e:
        return None, "echec", str(e)[:80]

    texte = trafilatura.extract(page, url=url, include_comments=False, include_tables=False)
    n = len(texte.split()) if texte else 0
    if ANTI_ROBOT.search(texte or "") or (n < MOTS_ECHEC and ANTI_ROBOT.search(page)):
        return None, "echec", "page anti-robot à la place de l'article"
    if n < MOTS_ECHEC:
        return None, "echec", f"extraction vide ({n} mots)"
    if PAYWALL_JSONLD.search(page) or PAYWALL_TEXTE.search(texte):
        return texte, "partiel", f"réservé aux abonnés ({n} mots publics)"
    if n < MOTS_COMPLET:
        return texte, "partiel", f"texte court ({n} mots)"
    return texte, "complet", f"{n} mots"


def bandeaux(articles):
    """Articles d'une même source au texte identique : c'est un bandeau, pas l'article. Les passe en echec."""
    groupes = {}
    for a in articles:
        if a.get("texte_complet"):
            cle = (a["source"], " ".join(a["texte_complet"].split()))
            groupes.setdefault(cle, []).append(a)
    touches = [a for g in groupes.values() if len(g) > 1 for a in g]
    for a in touches:
        a["texte_complet"] = None
        a["statut_texte"] = "echec"
    return touches


def ecrire(fichier, articles):
    tmp = fichier.with_suffix(".tmp")
    tmp.write_text(json.dumps(articles, ensure_ascii=False, indent=2), "utf-8")
    tmp.replace(fichier)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("fichier", nargs="?", help="corpus à compléter (défaut : le dernier veille_*.json)")
    ap.add_argument("--score", type=int, default=2, help="score minimal (défaut : 2)")
    ap.add_argument("--refaire", action="store_true", help="retenter aussi les articles complets ou partiels")
    args = ap.parse_args()

    if args.fichier:
        fichier = Path(args.fichier)
    else:
        fichiers = sorted(SORTIE.glob("veille_*.json"))
        if not fichiers:
            print("Aucun fichier veille_*.json dans corpus/.")
            return 1
        fichier = fichiers[-1]

    articles = json.loads(fichier.read_text("utf-8"))
    print(f"{fichier.name} : {len(articles)} articles\n")
    traites = 0
    for a in articles:
        titre = a["texte"].partition("\n\n")[0][:70]
        if a.get("score", 0) < args.score:
            continue
        if a.get("statut_texte") in ("complet", "partiel") and not args.refaire:
            print(f"  {'déjà fait':<9} {a['source'][:24]:<24} {titre}")
            continue
        texte, statut, raison = traiter(a)
        a["texte_complet"] = texte
        a["statut_texte"] = statut
        traites += 1
        print(f"  {statut:<9} {a['source'][:24]:<24} {titre}\n  {'':<9} → {raison}")
        # écrit après chaque article : une interruption ne fait rien perdre
        ecrire(fichier, articles)

    doublons = bandeaux(articles)
    if doublons:
        ecrire(fichier, articles)
        print(f"\nTexte identique dans une même source (bandeau, pas l'article) → echec :")
        for a in doublons:
            print(f"  {a['source'][:24]:<24} {a['texte'].partition(chr(10) * 2)[0][:70]}")

    print(f"\n{traites} article(s) traité(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
