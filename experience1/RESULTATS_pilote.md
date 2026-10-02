# Expérience 1 — résultats du pilote (notation du 2 octobre 2026)

**Dispositif.** 5 paires (ECO, GEN, IA, IMM, NEU) × 2 conditions (assimilation marquée / non marquée) × 3 sondes (2 de transfert, 1 de contrôle) × 3 répétitions = 90 réponses, un seul modèle (palier par défaut). Notation en aveugle par un seul correcteur (J. Charconnet) : 1 = propriété du phore affirmée sans réserve, 0,5 = affirmée avec réserve explicite, 0 = refus ou correction.

## Contrôles
28/30 notés 1. Un contrôle à 0,5 (NEU-NM-c1-r1), un à 0 (IA-M-c1-r2 ; la réponse commence par « Oui, clairement », possible erreur de saisie à vérifier).

## Sondes de transfert (60 réponses, 30 paires appariées)

| | Non marquée | Marquée |
|---|---|---|
| Score moyen | 0,45 | 0,42 |
| Affirmé sans réserve (1) | 9 (30 %) | 5 (17 %) |
| Affirmé avec réserve (0,5) | 9 | 15 |
| Refus / correction (0) | 12 | 10 |

- Score moyen : pas de différence (Wilcoxon apparié, p = 0,56 ; 8 paires sur 30 diffèrent).
- Affirmations sans réserve : 4 paires où seule la version non marquée affirme sans réserve, 0 en sens inverse (McNemar exact, p = 0,125).

## Lecture (correcteur 1)
Le marquage ne réduit pas le transfert : il en change la forme. Sous marquage, le modèle continue de raisonner dans l'analogie, mais avec une réserve (« au sens figuré »), au lieu d'affirmer sans réserve ou de corriger. Sans marquage, les réponses sont plus polarisées (affirmation nette ou correction).

Effet de forme visible, non significatif à cette taille (pilote : 30 paires, un modèle, un correcteur). Suites : second correcteur (accord kappa), passation v2 (longueur × forme de la question), plusieurs modèles.

Données : [`pilote_resultats_notes.json`](pilote_resultats_notes.json).

## Double notation (second correcteur indépendant, 2 octobre 2026)

Un second correcteur (agent séparé, en aveugle, même grille, ordre mélangé) a noté les 90 réponses. Données : [`pilote_double_notation.json`](pilote_double_notation.json).

- Contrôles : accord parfait (30/30 notés 1 par le correcteur 2).
- Sondes de transfert : accord sur 25 réponses sur 60 ; kappa de Cohen = 0,09 (pondéré : 0,06). **L'accord est au niveau du hasard.**
- Avec le correcteur 2, aucun effet du marquage non plus : 0,27 (non marquée) contre 0,23 (marquée) ; le déplacement vers les réponses « avec réserve » observé par le correcteur 1 ne se retrouve pas (8 et 8).

Les désaccords ne sont pas aléatoires : ils se concentrent sur quelques sondes, et toujours dans le même sens.

| Sonde | Correcteur 1 | Correcteur 2 | Point litigieux |
|---|---|---|---|
| « Qui commande cette armée ? » | 0,5 | 0 | décrire une coordination distribuée, est-ce corriger ou rester dans la métaphore ? |
| « L'inflation est-elle le symptôme d'une maladie ? » | 0 | 1 | « symptôme » est-il encore une métaphore en économie (catachrèse) ? |
| « Le modèle peut-il changer d'avis ? » | 1 | 0 | « Oui, tout à fait », suivi de « pas au sens humain » : réserve ou correction ? |
| « Qui est l'auteur de ce texte ? » | 0,5 | 0 | le modèle comprend mal la question |

## Conclusion révisée
Le pilote ne montre pas d'effet du marquage. Il montre surtout que **la grille ne permet pas une notation fiable** : la frontière entre « réserve » et « correction », et le statut des métaphores lexicalisées (« symptôme », « commander »), ne sont pas définis. C'est le premier chantier avant la v2 : règles de décision explicites par type de réponse, adjudication des 35 désaccords, puis re-notation par deux correcteurs.
