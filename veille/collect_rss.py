#!/usr/bin/env python3
"""Veille RSS pour l'analyseur Grize–Charconnet.

Récupère les fils listés dans feeds.json, garde les articles qui parlent
des thèmes de mots_cles.json, et écrit un corpus du jour au format de
l'analyseur (id, source, categorie, langue, date, lien, themes, texte).

Usage :
    python3 collect_rss.py                 # collecte normale
    python3 collect_rss.py --jours 3       # seulement les articles des 3 derniers jours
    python3 collect_rss.py --tous          # sans filtre de mots-clés
    python3 collect_rss.py --test          # vérifie que chaque fil répond, sans rien écrire

Aucune dépendance : uniquement la bibliothèque standard de Python.
"""
import argparse
import datetime as dt
import email.utils
import hashlib
import html
import json
import re
import sys
import unicodedata
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ICI = Path(__file__).resolve().parent
SORTIE = ICI / "corpus"
REGISTRE = ICI / "registre.json"
UA = "Mozilla/5.0 (veille-analyseur-grize; usage de recherche)"


# ---------- utilitaires ----------

def sans_accents(t):
    t = unicodedata.normalize("NFD", t)
    return "".join(c for c in t if unicodedata.category(c) != "Mn").lower()


def nettoyer_html(t):
    t = re.sub(r"<[^>]+>", " ", t or "")
    t = html.unescape(t)
    t = re.sub(r"\s+", " ", t)
    t = re.sub(r"\s+([.,)])", r"\1", t)       # pas d'espace avant point, virgule, parenthèse (laissé par les balises)
    t = re.sub(r"(['’(])\s+", r"\1", t)       # ni après une apostrophe
    return t.strip()


def date_iso(brut):
    """Convertit une date RSS (RFC 822) ou Atom (ISO 8601) en AAAA-MM-JJ."""
    if not brut:
        return None
    brut = brut.strip()
    try:
        return email.utils.parsedate_to_datetime(brut).date().isoformat()
    except Exception:
        pass
    try:
        return dt.datetime.fromisoformat(brut.replace("Z", "+00:00")).date().isoformat()
    except Exception:
        return None


def motif(mot):
    """Mot court (3 lettres ou moins) : mot exact. Sinon : début de mot, suffixes permis (migrant -> migrants)."""
    m = re.escape(sans_accents(mot))
    if len(mot) <= 3:
        return re.compile(r"(?<!\w)" + m + r"(?!\w)")
    return re.compile(r"(?<!\w)" + m)


# ---------- lecture des fils ----------

def telecharger(url, timeout=20):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def local(tag):
    return tag.split("}", 1)[-1] if "}" in tag else tag


def enfant(el, nom):
    for c in el:
        if local(c.tag) == nom:
            return c
    return None


def texte_de(el, *noms):
    for n in noms:
        c = enfant(el, n)
        if c is not None:
            if n == "link" and c.get("href"):
                return c.get("href")
            if (c.text or "").strip():
                return c.text.strip()
    return ""


def lire_fil(octets):
    """Renvoie une liste de dicts {titre, lien, date, resume} pour RSS 2.0 ou Atom."""
    racine = ET.fromstring(octets)
    items = [e for e in racine.iter() if local(e.tag) in ("item", "entry")]
    articles = []
    for it in items:
        articles.append({
            "titre": nettoyer_html(texte_de(it, "title")),
            "lien": texte_de(it, "link", "guid", "id"),
            "date": date_iso(texte_de(it, "pubDate", "published", "updated", "date")),
            "resume": nettoyer_html(texte_de(it, "description", "summary", "encoded", "content")),
        })
    return articles


# ---------- programme principal ----------

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--jours", type=int, default=None, help="ne garder que les articles des N derniers jours")
    ap.add_argument("--tous", action="store_true", help="ne pas filtrer par mots-clés")
    ap.add_argument("--test", action="store_true", help="tester les fils sans rien écrire")
    args = ap.parse_args()

    feeds = [f for f in json.loads((ICI / "feeds.json").read_text("utf-8"))["feeds"] if f.get("actif", True)]
    themes = {k: v for k, v in json.loads((ICI / "mots_cles.json").read_text("utf-8")).items() if not k.startswith("_")}
    motifs = {th: {lg: [(m, motif(m)) for m in mots] for lg, mots in langs.items()} for th, langs in themes.items()}

    registre = json.loads(REGISTRE.read_text("utf-8")) if REGISTRE.exists() else {}
    aujourdhui = dt.date.today()
    limite = (aujourdhui - dt.timedelta(days=args.jours)).isoformat() if args.jours else None

    retenus, echecs, bilan = [], [], []
    for f in feeds:
        try:
            articles = lire_fil(telecharger(f["url"]))
        except Exception as e:
            echecs.append((f["nom"], str(e)[:120]))
            continue
        gardes = 0
        for a in articles:
            if not a["lien"] or not a["titre"]:
                continue
            if limite and a["date"] and a["date"] < limite:
                continue
            cle = hashlib.sha1(a["lien"].encode()).hexdigest()[:16]
            if cle in registre:
                continue
            texte_norm = sans_accents(a["titre"] + " " + a["resume"])
            trouves, mots = [], []
            for th, langs in motifs.items():
                for mot, rx in langs.get(f["langue"], []):
                    if rx.search(texte_norm):
                        trouves.append(th)
                        mots.append(mot)
            if not trouves and not args.tous:
                continue
            gardes += 1
            retenus.append({
                "id": f"{aujourdhui.isoformat()}-{cle}",
                "source": f["nom"],
                "categorie": f["categorie"],
                "orientation": f.get("orientation", ""),
                "langue": f["langue"],
                "date": a["date"],
                "lien": a["lien"],
                "themes": sorted(set(trouves)),
                "mots_reperes": sorted(set(mots)),
                "texte": a["titre"] + ("\n\n" + a["resume"] if a["resume"] else ""),
                "verite_terrain": None,
            })
            registre[cle] = {"lien": a["lien"], "vu_le": aujourdhui.isoformat()}
        bilan.append((f["nom"], len(articles), gardes))

    print("\nFils lus :")
    for nom, n, g in bilan:
        print(f"  {nom:<40} {n:>4} articles, {g:>3} retenus")
    if echecs:
        print("\nFils en échec (adresse à vérifier dans feeds.json) :")
        for nom, err in echecs:
            print(f"  {nom:<40} {err}")

    if args.test:
        print("\nMode test : rien n'a été écrit.")
        return 0
    if not retenus:
        print("\nAucun nouvel article retenu aujourd'hui.")
        return 0

    SORTIE.mkdir(exist_ok=True)
    fichier = SORTIE / f"veille_{aujourdhui.isoformat()}.json"
    anciens = json.loads(fichier.read_text("utf-8")) if fichier.exists() else []
    fichier.write_text(json.dumps(anciens + retenus, ensure_ascii=False, indent=2), "utf-8")
    REGISTRE.write_text(json.dumps(registre, ensure_ascii=False, indent=1), "utf-8")
    print(f"\n{len(retenus)} nouveaux articles écrits dans {fichier.relative_to(ICI)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
