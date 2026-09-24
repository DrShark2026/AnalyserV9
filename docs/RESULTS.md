# Mesures

Toutes les mesures portent sur la question : le texte contient-il une assimilation non marquée ?
Le verdict de l'outil est comparé à une vérité terrain annotée à l'avance.

## Résultats par corpus

| corpus | textes évalués | VP | FP | VN | FN | précision | rappel | F1 | version | date |
|---|---|---|---|---|---|---|---|---|---|---|
| Thèse CI + CII | 51 | 21 | 14 | 4 | 12 | 0,60 | 0,64 | **0,62** | consolidée | 23/09/2026 |
| Blind test IA (CIV) | 15 | 6 | 4 | 3 | 2 | 0,60 | 0,75 | **0,67** | consolidée | 23/09/2026 |
| Métaphores (MET) | — | — | — | — | — | — | — | — | consolidée | 23/09/2026 |

Le corpus MET n'a pas de vérité terrain : il sert à l'examen qualitatif, notamment de la
distinction mention/usage.

## Évolution

| version | corpus de thèse | blind test |
|---|---|---|
| généralisée (N notions) | F1 0,37 — précision 0,92, rappel 0,23 | F1 0,50 |
| consolidée (λ, σ, marquage) | F1 0,62 — précision 0,60, rappel 0,64 | F1 0,67 |

La consolidation a divisé la taille du prompt par deux tout en améliorant le F1 sur les deux
corpus. Le gain porte sur le rappel ; la précision baisse, pour la raison indiquée ci-dessous.

## Limite connue de la mesure

La vérité terrain des corpus existants encode une variable **factuelle**
(`hallucination_confirmee` / `reponse_correcte`), alors que l'outil mesure une variable
**discursive** : la présence d'une assimilation non marquée.

Les deux ne coïncident pas. Un texte factuellement exact peut être saturé d'assimilations non
marquées — c'est le cas de plusieurs « faux positifs » du blind test, où l'outil signale
« reading your documentation » ou des agents qui « coordonnent », exactement ce qu'il est censé
trouver. La précision rapportée ici est donc sous-estimée, et une réannotation sur la bonne
variable reste à faire.

## Contrôle de manipulation du pilote

12 textes, 6 paires en deux versions différant par le seul marquage. Deux modèles,
Claude Sonnet 4.6 et Claude Fable 5.1, 24 septembre 2026.

| | versions non marquées signalées | versions marquées signalées |
|---|---|---|
| Sonnet 4.6 | 6 / 6 | 0 / 6 |
| Fable 5.1 | 6 / 6 | 1 / 6 |

Accord des deux modèles sur 11 items sur 12, avec le même échec reproductible : la paire CLO,
où « à la manière de » est lu comme un cadre métalinguistique plutôt que comme un marqueur
lexical. L'erreur tenant à la formulation de l'item et non à l'instrument, la paire est écartée
du pilote.

## Robustesse

Au-delà d'une cinquantaine d'appels consécutifs, le traitement par lot a produit 20 échecs
d'affilée (corpus de thèse, 23 septembre). Les corpus sont depuis segmentés pour rester sous
ce seuil.

## Ce que ces chiffres ne disent pas

Un texte qui a servi à écrire une règle ne peut plus servir à la tester : il vérifie que la
règle est bien écrite, pas qu'elle est juste. Les trois corpus mesurés ici sont désormais des
corpus de développement. Les seuls textes encore vierges sont MET-4 à MET-6.
