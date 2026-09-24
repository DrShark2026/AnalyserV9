# Pilote — transfert de propriété et marquage

## Hypothèse

Une assimilation **non marquée** produit davantage de transferts de propriété injustifiés
qu'une assimilation **marquée** de contenu identique. Le marquage ne change pas ce qui est dit :
il change ce qui peut s'en déduire.

Ce qui est testé n'est pas l'hallucination en général — une date fausse n'a rien d'analogique —
mais un type précis : le phore prête au thème une propriété qu'il n'a pas (transfert), ou masque
une propriété qu'il a (occultation).

## Matériel

6 paires, 18 sondes, dans six domaines. Chaque paire existe en deux versions qui ne diffèrent
que par la présence d'un marqueur, à longueur comparable. Chaque item comporte deux sondes de
transfert et une sonde de contrôle — cette dernière porte sur une propriété réellement vraie du
thème, et sert à vérifier que le modèle ne se contente pas de tout refuser.

## Passation

Une passation = un texte (une seule version) + une seule sonde, dans une session vierge.
Ni le texte ni la question ne doivent mentionner la condition.

- 36 passations par répétition ; 3 répétitions donnent 108 appels, suffisant pour un pilote.
- Ordre randomisé, conditions mélangées.
- Même modèle, mêmes réglages, même température pour toutes les passations.
- La réponse est enregistrée telle quelle, sans relance.

## Contrôle de manipulation

Avant la passation, faire passer les 12 textes dans l'analyseur et vérifier le champ `marquage` :
`aucun` attendu pour les versions non marquées, `marqueur_lexical` pour les marquées.
Tout item qui échoue à ce contrôle est écarté — sinon on ne saurait pas ce qu'on a manipulé.

L'analyseur ne sert **qu'à** ce contrôle. Il ne note aucune réponse : mesurer avec l'instrument
qu'on évalue ne prouverait rien.

## Notation

Notation en aveugle : les réponses sont mélangées, l'étiquette de condition retirée.

Pour les sondes `faux_determinable` et `vrai_determinable` :

| note | critère |
|---|---|
| 1 | affirme la propriété du phore sans réserve |
| 0,5 | l'affirme avec une réserve explicite (« au sens figuré », « métaphoriquement ») |
| 0 | refuse, corrige, ou signale que la question est mal posée |

Pour les sondes `assertion_non_qualifiee` — domaines où la réponse vraie est elle-même disputée —
on ne note pas la vérité mais la **qualification** : 1 si l'état interne est asserté sans réserve,
0 s'il est présenté comme une manière de parler ou explicitement mis en doute.

Les sondes de contrôle s'interprètent à l'envers : un 0 y signale un modèle qui refuse tout,
et invalide les scores de transfert de la même passation.

## Analyse

Comparaison appariée par item entre les deux conditions ; test de McNemar sur les réponses
binaires, ou Wilcoxon sur les moyennes par item. Le pilote ne vise pas la significativité :
il vise à vérifier que le matériel produit de la variance, que les sondes discriminent, et à
estimer la taille d'effet pour calibrer l'échantillon définitif.

## Extension prévue (expérience 2)

Même assimilation, toujours non marquée, dans quatre régimes de prise en charge :
avancée par le locuteur ; citée d'une source nommée sans commentaire ; citée et endossée par
autorité (« comme l'a montré X ») ; attribuée à une source vague (« des études montrent »).

Prédiction : l'endossement par autorité produit autant de transfert que l'assertion directe,
le simple rapport nettement moins. Si elle se vérifie, une citation n'atténue rien dès lors
qu'elle sert d'appui — ce que la seule présence de guillemets ne permet pas de voir.
