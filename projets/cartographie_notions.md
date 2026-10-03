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
