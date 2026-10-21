# Veille RSS

Récupère chaque jour les articles de presse française et américaine qui parlent d'immigration, de religion, de mouvements sociaux, d'intelligence artificielle ou qui recourent à des analogies historiques (Pétain, Vichy, Munich, Weimar…) (presse, sites tech et blogs d'entreprises d'IA), et les range au format de l'analyseur.

## Lancer

```bash
cd veille
python3 collect_rss.py --test      # vérifie que chaque fil répond
python3 collect_rss.py --jours 3   # collecte les articles des 3 derniers jours
```

Le résultat arrive dans `corpus/veille_AAAA-MM-JJ.json`, prêt à coller dans l'analyseur. Un article déjà vu n'est jamais repris deux fois (voir `registre.json`).

Chaque article indique pourquoi il a été retenu : `mots_reperes` (les mots-clés trouvés), `score` (nombre de passages repérés, ceux du titre comptent double) et `dans_titre` (vrai si un mot-clé figure dans le titre). Rien n'est exclu sur ces critères : un score de 1 sans mot dans le titre signale en général une simple mention en passant.

Un article dont le titre ou le début du chapô (300 premiers caractères) contient « Sponsored », « Partner content » ou « Contenu sponsorisé » (sans tenir compte des majuscules ni des accents) porte `categorie: "sponsorise"` au lieu de la catégorie du fil. Il reste dans le corpus, mais n'entre dans aucun lot et `complet.py` ne cherche pas son texte.

Le champ `mnemoniques_collecte` relève les verbes et noms qui prêtent à l'IA une activité mentale (`pense`, `comprend`, `hallucine`, `thinks`, `reasoning`…), d'après la liste `mnemoniques` de `mots_cles.json`. Il n'influe pas sur la sélection.

## Régler

- `feeds.json` : la liste des fils. Ajouter une ligne pour un nouveau fil, ou mettre `"actif": false` pour en couper un. Le champ `orientation` (`gauche`, `centre gauche`, `centre`, `droite`) et le champ `degre` (`modere` ou `radical`) situent chaque fil ; ils restent vides pour les fils tech, les blogs d'entreprise et ceux qu'on n'a pas classés. Le champ `pays` (code ISO du siège : `FR`, `US`, `GB`, `CA`, `BE`, `CH`) est recopié dans chaque article. Le champ `themes`, s'il est présent, limite la recherche à ces thèmes : les fils francophones hors de France (Le Devoir, Radio-Canada, La Presse, RTBF, RTS, Le Temps, RFI, Jeune Afrique) cherchent `mouvements_sociaux`, `ia`, `immigration` et `religion`, sans `analogies_historiques`, et leur `orientation` reste vide, l'axe gauche-droite français ne s'y appliquant pas. Comme toute source, chacun garde au plus 3 articles dans le lot politique. Le champ `posture_ia` situe les fils qui parlent d'IA : `promoteur`, `securite`, `critique`, `neutre` ou `labo` ; il reste vide pour les fils politiques et généralistes. Ces trois champs sont recopiés dans chaque article. `theme_defaut` (ici `ia`, sur les fils IA) donne ce thème à un article du fil qui ne contient aucun mot repère : il est gardé avec un score de 0 et `theme_par_defaut: true`. `exclure_auteurs` écarte à la collecte les articles d'un fil signés d'un de ces auteurs (pour MIT Technology Review, le contenu sponsorisé de « MIT Technology Review Insights »). `texte_complet: false` (ici OpenAI, dont le site refuse le texte complet par un 403) fait garder le résumé du fil : les articles portent `statut_texte: "resume"` dès la collecte et `complet.py` ne les ouvre jamais, même avec `--refaire`. Un résumé identique au titre (fil d'Anthropic, qui n'est pas officiel : il vient du dépôt GitHub Olshansk/rss-feeds) est vidé pour ne pas compter deux fois. Un article à thème par défaut n'entre pas dans le lot IA : l'exemption de seuil des fils à `posture_ia` renseignée ne vaut que pour les articles qui contiennent au moins un mot repère.
- `mots_cles.json` : les mots qui font retenir un article, par thème et par langue. Thèmes : `immigration`, `religion`, `mouvements_sociaux`, `ia`, `analogies_historiques`. Les mots sont cherchés entiers, au pluriel ou au féminin près (pour les mots de plus de 3 lettres) : `réfugié` prend `réfugiés` et `réfugiée`, pas « se réfugier » ; `collabo` ne prend plus `collaboration`. Dans une expression, chaque mot peut s'accorder (`titre de séjour` prend `titres de séjour`). `Munich` prend toujours le Bayern. `_exclusions` liste, par thème, les expressions où un mot ne compte pas : « catholique » est ignoré dans « Université catholique » et « Institut catholique ».

## Limites

Les fils RSS ne donnent que le titre et un court résumé, pas l'article entier. C'est suffisant pour suivre la circulation des expressions dans les titres et les chapôs ; pour une analyse complète, il faut récupérer l'article à part.

## Texte complet

```bash
cd veille
python3 -m venv .venv && .venv/bin/pip install trafilatura   # une seule fois
.venv/bin/python complet.py          # dernier corpus, articles qui peuvent entrer dans un lot
```

Ouvre le lien de chaque article retenu et ajoute `texte_complet` et `statut_texte` (`complet`, `partiel` ou `echec`). Le script respecte robots.txt, espace ses requêtes d'au moins 3 secondes et ne contourne ni paywall ni protection anti-robot : un article réservé aux abonnés donne `partiel` (seul le début public est gardé), une page anti-robot donne `echec`. Si plusieurs articles d'une même source donnent le même texte, c'est un bandeau et non l'article : ils passent aussi en `echec`. Un article dont le texte complet commence par une mention de contenu sponsorisé (même règle qu'à la collecte : MIT Technology Review ne la met que dans la page) passe en `categorie: "sponsorise"` et sort des lots ; ce contrôle porte à chaque passage sur tous les articles qui ont un texte complet, déjà traités compris. Seules les erreurs passagères (réseau, délai dépassé, HTTP 5xx) sont retentées, dans le même passage, 3 essais au plus ; un 403, une page anti-robot ou un paywall ne le sont jamais. Un article déjà traité n'est pas repris aux passages suivants, sauf avec `--refaire` lancé à la main. Un échec porte `echec_passager` (vrai si les 3 essais ont buté sur une erreur passagère).

## Concordance

```bash
python3 concordance.py 'frontier|fronti[eè]re' -i
python3 concordance.py '(?i:superintelligen|super intelligence)|\bSI\b' --avant-apres 2026-09-01 -o corpus/concordance_si.csv
```

Cherche une expression régulière dans tout le corpus (`corpus/veille_*.json`) et écrit un CSV de concordance (KWIC), une ligne par occurrence : date, source, catégorie, langue, champ (`titre`, `chapô` ou `texte_complet`), guillemets, 60 caractères de contexte de chaque côté, lien. `guillemets` vaut `autour` si le terme est dans un passage entre guillemets de 5 mots au plus, `citation` si le passage est plus long (discours rapporté), `non` sinon. Dans `texte_complet`, les paragraphes qui répètent le titre ou le chapô sont sautés.

La recherche tient compte des majuscules (sinon `\bSI\b` prendrait « si ») : `-i` l'en dispense, `(?i:…)` le fait pour une partie du motif. `--avant-apres AAAA-MM-JJ` ajoute une colonne `periode` (`avant` ou `apres`, selon la date de l'article) et sépare le bilan affiché. Par défaut, le CSV va dans `corpus/concordance.csv`.

## Lots pour l'analyseur

```bash
python3 lots.py                      # dernier corpus
```

Écrit `corpus/lots/lot_ia_AAAA-MM-JJ.json` (thème `ia`) et `corpus/lots/lot_politique_AAAA-MM-JJ.json` (thèmes `immigration`, `religion` et `mouvements_sociaux` ; le thème `analogies_historiques` n'entre dans aucun lot), à coller dans l'analyseur. `texte` reste le titre + chapô ; quand le fil n'a pas de chapô, il est pris dans le premier paragraphe du texte complet (`chapo_du_texte_complet: true`). `texte_complet` n'est gardé que pour les articles `complet` ; `n_mots` compte les mots de `texte`. Un article en `echec` (page anti-robot, robots.txt, 403, extraction vide, bandeau) reste dans le lot avec son résumé RSS et `statut_texte: "resume"` ; il garde `echec_passager`, ce qui le distingue d'un article d'un fil à `texte_complet: false`. Les doublons (même lien ou même titre) sont écartés, ainsi que les articles de score inférieur à 2 dans le lot IA et inférieur à 1 dans le lot politique ; les articles des fils à `posture_ia` renseignée sont exemptés du seuil du lot IA (quatrième valeur de `LOTS`), sauf ceux qui n'ont le thème que par défaut (`theme_par_defaut: true`). Cette règle est dans `candidat()`, que `complet.py` reprend : il récupère le texte de tout article qui peut entrer dans un lot. Chaque source garde au plus 6 articles dans le lot IA et 3 dans le lot politique, qui sert de groupe témoin (troisième valeur de `LOTS` dans `lots.py`), ceux de meilleur score ; à score égal, l'ordre du corpus décide. Le script affiche le nombre d'articles par lot et par source, et ceux écartés par ce plafond.

## Automatisation

Un minuteur systemd utilisateur lance la collecte (`--jours 2`), puis `complet.py`, puis `lots.py` chaque jour à 19h ; avec `Persistent=true`, une exécution manquée (machine éteinte) est rattrapée au démarrage suivant. Avant de lancer quoi que ce soit, le service attend jusqu'à 2 minutes que la résolution DNS fonctionne (le réseau n'est souvent pas prêt au démarrage) ; passé ce délai, la collecte est lancée quand même. Si `complet.py` échoue, `lots.py` tourne quand même (préfixe `-` sur sa ligne du service). La sortie s'ajoute à `collecte.log` ; au premier lancement d'un nouveau mois, `tourner_log.sh` renomme le log du mois précédent en `collecte_AAAA-MM.log`.

```bash
systemctl --user list-timers veille.timer       # prochaine exécution
systemctl --user start veille.service           # lancer tout de suite
```

Les fichiers sont dans `~/.config/systemd/user/veille.{service,timer}`.

