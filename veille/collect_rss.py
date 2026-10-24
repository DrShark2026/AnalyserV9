#!/usr/bin/env python3
"""Veille RSS pour l'analyseur Grize–Charconnet.

Récupère les fils listés dans feeds.json, garde les articles qui parlent
des thèmes de mots_cles.json, et écrit un corpus du jour au format de
l'analyseur (id, source, categorie, langue, date, lien, themes, texte).
Chaque article porte aussi un score (passages repérés, ceux du titre
comptent double), dans_titre (un mot-clé figure dans le titre) et
mnemoniques_collecte (les mots de la liste « mnemoniques » trouvés, sans effet sur la
sélection). Les articles d'un fil à « texte_complet »: false portent
statut_texte « resume » : complet.py ne cherche pas leur texte. Un fil qui
porte une liste « themes » n'est cherché que pour ces thèmes ; « pays » est
recopié dans chaque article. « exclure_pres_de » écarte un mot repère du fil
quand un des mots donnés en est séparé par PROCHE mots ou moins (« lycéen »
près de « Parcoursup », « manifestation » près de « Bolsonaro » chez Europe 1). Un article
dont le titre ou le début du chapô contient « Sponsored », « Partner content »
ou « Contenu sponsorisé » porte categorie « sponsorise » : il n'entre dans
aucun lot.

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
import gzip
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
PROCHE = 8   # « près de » pour exclure_pres_de : nombre de mots au plus entre les deux


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


def motif(mot, exact_max=3):
    """Mot court (exact_max lettres ou moins) : mot exact. Sinon : début de mot, suffixes permis (migrant -> migrants)."""
    m = re.escape(sans_accents(mot))
    if len(mot) <= exact_max:
        return re.compile(r"(?<!\w)" + m + r"(?!\w)")
    return re.compile(r"(?<!\w)" + m)


ACCORD = r"(?:e?s|e|x)?"   # pluriel et féminin : réfugié -> réfugiés, réfugiée ; pas réfugier


def mot_entier(mot, exact_max=3):
    """Mot repère : mot entier, avec pluriel ou féminin sur chaque mot de plus de exact_max lettres
    (titre de séjour -> titres de séjour). « réfugié » ne prend donc pas « se réfugier »."""
    parties = []
    for p in sans_accents(mot).split(" "):
        parties.append(re.escape(p) + ("" if len(p) <= exact_max else ACCORD))
    return re.compile(r"(?<!\w)" + " ".join(parties) + r"(?!\w)")


def hors_exclusions(spans, exclusions):
    """Garde les passages qui ne tombent pas dans une expression exclue (« catholique » dans « Université catholique »)."""
    return [(d, f) for d, f in spans if not any(ed <= d and f <= ef for ed, ef in exclusions)]


def loin_de(spans, t, regles):
    """Garde les passages qui ne sont pas près d'un mot écartant (« lycéens » près de « Parcoursup »)."""
    def pres(d, f, voisins):
        return any(len(re.findall(r"\w+", t[min(f, vf):max(d, vd)])) <= PROCHE   # mots entre les deux
                   for rx_v in voisins for vd, vf in (m.span() for m in rx_v.finditer(t)))
    return [(d, f) for d, f in spans
            if not any(rx.fullmatch(t[d:f]) and pres(d, f, voisins) for rx, voisins in regles)]


def occurrences(spans):
    """Nombre de passages repérés, en fusionnant les chevauchements (migrant / migrants, deport / deportation)."""
    n, fin = 0, -1
    for debut, f in sorted(spans):
        if debut >= fin:
            n += 1
        fin = max(fin, f)
    return n


# « partner content » et « contenu sponsorisé » ne servent qu'à étiqueter ; « sponsored » seulement en
# étiquette (en tête, suivi de « : », « | », « ] », « ) » ou précédé de « | », « [ », « ( »),
# pas dans « a bill sponsored by » ni « sponsored access »
SPONSOR = re.compile(r"(?<!\w)(?:partner content|contenu sponsorise)(?!\w)"
                     r"|^\W*sponsored(?!\w)|(?<!\w)sponsored\s*[:|\])]|[|\[(]\s*sponsored(?!\w)")
DEBUT_RESUME = 300   # « début du texte » : les premiers caractères du chapô


def sponsorise(titre_norm, resume_norm):
    """Vrai si le titre ou le début du chapô (déjà sans accents ni majuscules) annonce un contenu sponsorisé."""
    return bool(SPONSOR.search(titre_norm) or SPONSOR.search(resume_norm[:DEBUT_RESUME]))


# ---------- lecture des fils ----------

def lire_reponse(r):
    """Corps de la réponse ; certains serveurs (DeepMind) l'envoient en gzip sans qu'on le demande."""
    brut = r.read()
    if r.headers.get("Content-Encoding", "").lower() == "gzip":
        brut = gzip.decompress(brut)
    return brut


def telecharger(url, timeout=20):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return lire_reponse(r)


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
    """Renvoie une liste de dicts {titre, lien, date, resume, auteur} pour RSS 2.0 ou Atom."""
    racine = ET.fromstring(octets)
    items = [e for e in racine.iter() if local(e.tag) in ("item", "entry")]
    articles = []
    for it in items:
        articles.append({
            "titre": nettoyer_html(texte_de(it, "title")),
            "lien": texte_de(it, "link", "guid", "id"),
            "date": date_iso(texte_de(it, "pubDate", "published", "updated", "date")),
            "resume": nettoyer_html(texte_de(it, "description", "summary", "encoded", "content")),
            "auteur": texte_de(it, "creator", "author"),
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
    mots_cles = json.loads((ICI / "mots_cles.json").read_text("utf-8"))
    mnemo = {lg: [(m, motif(m, exact_max=4)) for m in mots] for lg, mots in mots_cles.get("mnemoniques", {}).items()}
    themes = {k: v for k, v in mots_cles.items() if not k.startswith("_") and k != "mnemoniques"}
    motifs = {th: {lg: [(m, mot_entier(m)) for m in mots] for lg, mots in langs.items()} for th, langs in themes.items()}
    exclusions = {th: [mot_entier(e) for e in exprs] for th, exprs in mots_cles.get("_exclusions", {}).items()}

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
        pres_de = [(mot_entier(m), [mot_entier(v) for v in voisins]) for m, voisins in f.get("exclure_pres_de", {}).items()]
        for a in articles:
            if not a["lien"] or not a["titre"]:
                continue
            if a["auteur"] in f.get("exclure_auteurs", []):
                continue
            if limite and a["date"] and a["date"] < limite:
                continue
            cle = hashlib.sha1(a["lien"].encode()).hexdigest()[:16]
            if cle in registre:
                continue
            if sans_accents(a["resume"]) == sans_accents(a["titre"]):
                a["resume"] = ""     # fil sans chapô qui répète le titre (Anthropic) : il compterait deux fois
            titre_norm, resume_norm = sans_accents(a["titre"]), sans_accents(a["resume"])
            trouves, mots, zones = [], [], {"titre": [], "resume": []}
            for th, langs in motifs.items():
                if "themes" in f and th not in f["themes"]:
                    continue     # thème que ce fil ne cherche pas (fils hors de France : pas d'analogies historiques)
                for mot, rx in langs.get(f["langue"], []):
                    trouve = False
                    for zone, t in (("titre", titre_norm), ("resume", resume_norm)):
                        exclus = [e.span() for rx_e in exclusions.get(th, []) for e in rx_e.finditer(t)]
                        spans = loin_de(hors_exclusions([m.span() for m in rx.finditer(t)], exclus), t, pres_de)
                        zones[zone] += spans
                        trouve = trouve or bool(spans)
                    if trouve:
                        trouves.append(th)
                        mots.append(mot)
            n_titre, n_resume = occurrences(zones["titre"]), occurrences(zones["resume"])
            par_defaut = not trouves and bool(f.get("theme_defaut"))
            if par_defaut:
                trouves.append(f["theme_defaut"])
            if not trouves and not args.tous:
                continue
            mnemoniques = sorted(m for m, rx in mnemo.get(f["langue"], []) if rx.search(titre_norm) or rx.search(resume_norm))
            gardes += 1
            article = {
                "id": f"{aujourdhui.isoformat()}-{cle}",
                "source": f["nom"],
                "categorie": "sponsorise" if sponsorise(titre_norm, resume_norm) else f["categorie"],
                "pays": f.get("pays", ""),
                "orientation": f.get("orientation", ""),
                "degre": f.get("degre", ""),
                "posture_ia": f.get("posture_ia", ""),
                "langue": f["langue"],
                "date": a["date"],
                "lien": a["lien"],
                "themes": sorted(set(trouves)),
                "mots_reperes": sorted(set(mots)),
                "score": 2 * n_titre + n_resume,
                "dans_titre": n_titre > 0,
                "theme_par_defaut": par_defaut,
                "mnemoniques_collecte": mnemoniques,
                "texte": a["titre"] + ("\n\n" + a["resume"] if a["resume"] else ""),
                "verite_terrain": None,
            }
            if f.get("texte_complet") is False:
                article["statut_texte"] = "resume"     # le site refuse le texte complet : complet.py ne le cherche pas
            retenus.append(article)
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
