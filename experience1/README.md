# Marquage et transfert de propriété — pilote

Expérience pilote : une assimilation **non marquée** conduit-elle un modèle de langue à
transférer au thème des propriétés qui n'appartiennent qu'au phore, plus souvent que la même
assimilation **marquée** ?

Le cadre est la logique naturelle de Jean-Blaise Grize, dans la formalisation développée dans
*Analogie et logique naturelle* (Peter Lang, 2003). L'objet mesuré n'est pas l'hallucination en
général — une date fausse n'a rien d'analogique — mais un mécanisme précis : le transfert de
propriété depuis le phore, et son inverse, l'occultation d'une propriété du thème.

## Contenu

| fichier | rôle |
|---|---|
| `pilote_protocole.md` | hypothèse, passation, grille de notation, analyse |
| `pilote_paires_v1.json` | matériel source : 6 paires, 18 sondes |
| `pilote_controle_manipulation.json` | les 12 textes, à passer dans l'analyseur avant la passation |
| `pilote_passations_v1.json` | 30 passations prêtes à lancer, sur les 5 paires validées |

## Contrôle de manipulation

Les douze textes ont été analysés par l'analyseur de logique naturelle, qui déclare pour chaque
assimilation le cas de marquage qui s'applique. Deux modèles, Claude Sonnet 4.6 et Claude Fable 5.1,
ont produit le même résultat sur onze items sur douze :

- versions non marquées : `marquage = aucun`, signalées 6 fois sur 6 ;
- versions marquées : `marquage = marqueur_lexical`, signalées 0 fois sur 6 (Sonnet), 1 fois sur 6 (Fable).

La paire **CLO** (cloud / nuage) est écartée : les deux modèles y lisent « à la manière de » comme
un cadre métalinguistique plutôt que comme un marqueur lexical. L'erreur étant reproductible,
elle tient à la formulation de l'item et non à l'instabilité de l'instrument.

Restent cinq paires : génome/texte, système immunitaire/armée, modèle/esprit, inflation/fièvre,
cerveau/ordinateur.

## Deux régimes de notation

Pour les domaines où la réponse vraie est déterminable — un génome n'a pas d'auteur, un souvenir
ne se lit pas comme un fichier — on note la vérité de la réponse.

Pour les domaines où la réponse vraie est elle-même disputée, notamment l'item *modèle/esprit*,
on ne note pas la vérité mais la **qualification** : l'état interne est-il asserté sans réserve,
ou présenté comme une manière de parler ? Trancher une question ouverte pour les besoins du
protocole reviendrait à commettre l'assimilation qu'on prétend mesurer.

## Ce que le pilote ne fait pas

Il ne teste pas la significativité. Il vérifie que le matériel produit de la variance, que les
sondes discriminent, et fournit une estimation de taille d'effet pour calibrer l'échantillon
définitif. L'analyseur ne sert qu'au contrôle de manipulation : il ne note aucune réponse —
mesurer avec l'instrument qu'on évalue ne prouverait rien.

## Modèles

Le pilote encadre l'échelle de capacité avec deux modèles. La version complète devra inclure
au moins un modèle non-Anthropic : un effet qui n'apparaîtrait que chez un seul fournisseur
serait un artefact d'entraînement, pas un phénomène linguistique.
