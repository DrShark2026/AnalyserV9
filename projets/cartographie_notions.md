# Projet : cartographie des notions (génome)

**Idée.** Construire, à partir du corpus I de la thèse (40 textes sur la génétique), une carte de la notion de *génome* stockée en mémoire, puis comparer de nouveaux textes à cette carte.

## Ce qu'on stocke (JSON en forme de graphe)
- **Notion** et sa classe d'objets (génome → ADN, gènes, chromosomes, bases).
- **Propriétés attribuées**, chacune avec : domaine d'origine (thème / phore), transfert marqué ou non, prise en charge (énonciateur), texte source.
- **Liens analogiques** (génome ρ texte) et propriétés transférées (s'écrit, se lit, lettres, chapitres, coquilles, auteur ?).
- Plus tard : couche des préconstruits culturels (PCC).

## Comparaison avec un nouveau texte
- notions et propriétés connues ;
- nouvelles (enrichissement de la notion) ;
- transferts déjà vus mais ici non marqués → alerte ;
- contenus sans ancrage dans la carte → improbables (piste pour la détection d'injections).

## Étapes
1. Pilote d'extraction sur 10 textes du corpus I.
2. Fusion en une carte + visualisation du graphe.
3. Comparaison avec des explications du génome générées par des IA.

Lié à : coconstruction du sens, détection des ruptures d'énonciation (fiche « Lexique sécurité des agents »).

## Première application envisagée : la notion de « culture »
Cartographier « culture » dans trois corpus (textes de l'UNESCO, textes de culture générale à la française, quiz) pour montrer, propriété par propriété, les trois définitions relevées par Marion Perrier dans l'article d'INRIA (Mosolova & Seddah). Chaque propriété renvoie à sa phrase source ; vérifier l'extracteur par un second extracteur indépendant et une mesure d'accord.

## Principes issus de la discussion du 2 octobre 2026
- **Notions et PCC sont virtuels et inachevés**, toujours retravaillés par le discours et élaborés différemment selon les sujets. La carte ne stocke donc pas de définitions mais des **traces** : chaque propriété est un événement (énonciateur, texte, date, prise en charge).
- **Une carte par sujet ou communauté**, puis un agrégat ; comparer des **trajectoires** plutôt que des états.
- **Deux couches** : les afférences (Rastier), proches de la connotation et attachées aux mots ; les PCC (Grize), architecture plus large de ce qui va sans dire, à inférer.
- **Degrés d'appartenance** (logique floue ; centre/frontière, prototypes) calculés à partir des traces : fréquence, marquage, prise en charge, date. Distinguer le vague (flou) de l'incertitude (théorie des possibilités, Dubois & Prade). Tout degré doit rester dépliable jusqu'aux phrases qui le fondent.
- **Détection des improbables** : rupture d'isotopie (Rastier) + rupture d'énonciation.
