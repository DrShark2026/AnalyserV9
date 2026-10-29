#!/usr/bin/env python3
"""Dossier : collecte rétrospective sur un sujet, séparée de la veille quotidienne.

Interroge Google Actualités (news.google.com/rss/search) pour chaque requête,
entre guillemets (une requête qui en contient déjà, comme "sentience" IA, part
telle quelle), dans les éditions France (fr, FR), Canada (fr-CA, CA),
Belgique (fr, BE) et États-Unis (en-US, US), ou celles de --editions, par tranches de 7 jours sur les
N jours qui finissent aujourd'hui ou à --jusqu-au (opérateurs after:/before:,
after: la veille du premier jour, before: le lendemain du dernier) ; une tranche
qui atteint le plafond de 100 résultats de Google est refaite jour par jour. Les liens
news.google.com/rss/articles/… sont résolus vers l'URL de l'éditeur. Les
articles groupés dans la description d'un résultat (grappe) sont repris aussi :
faute de date propre, ils portent celle du résultat et date_de_la_grappe: true.
Doublons écartés par URL finale (sans fragment ni paramètres de suivi) et par
titre ; un doublon ajoute ses requêtes au champ « requetes » de l'article gardé.
« langue » est celle de l'édition où l'article a été trouvé en premier. Les liens
déjà résolus sont gardés dans liens.json : une nouvelle collecte ne les redemande pas.
Google ne rend pas toujours les mêmes résultats : avec --garder, les articles de la
liste précédente que la nouvelle collecte ne retrouve pas restent dans le lot, avec
absent_depuis (date et heure de la première collecte où ils ont manqué).

Une source déjà dans feeds.json (même domaine, ou même nom avant « – ») donne
pays, categorie, orientation, degre et posture_ia, quand tous ses fils sont
d'accord ; sinon ces champs restent vides.

Deux étapes, pour voir le décompte avant d'ouvrir les articles :
    1. (par défaut) liste des articles et décompte par semaine, sans texte complet ;
    2. --textes : texte complet avec l'extracteur de complet.py (robots.txt,
       une requête toutes les 3 secondes au plus). Un échec ou une page réservée
       aux abonnés donne statut_texte « resume » ; le chapô vient du texte
       complet comme dans lots.py (Google Actualités n'en donne pas). Les textes
       bruts sont gardés dans textes.json : une interruption ne fait rien perdre.

Sortie, dans corpus/dossiers/<nom>/ :
    lot_<nom>.json   même format que les lots
    comptage.csv     date, source, pays
    meta.json        date et heure de collecte, requêtes exactes, tranches, résultats par requête

Usage :
    python3 dossier.py orelien "Thélyson Orélien" "Thelyson Orelien"
    python3 dossier.py orelien "Thélyson Orélien" --jours 30
    python3 dossier.py orelien "Thélyson Orélien" --jusqu-au 2026-10-22 --remplacer --garder
    python3 dossier.py conscience_ia '"conscience" "intelligence artificielle"' "AI consciousness" --editions fr en
    .venv/bin/python dossier.py orelien --textes
"""
import argparse
import base64
import collections
import csv
import datetime as dt
import hashlib
import html
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

from collect_rss import ICI, SORTIE, UA, date_iso, lire_reponse, mot_entier, motif, nettoyer_html, sans_accents
from lots import avec_chapo

EDITIONS = {"fr": {"hl": "fr", "gl": "FR", "ceid": "FR:fr"},
            "fr-CA": {"hl": "fr-CA", "gl": "CA", "ceid": "CA:fr"},
            "fr-BE": {"hl": "fr", "gl": "BE", "ceid": "BE:fr"},
            "en": {"hl": "en-US", "gl": "US", "ceid": "US:en"}}
TRANCHE = 7              # jours par requête
PLAFOND = 100            # Google Actualités ne rend pas plus de 100 résultats : la tranche est alors refaite jour par jour
DELAI_GOOGLE = 2.0       # secondes entre deux requêtes à Google
SUIVI = re.compile(r"^(utm_|at_|xtor$|oc$|fbclid$|gclid$)")

_derniere = 0.0


def google(url, corps=None):
    global _derniere
    reste = _derniere + DELAI_GOOGLE - time.monotonic()
    if reste > 0:
        time.sleep(reste)
    _derniere = time.monotonic()
    entetes = {"User-Agent": UA}
    if corps is not None:
        entetes["Content-Type"] = "application/x-www-form-urlencoded;charset=UTF-8"
    req = urllib.request.Request(url, data=corps, headers=entetes)
    for essai in range(2):
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                return lire_reponse(r).decode("utf-8", errors="replace")
        except urllib.error.HTTPError as e:
            if e.code != 429:
                raise
            if essai:
                raise SystemExit("Google répond 429 (trop de requêtes) deux fois de suite : arrêt, le lot n'est pas réécrit (liens.json garde les liens déjà résolus).")
            print("    429 de Google : pause de 120 secondes")
            time.sleep(120)


def resoudre(lien):
    """URL de l'éditeur derrière un lien news.google.com/rss/articles/<id>, ou None.
    Anciens identifiants : l'URL est dans l'id (base64). Nouveaux (AU_yqL…) : la page de l'article
    donne une signature et un horodatage, que l'appel batchexecute échange contre l'URL."""
    gid = urllib.parse.urlsplit(lien).path.rsplit("/", 1)[-1]
    brut = base64.urlsafe_b64decode(gid + "=" * (-len(gid) % 4))
    if b"AU_yqL" not in brut[:12]:      # l'en-tête fait 4 ou 5 octets selon la longueur de l'id
        m = re.search(rb"https?://[\x21-\x7e]+", brut)
        if m:
            return m.group().decode()
    page = google(f"https://news.google.com/rss/articles/{gid}")
    sg, ts = re.search(r'data-n-a-sg="([^"]+)"', page), re.search(r'data-n-a-ts="([^"]+)"', page)
    if not (sg and ts):
        return None
    req = ["Fbv4je", f'["garturlreq",[["X","X",["X","X"],null,null,1,1,"US:en",null,1,null,null,null,null,null,0,1],'
                     f'"X","X",1,[1,1,1],1,1,null,0,0,null,0],"{gid}",{ts.group(1)},"{sg.group(1)}"]']
    rep = google("https://news.google.com/_/DotsSplashUi/data/batchexecute",
                 ("f.req=" + urllib.parse.quote(json.dumps([[req]]))).encode())
    url = json.loads(json.loads(rep.split("\n\n", 1)[1])[0][2])[1]
    return url if url.startswith("http") else None


def normaliser(url):
    p = urllib.parse.urlsplit(url)
    hote = p.netloc.lower().removeprefix("www.")
    requete = urllib.parse.urlencode([(k, v) for k, v in urllib.parse.parse_qsl(p.query) if not SUIVI.match(k)])
    return urllib.parse.urlunsplit(("https", hote, p.path.rstrip("/"), requete, ""))


def domaine(url):
    """Domaine enregistré, grossièrement : lemonde.fr, bbc.co.uk."""
    parties = urllib.parse.urlsplit(url).netloc.lower().split(":")[0].split(".")
    n = 3 if len(parties) >= 3 and len(parties[-1]) == 2 and parties[-2] in ("co", "com", "org", "gouv", "qc") else 2
    return ".".join(parties[-n:])


def cle_titre(t):
    return re.sub(r"\W+", " ", sans_accents(t)).strip()


def fiche_source(nom, url, feeds):
    """Champs de la source tirés de feeds.json : ceux sur lesquels tous ses fils sont d'accord."""
    fils = [f for f in feeds if domaine(f["url"]) == domaine(url)
            or sans_accents(f["nom"].split(" – ")[0]) == sans_accents(nom)]
    champs = {}
    for k in ("categorie", "pays", "orientation", "degre", "posture_ia"):
        valeurs = {f.get(k, "") for f in fils}
        champs[k] = valeurs.pop() if len(valeurs) == 1 else ""
    return champs, [f["nom"] for f in fils]


def resultats(xml_txt):
    """Résultats d'une recherche : (titre, lien, date, source, url de la source, grappe)."""
    for it in ET.fromstring(xml_txt).iter("item"):
        src = it.find("source")
        nom = (src.text or "").strip() if src is not None else ""
        titre = nettoyer_html(it.findtext("title") or "").removesuffix(f" - {nom}")
        desc = html.unescape(it.findtext("description") or "")
        grappe = [(nettoyer_html(t), lien, nettoyer_html(s)) for lien, t, s in
                  re.findall(r'<li><a href="([^"]+)"[^>]*>(.*?)</a>\s*<font[^>]*>(.*?)</font>', desc)]
        yield titre, it.findtext("link"), date_iso(it.findtext("pubDate") or ""), nom, \
            src.get("url", "") if src is not None else "", grappe


def termes(requete):
    """Motifs des termes d'une requête : ses passages entre guillemets et ses mots hors guillemets,
    ou la requête entière si elle n'a pas de guillemets."""
    if '"' not in requete:
        return [mot_entier(requete)]
    return [mot_entier(g or m) for g, m in re.findall(r'"([^"]+)"|([^\s"]+)', requete)]


def dans(rxs, titre_n):
    """Nombre de fois où le titre contient la requête : le moins présent de ses termes."""
    return min(len(rx.findall(titre_n)) for rx in rxs)


def collecter(nom, requetes, jours, jusqu_au, liens_f, editions):
    feeds = json.loads((ICI / "feeds.json").read_text("utf-8"))["feeds"]
    mots_cles = json.loads((ICI / "mots_cles.json").read_text("utf-8"))
    mnemo = {lg: [(m, motif(m, exact_max=4)) for m in ms] for lg, ms in mots_cles.get("mnemoniques", {}).items()}
    rx_req = [(r, termes(r)) for r in requetes]

    maintenant = dt.datetime.now().astimezone()
    fin = (jusqu_au or maintenant.date()) + dt.timedelta(days=1)          # exclu
    debut = fin - dt.timedelta(days=jours)
    tranches = []
    d = debut
    while d < fin:
        tranches.append((d, min(d + dt.timedelta(days=TRANCHE), fin)))
        d += dt.timedelta(days=TRANCHE)

    articles, par_url, par_titre, journal = [], {}, {}, []
    resolus = json.loads(liens_f.read_text("utf-8")) if liens_f.exists() else {}
    deja = len(resolus)

    def ajouter(titre, lien_g, date, source, url_source, provenance, langue, grappe_de=None):
        cle_t = (sans_accents(source), cle_titre(titre))
        if cle_t in par_titre:
            a = par_titre[cle_t]
        else:
            gid = urllib.parse.urlsplit(lien_g).path.rsplit("/", 1)[-1]
            if gid not in resolus:
                try:
                    resolus[gid] = resoudre(lien_g)
                except Exception as e:
                    print(f"    lien non résolu ({str(e)[:60]}) : {source[:24]} {titre[:50]}")
                    resolus[gid] = None
                if (len(resolus) - deja) % 50 == 0:
                    print(f"    {len(resolus) - deja} nouveaux liens Google résolus ou tentés")
                    ecrire_json(liens_f, {g: u for g, u in resolus.items() if u})
            final = resolus[gid]
            a = par_url.get(normaliser(final)) if final else None
            if a is None:
                lien = final or lien_g
                champs, connus = fiche_source(source, final or url_source, feeds)
                titre_n = sans_accents(titre)
                n_titre = sum(dans(rxs, titre_n) for _, rxs in rx_req)
                a = {
                    "id": f"{nom}-{hashlib.sha1(lien.encode()).hexdigest()[:16]}",
                    "source": source,
                    "categorie": champs["categorie"],
                    "pays": champs["pays"],
                    "orientation": champs["orientation"],
                    "degre": champs["degre"],
                    "posture_ia": champs["posture_ia"],
                    "langue": langue,
                    "date": date,
                    "lien": lien,
                    "themes": [nom],
                    "mots_reperes": sorted(r for r, rxs in rx_req if dans(rxs, titre_n)),
                    "score": 2 * n_titre,
                    "dans_titre": n_titre > 0,
                    "theme_par_defaut": False,
                    "mnemoniques_collecte": sorted(m for m, rx in mnemo.get(langue, []) if rx.search(titre_n)),
                    "texte": titre,
                    "verite_terrain": None,
                    "lien_google": lien_g,
                    "lien_resolu": final is not None,
                    "sources_connues": connus,
                    "requetes": [],
                }
                if grappe_de:
                    a["date_de_la_grappe"] = True
                articles.append(a)
                if final:
                    par_url[normaliser(final)] = a
            par_titre[cle_t] = a
        if a.get("date_de_la_grappe") and not grappe_de:
            a["date"] = date
            del a["date_de_la_grappe"]
        if provenance not in a["requetes"]:
            a["requetes"].append(provenance)

    def rechercher():
        for requete in requetes:
            for langue, ed in editions.items():
                a_faire = list(tranches)
                while a_faire:
                    d0, d1 = a_faire.pop(0)
                    q = (requete if '"' in requete else f'"{requete}"') + f' after:{d0 - dt.timedelta(days=1)} before:{d1}'
                    url = "https://news.google.com/rss/search?" + urllib.parse.urlencode({"q": q, **ed})
                    items = list(resultats(google(url)))
                    n_grappe = sum(len(g) for *_, g in items)
                    redecoupe = len(items) >= PLAFOND and (d1 - d0).days > 1
                    journal.append({"requete": requete, "q": q, "edition": langue, **ed,
                                    "tranche": [d0.isoformat(), (d1 - dt.timedelta(days=1)).isoformat()],
                                    "url": url, "n_resultats": len(items), "n_dans_grappes": n_grappe,
                                    "plafond_atteint": len(items) >= PLAFOND, "refaite_par_jour": redecoupe})
                    print(f"  {langue} {d0} → {d1 - dt.timedelta(days=1)}  {requete:<20} {len(items):>3} résultats"
                          + (f" (+{n_grappe} en grappe)" if n_grappe else "")
                          + ("  → refaite jour par jour" if redecoupe else
                             "  ⚠ plafond de 100 atteint sur un jour" if len(items) >= PLAFOND else ""))
                    if redecoupe:
                        a_faire[:0] = [(d0 + dt.timedelta(days=i), d0 + dt.timedelta(days=i + 1)) for i in range((d1 - d0).days)]
                        continue      # les résultats de la semaine sont repris par ceux des jours
                    for titre, lien_g, date, source, url_source, grappe in items:
                        ajouter(titre, lien_g, date, source, url_source, q + f" [{langue}]", langue.split("-")[0])
                        for t, l, s in grappe:
                            if (sans_accents(s), cle_titre(t)) != (sans_accents(source), cle_titre(titre)):
                                ajouter(t, l, date, s, "", q + f" [{langue}, grappe]", langue.split("-")[0], grappe_de=lien_g)

    try:
        rechercher()
    finally:
        ecrire_json(liens_f, {g: u for g, u in resolus.items() if u})     # un échec sera retenté

    articles.sort(key=lambda a: (a["date"] or "", a["source"]))
    meta = {
        "dossier": nom,
        "collecte": maintenant.isoformat(timespec="seconds"),
        "requetes": requetes,
        "jours": jours,
        "jusqu_au": (fin - dt.timedelta(days=1)).isoformat(),
        "editions": editions,
        "tranches": [[d0.isoformat(), (d1 - dt.timedelta(days=1)).isoformat()] for d0, d1 in tranches],
        "recherches": journal,
        "n_articles": len(articles),
        "n_plafond_jour": sum(1 for j in journal if j["plafond_atteint"] and not j["refaite_par_jour"]),
        "n_liens_non_resolus": sum(1 for a in articles if not a["lien_resolu"]),
    }
    return articles, meta, tranches


def ecrire_json(fichier, donnees):
    tmp = fichier.with_suffix(".tmp")
    tmp.write_text(json.dumps(donnees, ensure_ascii=False, indent=2), "utf-8")
    tmp.replace(fichier)


def ecrire_comptage(fichier, articles):
    with fichier.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["date", "source", "pays"])
        for a in sorted(articles, key=lambda a: (a["date"] or "", a["source"])):
            w.writerow([a["date"] or "", a["source"], a["pays"]])


def par_semaine(articles, tranches):
    print("\nArticles par semaine (date de l'article) :")
    for d0, d1 in tranches:
        n = sum(1 for a in articles if a["date"] and d0.isoformat() <= a["date"] < d1.isoformat())
        print(f"  {d0} → {d1 - dt.timedelta(days=1)}  {n:>4}  {'█' * n}")
    hors = [a for a in articles if not a["date"] or a["date"] < tranches[0][0].isoformat()
            or a["date"] >= tranches[-1][1].isoformat()]
    if hors:
        print(f"  hors des tranches ou sans date : {len(hors)}")
    approx = sum(1 for a in articles if a.get("date_de_la_grappe"))
    if approx:
        print(f"  dont {approx} daté(s) par leur grappe")


def garder_precedents(articles, ancien, collecte):
    """Ajoute aux articles ceux de la liste précédente qu'ils ne contiennent pas (même id, même URL
    ou même titre dans la même source), avec absent_depuis : la collecte où ils ont manqué la première fois."""
    ids = {a["id"] for a in articles}
    urls = {normaliser(a["lien"]) for a in articles}
    titres = {(sans_accents(a["source"]), cle_titre(a["texte"].partition("\n\n")[0])) for a in articles}
    gardes = []
    for a in ancien:
        if a["id"] in ids or normaliser(a["lien"]) in urls \
                or (sans_accents(a["source"]), cle_titre(a["texte"].partition("\n\n")[0])) in titres:
            continue
        a.setdefault("absent_depuis", collecte)
        gardes.append(a)
    articles.extend(gardes)
    return gardes


def textes(dossier, nom):
    import complet     # trafilatura : seulement pour cette étape

    fichier, cache_f = dossier / f"lot_{nom}.json", dossier / "textes.json"
    articles = json.loads(fichier.read_text("utf-8"))
    cache = json.loads(cache_f.read_text("utf-8")) if cache_f.exists() else {}
    for a in articles:
        if a["id"] in cache:
            continue
        if not a["lien_resolu"]:
            cache[a["id"]] = {"texte_complet": None, "statut": "echec", "raison": "lien Google non résolu", "passager": False}
        else:
            texte, statut, raison, passager = complet.traiter(a)
            cache[a["id"]] = {"texte_complet": texte, "statut": statut, "raison": raison, "passager": passager}
        print(f"  {cache[a['id']]['statut']:<9} {a['source'][:24]:<24} {a['texte'].partition(chr(10))[0][:60]}\n"
              f"  {'':<9} → {cache[a['id']]['raison']}")
        ecrire_json(cache_f, cache)

    for a in articles:
        c = cache[a["id"]]
        a["texte_complet"] = c["texte_complet"]
        a["statut_texte"] = c["statut"]
    bandeaux = complet.bandeaux(articles)
    sponsorises = complet.sponsorises(articles)
    lot = []
    for a in articles:
        if a["categorie"] == "sponsorise":
            continue
        a["texte"], emprunte = avec_chapo(a)
        if emprunte:
            a["chapo_du_texte_complet"] = True
        paywall = cache[a["id"]]["raison"].startswith("réservé aux abonnés")
        if a["statut_texte"] == "echec" or paywall:
            a["statut_texte"] = "resume"
        if a["statut_texte"] != "complet":
            del a["texte_complet"]
        a.pop("echec_passager", None)
        a["n_mots"] = len(a["texte"].split())
        if "texte_complet" in a:
            a["n_mots_complet"] = len(a["texte_complet"].split())
        lot.append(a)
    ecrire_json(fichier, lot)
    ecrire_comptage(dossier / "comptage.csv", lot)

    meta = json.loads((dossier / "meta.json").read_text("utf-8"))
    meta["textes"] = {
        "date": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        "statuts": dict(collections.Counter(a["statut_texte"] for a in lot)),
        "bandeaux": [a["id"] for a in bandeaux],
        "sponsorises_ecartes": [a["id"] for a in sponsorises],
        "raisons": {i: c["raison"] for i, c in cache.items()},
    }
    meta["n_articles"] = len(lot)
    ecrire_json(dossier / "meta.json", meta)
    print(f"\n{fichier.relative_to(SORTIE.parent)} : {len(lot)} articles "
          f"({', '.join(f'{n} {s}' for s, n in collections.Counter(a['statut_texte'] for a in lot).most_common())})")
    if bandeaux:
        print(f"  {len(bandeaux)} texte(s) identique(s) dans une même source (bandeau) → resume")
    if sponsorises:
        print(f"  {len(sponsorises)} article(s) sponsorisé(s) écartés")
    print(f"  chapô pris dans le texte complet : {sum(1 for a in lot if a.get('chapo_du_texte_complet'))}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("nom", help="nom du dossier (corpus/dossiers/<nom>/)")
    ap.add_argument("requetes", nargs="*", help="requêtes, cherchées entre guillemets")
    ap.add_argument("--jours", type=int, default=60, help="période couverte, jusqu'à aujourd'hui (défaut 60)")
    ap.add_argument("--jusqu-au", type=dt.date.fromisoformat, help="dernier jour couvert, AAAA-MM-JJ (défaut : aujourd'hui)")
    ap.add_argument("--editions", nargs="+", choices=list(EDITIONS), default=list(EDITIONS),
                    help="éditions de Google Actualités (défaut : toutes)")
    ap.add_argument("--textes", action="store_true", help="étape 2 : texte complet des articles déjà listés")
    ap.add_argument("--remplacer", action="store_true", help="refaire l'étape 1 même si les textes sont commencés")
    ap.add_argument("--garder", action="store_true",
                    help="étape 1 : garder les articles de la liste précédente que cette collecte ne retrouve pas")
    args = ap.parse_args()

    dossier = SORTIE / "dossiers" / args.nom
    if args.textes:
        if not (dossier / f"lot_{args.nom}.json").exists():
            print(f"Pas de lot_{args.nom}.json : lancer d'abord l'étape 1.")
            return 1
        textes(dossier, args.nom)
        return 0

    if not args.requetes:
        ap.error("au moins une requête pour l'étape 1")
    if (dossier / "textes.json").exists() and not args.remplacer:
        print(f"{dossier.relative_to(SORTIE.parent)}/textes.json existe : l'étape 2 est commencée. "
              "--remplacer pour refaire la liste (les textes déjà pris restent dans textes.json).")
        return 1
    dossier.mkdir(parents=True, exist_ok=True)
    liens_f = dossier / "liens.json"
    if not liens_f.exists() and (dossier / f"lot_{args.nom}.json").exists():
        ancien = json.loads((dossier / f"lot_{args.nom}.json").read_text("utf-8"))
        ecrire_json(liens_f, {urllib.parse.urlsplit(a["lien_google"]).path.rsplit("/", 1)[-1]: a["lien"]
                              for a in ancien if a.get("lien_resolu")})
    articles, meta, tranches = collecter(args.nom, args.requetes, args.jours, args.jusqu_au, liens_f,
                                       {e: EDITIONS[e] for e in args.editions})
    if args.garder and (dossier / f"lot_{args.nom}.json").exists():
        ancien = json.loads((dossier / f"lot_{args.nom}.json").read_text("utf-8"))
        gardes = garder_precedents(articles, ancien, meta["collecte"])
        articles.sort(key=lambda a: (a["date"] or "", a["source"]))
        ancienne_meta = json.loads((dossier / "meta.json").read_text("utf-8")) if (dossier / "meta.json").exists() else {}
        if "reintegres" in ancienne_meta:
            meta["reintegres"] = ancienne_meta["reintegres"]
        meta["gardes_de_la_liste_precedente"] = [a["id"] for a in gardes]
        meta["n_articles"] = len(articles)
        print(f"\n{len(gardes)} article(s) de la liste précédente gardé(s), absents de cette collecte")
    ecrire_json(dossier / f"lot_{args.nom}.json", articles)
    ecrire_comptage(dossier / "comptage.csv", articles)
    ecrire_json(dossier / "meta.json", meta)
    par_semaine(articles, tranches)
    print(f"\n{len(articles)} articles, {meta['n_liens_non_resolus']} lien(s) non résolu(s) "
          f"→ {dossier.relative_to(SORTIE.parent)}/")
    print(f"Étape suivante : .venv/bin/python dossier.py {args.nom} --textes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
