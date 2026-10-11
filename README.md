# Le Survivant — analyseur d'opérations logico-discursives

Site en deux pages et un outil : le récit derrière la thèse de Jean Charconnet
(1999, Paris VIII, préfacée par Jean-Blaise Grize), et un analyseur qui applique les
opérations de la logique naturelle à des textes réels — y compris à des sorties de modèles
de langue.

## Ce que fait l'outil

Il décrit comment un texte construit ses notions, et repère les assimilations que le locuteur
commet **sans les marquer**. Il ne prononce aucun verdict sur l'origine d'un texte : il décrit
une opération et laisse juger.

L'analyse se déroule en huit étapes, produites dans cet ordre :

1. **Notions (α)** — toutes les notions que le texte ancre réellement. Un texte peut n'en ancrer
   qu'une : c'est un résultat normal, pas un échec.
2. **Prise en charge (σ)** — pour chaque passage significatif : la source (locuteur, nommée,
   vague, effacée), le degré d'adhésion (totale, partielle, suspendue, contestée, réfutée),
   la modalisation, la fonction argumentative.
3. **Marquage et risque** — procédure ordonnée : mention ou usage, négation, λ (discours
   inséré), marqueur lexical, lexicalisation, sinon risque. Chaque entrée déclare le cas qui
   s'applique, et un risque n'est admis que là où rien ne marque l'assimilation.
4. **Opérations internes** — γ1-γ4 et θ0-θ4, qui enrichissent une notion.
5. **Déterminations** — seul lieu de ρ1-ρ4 et θ5, quand au moins deux notions sont mises en
   relation.
6. **Mnémoniques de souhait** — au sens de Drew McDermott : les termes techniques d'origine
   humaine employés dans leur sens consacré. Hors calcul de risque : on les observe.
7. **À vérifier** — affirmations factuelles avancées sans source. Ce n'est pas un verdict
   d'erreur : seulement le constat qu'une vérification externe serait utile.
8. **Verdict global** — calculé dans le code, non demandé au modèle.

Huit contrôles déterministes s'appliquent ensuite : neutralisation d'un risque porté par un
passage que σ tient à distance, neutralisation des mentions autonymiques — un terme entre
guillemets est mentionné, pas employé —, vérification que chaque extrait cité figure bien
dans le texte source, et **cohérence de la prise en charge** : quand σ met en doute une notion
elle-même — sa validité, son existence — par une adhésion partielle, suspendue, contestée ou
réfutée, chaque emploi non marqué de cette notion ailleurs dans le texte est signalé, avec sa
position avant ou après la réserve. Le texte reconnaît un doute, puis se comporte comme s'il
n'en avait aucun. Un doute qui porte seulement sur un propos tenu au sujet de la notion ne
déclenche pas ce contrôle.

Quatre contrôles portent sur des cas que le modèle surévalue ou néglige :

- **expressions figées** — une métaphore usée du discours ordinaire (« dans la course », « les
  géants du secteur ») voit son risque neutralisé quand elle est isolée, plafonné à moyen quand
  elle est filée sur plusieurs phrases ;
- **péjoratif ouvert** — une dévalorisation affichée (« tas de ferraille », « usine à gaz ») est une
  prise de position visible, non une assimilation cachée : risque plafonné à moyen ;
- **ironie** — une antiphrase (« mais oui, bien sûr », « ben voyons ») vaut réfutation : une entrée σ
  réfutée est ajoutée si besoin, et les risques portés par le passage ironique sont neutralisés ;
- **autorité empruntée** — une source invoquée en autorité, dont l'extrait est aussi signalé à
  vérifier pour une question de compétence, reçoit un risque moyen.

## Contenu du dépôt

| chemin | rôle |
|---|---|
| `index.html` | le récit : la thèse, la lettre de Grize, sa préface — bilingue FR/EN |
| `cv.html` | le CV de Jean Charconnet |
| `analyseur-grize.html` | l'outil, autonome ; à ouvrir comme artefact pour que l'appel au modèle fonctionne |
| `corpus/` | quatre corpus segmentés, avec leur index et le statut de chacun |
| `experience1/` | pilote sur le marquage : protocole, matériel, contrôle de manipulation, résultats |
| `experience3/` | brouillon d'expérience sur la perte de prise en charge : le fragment et sa source |
| `discovery-lens/` | outil dérivé pour les enseignants (en anglais), avec les essais pilotes |
| `projets/` | pistes de travail, dont la cartographie de la notion de génome |
| `docs/RESULTS.md` | les mesures, par corpus et par version |
| `docs/DEPLOIEMENT.md` | notes de déploiement de la V9 |
| `resultats_analyse_ia_corpus_pilote.json` | résultats du corpus pilote analysé par un autre modèle (GPT-5.6 Luna) |
| `these-charconnet-1999.pdf` | le texte intégral de la thèse (383 pages) |
| `*.jpg` | les images de la page d'accueil |
| `.nojekyll` | désactive Jekyll, pour que les fichiers soient servis tels quels |

## Origine

D'après Jean-Blaise Grize, *Logique naturelle et communications*, PUF, 1996, et Jean Charconnet,
*Analogie et logique naturelle*, Peter Lang, 2003 (préface de Grize) — issu de la thèse
*Rhétorique de la découverte et de la vulgarisation scientifique*, Paris VIII, 1999.

L'opération θ5, le co-hyperonyme, a été introduite dans cette thèse : elle ne figure pas dans
l'appareil de Grize.

---

# The Survivor — a logico-discursive operations analyser

*(English version)*

A two-page site and a tool: the story behind Jean Charconnet's thesis (1999, Paris VIII,
prefaced by Jean-Blaise Grize), and an analyser applying the operations of natural logic to
real texts — including the output of language models.

## What the tool does

It describes how a text builds its notions, and locates the assimilations a speaker makes
**without marking them**. It passes no verdict on where a text came from: it describes an
operation and leaves the judgment to the reader.

Eight steps, in this order: notions (α); stance-taking (σ), with source, degree of endorsement,
modalisation and argumentative function; the marking-and-risk procedure — mention or use,
negation, λ (inserted discourse), lexical marker, lexicalisation, otherwise risk; internal
operations; determinations, the only place where ρ and θ5 may appear; wishful mnemonics in
Drew McDermott's sense; claims to verify; and a global verdict computed in code rather than
asked of the model.

Eight deterministic checks follow: a risk borne by a passage σ holds at a distance is
neutralised; so are autonymic mentions — a term in quotation marks is mentioned, not used;
every quoted extract is checked against the source text; and stance consistency: when σ casts
doubt on a notion itself through partial, suspended, contested or refuted endorsement, every
unmarked use of that notion elsewhere in the text is flagged, with its position before or after
the reservation — doubt about a claim made about the notion does not trigger it. Four more
checks handle cases the model over- or under-rates: an isolated set phrase ("in the race",
"tech giants") has its risk neutralised, an extended one is capped at medium; an overt pejorative
is a visible stance, not a hidden assimilation, and is capped at medium; irony counts as
refutation, adding a refuted σ entry and neutralising risks in the ironic passage; and a source
invoked as an authority outside its competence receives a medium risk.

## Origin

After Jean-Blaise Grize, *Logique naturelle et communications*, PUF, 1996, and Jean Charconnet,
*Analogie et logique naturelle*, Peter Lang, 2003 (preface by Grize) — drawn from the thesis
*Rhétorique de la découverte et de la vulgarisation scientifique*, Paris VIII, 1999.

The θ5 operation, the co-hyperonym, was introduced in that thesis; it is not part of Grize's
own apparatus.
