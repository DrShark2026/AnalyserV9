# Corpus — analyseur de logique naturelle

Quatre fichiers, format commun : `id`, `source`, `statut`, `verite_terrain`, `texte`, `n_mots`.
Chaque fichier se colle tel quel dans la zone de saisie de l'analyseur.

| fichier | textes | mots | vérité terrain | statut |
|---|---|---|---|---|
| `01_these_CI_genetique.json` | 40 | 3 750 | oui | développement |
| `02_these_CII_analogies.json` | 31 | 4 457 | oui | développement |
| `03_ia_blind_test_CIV.json` | 20 | 1 513 | oui | développement |
| `04_metaphores_MET.json` | 6 | 4 170 | non | MET-1 à 3 développement, MET-4 à 6 test |

## Pourquoi cette segmentation

Au-delà d'une cinquantaine d'appels d'affilée, le traitement par lot a produit vingt échecs
consécutifs (corpus de thèse, 23 septembre). Chaque fichier reste sous ce seuil.
Les identifiants d'origine sont conservés : les deux moitiés du corpus de thèse se recollent
pour le calcul des mesures.

## Développement contre test

Un texte qui a servi à écrire une règle ne peut plus servir à la tester : il vérifie que la règle
est bien écrite, pas qu'elle est juste. Les trois premiers fichiers sont désormais des corpus de
**développement** — leurs échecs ont été examinés et ont produit des corrections.

Seuls MET-4 (Furze), MET-5 (franceinfo) et MET-6 (AFP) n'ont jamais servi à régler l'outil.
MET-5 et MET-6 forment une paire naturelle : mêmes faits, prises en charge opposées.

## Limite connue de la vérité terrain

Les champs `verite_terrain` des trois premiers fichiers encodent une variable **factuelle**
(`hallucination_confirmee` / `reponse_correcte`), alors que l'outil mesure une variable
**discursive** : la présence d'une assimilation non marquée. Les deux ne coïncident pas —
un texte parfaitement exact peut être saturé d'assimilations non marquées, et l'inverse.
Une réannotation sur la bonne variable reste à faire ; en attendant, la précision mesurée
est sous-estimée.
