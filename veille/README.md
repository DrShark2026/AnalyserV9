# Veille RSS

Récupère chaque jour les articles de presse française et américaine qui parlent d'immigration, de religion ou d'intelligence artificielle (presse, sites tech et blogs d'entreprises d'IA), et les range au format de l'analyseur.

## Lancer

```bash
cd veille
python3 collect_rss.py --test      # vérifie que chaque fil répond
python3 collect_rss.py --jours 3   # collecte les articles des 3 derniers jours
```

Le résultat arrive dans `corpus/veille_AAAA-MM-JJ.json`, prêt à coller dans l'analyseur. Un article déjà vu n'est jamais repris deux fois (voir `registre.json`).

Chaque article indique pourquoi il a été retenu : `mots_reperes` (les mots-clés trouvés), `score` (nombre de passages repérés, ceux du titre comptent double) et `dans_titre` (vrai si un mot-clé figure dans le titre). Rien n'est exclu sur ces critères : un score de 1 sans mot dans le titre signale en général une simple mention en passant.

Le champ `mnemoniques_collecte` relève les verbes et noms qui prêtent à l'IA une activité mentale (`pense`, `comprend`, `hallucine`, `thinks`, `reasoning`…), d'après la liste `mnemoniques` de `mots_cles.json`. Il n'influe pas sur la sélection.

## Régler

- `feeds.json` : la liste des fils. Ajouter une ligne pour un nouveau fil, ou mettre `"actif": false` pour en couper un. Le champ `orientation` est vide : à remplir soi-même si on veut équilibrer les camps.
- `mots_cles.json` : les mots qui font retenir un article, par thème et par langue.

## Limites

Les fils RSS ne donnent que le titre et un court résumé, pas l'article entier. C'est suffisant pour suivre la circulation des expressions dans les titres et les chapôs ; pour une analyse complète, il faut récupérer l'article à part.

## Texte complet

```bash
cd veille
python3 -m venv .venv && .venv/bin/pip install trafilatura   # une seule fois
.venv/bin/python complet.py          # dernier corpus, articles de score >= 2
```

Ouvre le lien de chaque article retenu et ajoute `texte_complet` et `statut_texte` (`complet`, `partiel` ou `echec`). Le script respecte robots.txt, espace ses requêtes d'au moins 3 secondes et ne contourne ni paywall ni protection anti-robot : un article réservé aux abonnés donne `partiel` (seul le début public est gardé), une page anti-robot donne `echec`. Si plusieurs articles d'une même source donnent le même texte, c'est un bandeau et non l'article : ils passent aussi en `echec`. Les articles déjà traités ne sont pas retentés, sauf avec `--refaire`.

## Automatisation

Un minuteur systemd utilisateur lance la collecte (`--jours 2`) puis `complet.py` chaque jour à 19h ; avec `Persistent=true`, une exécution manquée (machine éteinte) est rattrapée au démarrage suivant. La sortie s'ajoute à `collecte.log`.

```bash
systemctl --user list-timers veille.timer       # prochaine exécution
systemctl --user start veille.service           # lancer tout de suite
```

Les fichiers sont dans `~/.config/systemd/user/veille.{service,timer}`.

