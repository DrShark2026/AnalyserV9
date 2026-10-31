#!/usr/bin/env python3
"""Trie les articles d'un dossier venus de la requête "AI" "soul" en huit catégories.

    hors_sujet        « soul » n'a rien à voir avec l'IA (jeu vidéo, soul music,
                      marque, « heart and soul »…)
    indetermine       « soul » n'est pas dans le texte complet (50 mots ou plus)
    non_analysable    « soul » n'est pas dans le texte disponible, et ce texte n'est pas
                      complet ou fait moins de 50 mots : on ne force pas le classement
    a_recollecter     comme non_analysable ou indetermine, mais le titre est dans le sujet
                      (liste tenue à la main : tri_soul_a_recollecter.txt dans le dossier)
    ame_esthetique    l'âme comme authenticité, créativité, intention humaine
                      (souvent : l'IA n'en a pas)
    ame_metaphysique  l'âme au sens religieux ou philosophique (une IA peut-elle
                      avoir une âme, âme et conscience, le pape Léon…)
    ame_collective    l'âme d'une institution, d'un secteur, d'un lieu (soul of
                      business, Hollywood's soul, fight for its soul)
    soul_doc          le « soul document » de Claude (sa constitution)

Les sites de musique (Soul Kitchen, Soul Bag, Larsen…) et Body+Soul sont hors_sujet
d'office, par la source. Les mots sont découpés hors apostrophes et guillemets
('Soul', Soul's) ; « AI » d'un vol Air India (AI-2379) ou du prénom Ai Jing n'est pas
l'IA, ni le « ai » de « j'ai ». Un article où « AI » n'est que cela est hors_sujet.
D'abord, les « soul » qui ne sont pas l'âme sont écartés : genres musicaux (soul
music, afro soul, la soul), expressions (heart and soul, a single soul, an innocent
soul, soul-crushing, souls on board), noms propres (Soul Machines, l'appli Soul, Dark Souls, Rubber
Soul…). On garde les « soul » à moins de 15 mots d'un terme du domaine (AI,
artificial intelligence, machine, model, chatbot, robot, consciousness, sentient,
Claude, ChatGPT…). Puis, dans l'ordre :
    aucun soul gardé, titre qui demande si une IA a une âme → ame_metaphysique
    plus de « soul » dans le texte → indetermine (hors_sujet s'il n'y avait que des
        « soul » écartés)
    aucun soul gardé → hors_sujet
    un « soul doc(ument) / overview » → soul_doc
    au moins la moitié des soul gardés sont l'âme d'une institution → ame_collective
    indices autour des soul gardés (40 mots) : la catégorie qui en a le plus
        l'emporte (art, musique, création… contre Dieu, pape, théologie…)
    à égalité : le déterminant — « a soul », « a human soul », « give X a soul »,
        « souls » → ame_metaphysique ; « soul » sans article (have soul, lacks soul,
        no soul), soulless, soulful → ame_esthetique ; la forme la plus fréquente
    encore égalité : titre qui demande si une IA a une âme → ame_metaphysique
    encore égalité : indices sur tout le texte ; sinon ame_esthetique, « à vérifier »
Chaque ligne dit pourquoi dans la colonne motif.

Rien n'est modifié dans le dossier : le tri est écrit à part.

Sortie, dans corpus/dossiers/<nom>/ :
    tri_soul.csv            id, titre, source, date, categorie, phrase, motif
    echantillon_verif.csv   10 articles tirés au hasard par catégorie (même format)

Usage :
    python3 tri_soul.py
    python3 tri_soul.py conscience_ia --graine 7
    python3 tri_soul.py --essai          # comptage seul, rien d'écrit (ni CSV ni dossier.log)
"""
import argparse
import collections
import csv
import datetime as dt
import json
import random
import re
import sys
import urllib.parse

from collect_rss import SORTIE

FENETRE = 15        # mots autour de « soul » pour le filtre du domaine
CONTEXTE = 40       # mots autour de « soul » pour départager esthétique et métaphysique
REQUETE = '"AI" "soul"'
PAR_CATEGORIE = 10
CATEGORIES = ("hors_sujet", "indetermine", "non_analysable", "a_recollecter", "ame_esthetique", "ame_metaphysique", "ame_collective", "soul_doc")

SOUL = re.compile(r"^souls?$|^soul(less|lessness|ful|fully)$", re.I)
DOMAINE = re.compile(
    r"^(ai|a\.i\.?|ia|ais|agi|artificial|artificielle?|machines?|models?|chatbots?|bots?|robots?|robotics?|"
    r"androids?|algorithms?|algorithmes?|consciousness|conscious|sentient|sentience|claude|chatgpt|gpt\S*|"
    r"gemini|grok|copilot|llms?|openai|anthropic|computers?|ordinateurs?|digital|numérique)$", re.I)
METAPHYSIQUE = re.compile(
    r"^(god|gods|dieu|divine|divin\w*|relig\w*|spiritu\w*|theolog\w*|théolog\w*|church|église|pope|pape|vatican|"
    r"leo|léon|catholic\w*|catholique|christian\w*|chrétien\w*|christ|jesus|jésus|faith|foi|pray\w*|prière|"
    r"sacred|sacré|holy|metaphysic\w*|métaphysi\w*|philosoph\w*|immortal\w*|afterlife|ensoul\w*|"
    r"consciousness|conscience|sentien\w*|personhood|dignity|dignité|bible|biblical|scripture\w*|"
    r"encyclical|encyclique|bishop|priest|prêtre|rabbi|imam|islam\w*|buddh\w*|hindu\w*|dualism|"
    r"descartes|aquinas|créateur|creation|moral|morale|mind|minds|heaven|salvation|sin)$", re.I)
ESTHETIQUE = re.compile(
    r"^(art|arts|artist\w*|artistic|artwork\w*|music\w*|musique|song\w*|singer\w*|creativ\w*|créativ\w*|"
    r"film\w*|movie\w*|cinema|écrit\w*|writing|writer\w*|author\w*|novel\w*|poe\w*|poè\w*|design\w*|craft\w*|"
    r"authentic\w*|authenti\w*|artisan\w*|slop|soulless|brand\w*|marketing|content|voice|storytell\w*|"
    r"painting\w*|painter\w*|photograph\w*|illustrat\w*|animation|animators?|studio\w*|album\w*|"
    r"generated|génér\w*|imitat\w*|copy|copies|style|aesthetic\w*|esthéti\w*|touch|handmade|culture|"
    r"creator\w*|creators|performance|perform\w*|dance\w*|theater|theatre|actors?|lyrics|melod\w*|"
    r"game|games|gaming|fashion|food|cuisine|chef|recipe\w*|human-made|human-written|feel|feeling\w*|emotion\w*)$",
    re.I)
# « soul » qui n'est pas l'âme : genres musicaux, expressions figées, noms connus
EXPRESSIONS = re.compile(
    r"\b(heart|body|mind|life|cœur|corps)\s+(and|&|et)\s+souls?\b"
    r"|\b(neo|afro|northern|southern|deep|blue[- ]eyed|r\s?&\s?b|rnb|funk|gospel|jazz|pop|psychedelic|amapiano)[- ]soul\b"
    r"|\bsoul[- ]?(music|musique|tracks?|songs?|singers?|chanteu\w*|albums?|artists?|artistes?|genre|bands?|groupe|"
    r"funk|jazz|r\s?&\s?b|ballads?|vibes?|food|mates?|searching|strike|calibur|knights?|reaver|hackers?|train|"
    r"cycle|cycling|machines?|app|matching|eater|edge|sisters?|origin|ferry|reborn|zhang|x\b|2\.0|n1|notes)"
    r"|\b(la|en|de la)\s+soul\b|\b(couleur|voix|style|univers|influences?|chanteuse|chanteur|reine|roi)\s+soul\b"
    r"|\b(sell|sells|selling|sold)\s+(their|his|her|your|my|our)\s+souls?\b"
    r"|\bsoul-(crushing|sucking|squeezing|searching|destroying|stirring|baring|deep)\b"
    r"|\bsouls?['’]?s?\s+on\s+board\b"
    r"|\b(single|living|kindred|lone|lonely|brave|poor|innocent|gentle|kind|old|troubled|tortured|sweet|beautiful|good)\s+souls?\b|\bsoul in sight\b"
    r"|\bsummer of soul\b|\bchicken soup for the soul\b|\boncle soul\b|\b(dark|demon'?s|demon’s|rubber|painted|lost)\s+souls?\b"
    r"|\b(gpt[- ]?\d+(\.\d+)?|\d+\.\d+|a2o|dragon|soul)\s+soul\b",
    re.I)
# l'appli chinoise Soul (Soul App, de Zhang Lu) : tous ses « Soul » à majuscule sont un nom propre
APPLI_SOUL = re.compile(r"\bSoul,? Zhang Lu|\bSoulX|\bSoul App\b|\bLoxi\w*|social apps?\b[^.\n]{0,60}\bSoul\b"
                        r"|\bSoul\b[^.\n]{0,60}\bsocial apps?\b", re.I)
# un titre qui demande si une IA (une machine, Claude…) a une âme
QUESTION = re.compile(
    r"\b(ai|a\.i\.|machines?|robots?|chatbots?|computers?|claude|chatgpt|llms?|algorithms?|models?|it)\b"
    r"[^?]{0,40}\b(have|has|possess|get|gain|develop|acquire|grow|need)\s+(a\s+|an?\s+)?souls?\b[^?]{0,40}\?"
    r"|\bsouls?\b[^?]{0,20}\b(in|of|for)\s+(the\s+|a\s+)?(machines?|ai|a\.i\.|robots?|chatbots?|claude)\b[^?]{0,20}\?",
    re.I)
# l'âme d'une institution, d'un secteur, d'un lieu : soul of business, Hollywood's soul, fight for its soul
COLLECTIF_NOMS = (r"(business(es)?|compan(y|ies)|firms?|corporat\w+|industr(y|ies)|sectors?|hollywood|newsrooms?|"
                  r"journalism|media|press|cit(y|ies)|towns?|nations?|countr(y|ies)|party|democracy|republic|"
                  r"universit(y|ies)|schools?|education|brands?|internet|web|sports?|football|teams?|clubs?|"
                  r"professions?|workplaces?|organi[sz]ations?|institutions?|markets?|economy|capitalism|tech|"
                  r"silicon valley|wall street|communit(y|ies)|neighbou?rhoods?|studios?|labels?|newspapers?|"
                  r"magazines?|publishing|cinema|america|india|cyprus|europe|china|britain|france)")
COLLECTIF = re.compile(
    r"\bsouls? of (the |our |its |their |a |this |modern |american |british |global )?([\w-]+ ){0,2}?" + COLLECTIF_NOMS + r"\b"
    r"|\b" + COLLECTIF_NOMS + r"(['’]s)? souls?\b"
    r"|\b(fight|fights|fighting|battle|battles|struggle|war|wars)\s+(over|for)\s+(its|their|the|our) soul\b"
    r"|\b(lose|loses|losing|lost|save|saving|sell|sells|selling|sold)\s+its soul\b",
    re.I)
COLLECTIF_PROPRE = re.compile(r"\bsouls? of (the )?([A-Z][\w-]+)")
# avant « soul » : un mot qui exclut la lecture « a + adjectif + soul », et les mots après
# lesquels « soul » est sans article (have soul, lacks soul, no soul, with soul)
DETERMINANTS = {"the", "its", "his", "her", "their", "our", "my", "your", "this", "that", "every", "each", "of", "no"}
SANS_ARTICLE = {"have", "has", "had", "having", "lack", "lacks", "lacked", "lacking", "no", "without", "with", "any",
                "zero", "got", "missing", "little", "more", "less", "real", "true", "much"}
MOT = re.compile(r"[\w.-]+", re.U)      # apostrophes et guillemets hors des mots : 'Soul' → Soul, Soul's → Soul s
MIN_MOTS = 50       # en dessous (ou sans texte complet), un article sans « soul » est non_analysable
# « AI » qui n'est pas l'IA : vols d'Air India (AI-2379, AI 171), le prénom Ai Jing (Ai Ching, Ai Qing)
FAUX_AI = re.compile(r"\bAI(?=[- ]?\d{2,4}\b)|\bAi(?= (?:Jing|Ching|Qing)\b)")
# « ai » du français élidé (j'ai, n'ai, qu'ai…), qui sans les apostrophes passerait pour « AI »
AI_ELIDE = re.compile(r"(\b(?:[jnlmts]|qu)['’])ai\b", re.I)
# sites de musique (et Body+Soul) : « soul » y vient du nom ou du genre musical → hors_sujet d'office
SITES_MUSIQUE = re.compile(
    r"soul-?kitchen|soulbag|soul ?bag|larsenmag|\blarsen\b|hypesoul|soulinstereo|soul in stereo|youknowigotsoul|"
    r"northernsoul|citimuzik|modzik|ziknation|jazzophone|jazzradio|jazz radio|journalofgospelmusic|soundofviolence|"
    r"sound of violence|rocknfolk|rock&folk|unitedrocknations|concertandco|thatgrapejuice|that grape juice|bodyandsoul",
    re.I)
PHRASE_SPAN = re.compile(r"[^\n.!?…]+(?:[.!?…]+|$)", re.M)


def neutraliser(texte):
    """texte où les « soul » qui ne sont pas l'âme (genre musical, expression figée,
    nom propre) deviennent « s0ul » (même longueur : les positions ne bougent pas),
    et le nombre d'occurrences neutralisées."""
    n = 0

    def sous(m):
        nonlocal n
        n += len(re.findall(r"soul", m.group(), re.I))
        return re.sub(r"(s)(o)(ul)", lambda x: x.group(1) + "0" + x.group(3), m.group(), flags=re.I)

    texte = EXPRESSIONS.sub(sous, texte)
    texte = FAUX_AI.sub(lambda m: "Xx", texte)
    texte = AI_ELIDE.sub(lambda m: m.group(1) + "xx", texte)
    if APPLI_SOUL.search(texte):
        texte = re.sub(r"\bSoul\b(?!\s+(doc|document|overview))", sous, texte)
    noms = set()
    for p in PHRASE_SPAN.finditer(texte):
        jetons = list(MOT.finditer(p.group()))
        lettres = [j.group() for j in jetons if j.group()[:1].isalpha() and len(j.group()) > 3]
        if not lettres or sum(w[0].isupper() for w in lettres) / len(lettres) >= 0.6:
            continue        # titre en capitales initiales : on ne peut pas y repérer les noms propres
        for k, j in enumerate(jetons):
            w = j.group().strip(".'’-")
            if not re.fullmatch(r"(Soul|SOUL)[sS]?", w):
                continue
            suite = jetons[k + 1].group().lower().strip(".'’-,") if k + 1 < len(jetons) else ""
            if suite in ("doc", "document", "overview", "file", "spec"):
                continue    # le « soul document » de Claude
            debut, fin = k, k
            def colle(a, b):    # deux jetons à majuscule séparés seulement par des espaces
                return (jetons[a].group()[:1].isupper() and jetons[b].group()[:1].isupper()
                        and not p.group()[jetons[a].end():jetons[b].start()].strip())
            while debut > 0 and colle(debut - 1, debut):
                debut -= 1
            while fin + 1 < len(jetons) and colle(fin, fin + 1):
                fin += 1
            if k == 0 and fin == k:
                continue    # « Soul » seul en début de phrase : un mot ordinaire
            if fin > debut:
                noms.add(p.group()[jetons[debut].start():jetons[fin].end()].strip(".'’"))
            else:
                texte = texte[:p.start() + j.start()] + "s0ul" + texte[p.start() + j.start() + 4:]
                n += 1
    for nom in sorted(noms, key=len, reverse=True):
        texte = re.sub(re.escape(nom), lambda m: sous(m), texte)
    return texte, n


def collectif(texte, pos):
    """La « soul » à la position pos est-elle l'âme d'une institution, d'un secteur, d'un lieu ?"""
    autour = texte[max(0, pos - 70):pos + 70]
    if any(m.start() <= pos - max(0, pos - 70) < m.end() + 1 for m in COLLECTIF.finditer(autour)):
        return True
    m = COLLECTIF_PROPRE.match(texte, pos)
    return bool(m) and not DOMAINE.match(m.group(2))


def determinant(ms, i):
    """« meta » pour « a soul », « a human soul », « souls » ; « esth » pour « soul » sans article
    (have soul, lacks soul, no soul) et soulless, soulful ; None sinon (the soul, its soul…)."""
    m = ms[i].lower()
    if m == "souls":
        return "meta"
    if m != "soul":
        return "esth"
    avant = ms[i - 1].lower() if i else ""
    if avant in ("a", "an") or (i > 1 and ms[i - 2].lower() in ("a", "an") and avant not in DETERMINANTS):
        return "meta"
    if avant in SANS_ARTICLE:
        return "esth"
    return None


def classer(texte, titre=""):
    """(catégorie, position dans texte de l'occurrence retenue, motif)."""
    brut = texte
    texte, neutres = neutraliser(texte)
    jetons = list(MOT.finditer(texte))
    ms = [j.group().strip(".'’-") for j in jetons]
    souls = [i for i, m in enumerate(ms) if SOUL.match(m)]
    note = f" ; {neutres} soul écarté(s) (musique, nom propre, expression)" if neutres else ""
    proches = [i for i in souls if any(DOMAINE.match(m) for m in ms[max(0, i - FENETRE):i + FENETRE + 1])]
    docs = [i for i in proches if i + 1 < len(ms) and ms[i + 1].lower() in ("doc", "document", "overview")]
    collectifs = [i for i in proches if collectif(texte, jetons[i].start())]
    question = bool(QUESTION.search(titre))
    if not proches and FAUX_AI.search(brut) and not any(DOMAINE.match(m) for m in ms):
        return "hors_sujet", FAUX_AI.search(brut).start(), "« AI » seulement comme vol Air India ou prénom (Ai Jing)"
    if not proches and question:
        return "ame_metaphysique", brut.find(titre) if titre else None, "le titre demande si une IA a une âme"
    if not souls:
        if neutres:
            return "hors_sujet", texte.lower().find("s0ul"), f"soul seulement comme musique, nom propre ou expression ({neutres}×)"
        return "indetermine", None, "soul absent du texte disponible"
    if not proches:
        return "hors_sujet", jetons[souls[0]].start(), f"soul ({len(souls)}×) loin des termes du domaine" + note
    if docs:
        return "soul_doc", jetons[docs[0]].start(), f"« soul document » de Claude ({len(docs)}×)" + note
    if collectifs and 2 * len(collectifs) >= len(proches):
        return ("ame_collective", jetons[collectifs[0]].start(),
                f"{len(collectifs)}/{len(proches)} soul près du domaine sont l'âme d'une institution, d'un secteur, d'un lieu" + note)
    proches = [i for i in proches if i not in collectifs]
    meta = esth = 0
    vus = set()
    for i in proches:
        for j in range(max(0, i - CONTEXTE), min(len(ms), i + CONTEXTE + 1)):
            if j in vus or j == i:
                continue
            vus.add(j)
            meta += bool(METAPHYSIQUE.match(ms[j]))
            esth += bool(ESTHETIQUE.match(ms[j]))
    esth += sum(ms[i].lower().startswith("soulless") for i in proches)
    motif = f"{len(proches)}/{len(souls)} soul près du domaine ; indices métaphysique {meta}, esthétique {esth}" + note
    if meta != esth:
        return "ame_metaphysique" if meta > esth else "ame_esthetique", jetons[proches[0]].start(), motif
    # égalité des indices : le déterminant, puis le titre, puis les indices sur tout le texte
    dets = {i: determinant(ms, i) for i in proches}
    n_meta = [i for i, d in dets.items() if d == "meta"]
    n_esth = [i for i, d in dets.items() if d == "esth"]
    if len(n_meta) != len(n_esth):
        gagnants = n_meta if len(n_meta) > len(n_esth) else n_esth
        return ("ame_metaphysique" if gagnants is n_meta else "ame_esthetique", jetons[gagnants[0]].start(),
                motif + f" ; égalité départagée par le déterminant : {len(n_meta)} « a soul / souls », "
                f"{len(n_esth)} « soul » sans article")
    if question:
        return "ame_metaphysique", jetons[proches[0]].start(), motif + " ; égalité départagée par le titre (question : une IA a-t-elle une âme ?)"
    meta = sum(bool(METAPHYSIQUE.match(m)) for m in ms)
    esth = sum(bool(ESTHETIQUE.match(m)) for m in ms)
    motif += f" ; égalité départagée sur tout le texte (métaphysique {meta}, esthétique {esth})"
    if meta > esth:
        return "ame_metaphysique", jetons[proches[0]].start(), motif
    if meta == esth:
        motif += " ; à vérifier"
    return "ame_esthetique", jetons[proches[0]].start(), motif


def phrase_de(texte, pos):
    """Phrase de texte qui contient la position pos, ou ''."""
    if pos is None or pos < 0:
        return ""
    for p in PHRASE_SPAN.finditer(texte):
        if p.start() <= pos < p.end():
            return " ".join(p.group().split())[:600]
    return ""


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("nom", nargs="?", default="conscience_ia")
    ap.add_argument("--graine", type=int, default=None, help="graine du tirage de l'échantillon")
    ap.add_argument("--essai", action="store_true", help="affiche le comptage sans rien écrire (ni CSV ni dossier.log)")
    args = ap.parse_args()

    dossier = SORTIE / "dossiers" / args.nom
    lot = json.loads((dossier / f"lot_{args.nom}.json").read_text("utf-8"))
    textes = json.loads((dossier / "textes.json").read_text("utf-8")) if (dossier / "textes.json").exists() else {}
    choisis = [a for a in lot if any(q.startswith(REQUETE + " ") for q in a.get("requetes") or [])]
    f_recollecter = dossier / "tri_soul_a_recollecter.txt"
    a_recollecter = set()
    if f_recollecter.exists():
        a_recollecter = {l.split()[0] for l in f_recollecter.read_text("utf-8").splitlines() if l.strip() and not l.startswith("#")}

    lignes = []
    for a in choisis:
        titre, _, chapo = (a.get("texte") or "").partition("\n")
        complet = (textes.get(a["id"]) or {}).get("texte_complet") or a.get("texte_complet") or ""
        texte = "\n".join(x for x in (titre, chapo, complet) if x)
        if SITES_MUSIQUE.search(a["source"] + " " + urllib.parse.urlsplit(a.get("lien") or "").netloc):
            categorie, rang, motif = "hors_sujet", None, f"source : {'Body+Soul (santé)' if 'bodyandsoul' in a.get('lien', '') else 'site de musique'} ({a['source']})"
        else:
            categorie, rang, motif = classer(texte, titre.strip())
        if categorie == "indetermine" and a["id"] in a_recollecter:
            categorie = "a_recollecter"
            motif += " ; titre dans le sujet : texte complet à récupérer"
        if categorie == "indetermine":
            n_mots = len(texte.split())
            if a.get("statut_texte") != "complet" or n_mots < MIN_MOTS:
                categorie = "non_analysable"
                motif += f" ; texte {a.get('statut_texte')}, {n_mots} mots"
                if a["id"] in a_recollecter:
                    categorie = "a_recollecter"
                    motif += " ; titre dans le sujet : texte complet à récupérer"
        lignes.append({"id": a["id"], "titre": titre.strip(), "source": a["source"], "date": a["date"],
                       "categorie": categorie, "phrase": phrase_de(texte, rang), "motif": motif})

    champs = ["id", "titre", "source", "date", "categorie", "phrase", "motif"]

    def ecrire(chemin, ls):
        with open(chemin, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=champs)
            w.writeheader()
            w.writerows(ls)

    if args.essai:
        compte = collections.Counter(l["categorie"] for l in lignes)
        print("essai, rien d'écrit : " + ", ".join(f"{c} {compte[c]}" for c in CATEGORIES))
        return 0
    ecrire(dossier / "tri_soul.csv", lignes)
    hasard = random.Random(args.graine)
    par_cat = collections.defaultdict(list)
    for l in lignes:
        par_cat[l["categorie"]].append(l)
    echantillon = []
    for c in CATEGORIES:
        echantillon += hasard.sample(par_cat[c], min(PAR_CATEGORIE, len(par_cat[c])))
    ecrire(dossier / "echantillon_verif.csv", echantillon)

    compte = collections.Counter(l["categorie"] for l in lignes)
    egalites = sum(1 for l in lignes if "à vérifier" in l["motif"])
    resume = (f"tri_soul.py : {len(lignes)} articles de la requête {REQUETE} triés → tri_soul.csv ; "
              + ", ".join(f"{c} {compte[c]}" for c in CATEGORIES)
              + f" (égalités à vérifier : {egalites}) ; "
              f"échantillon de {len(echantillon)} → echantillon_verif.csv")
    print(resume)
    with open(dossier / "dossier.log", "a", encoding="utf-8") as f:
        f.write(f"===== {resume} ({dt.datetime.now():%F %T}) =====\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
