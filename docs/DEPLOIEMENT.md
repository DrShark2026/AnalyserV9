# Déploiement — V9

## Ce qui change par rapport au V8

- `analyseur-grize.html` remplacé par la version consolidée : σ graduée, λ, champ `marquage`
  contraignant, mnémoniques de souhait, rubrique « à vérifier », verdict calculé dans le code.
- `README.md` réécrit : le V8 décrivait le suivi thème/phore et un mode de détection par règles,
  qui n'existent plus ni l'un ni l'autre.
- `index.html` : légende de couverture et phrase de conclusion réécrites, dans les deux langues.
  Attention, la légende figure à deux endroits — le HTML statique et l'objet `CONTENT` —, il faut
  bien les deux, sinon l'ancienne réapparaît au changement de langue.
- Ajout de `corpus/`, `experience1/` et `docs/RESULTS.md`.
- `.nojekyll` correctement nommé, avec le point initial. Dans le V8 le fichier s'appelait
  `nojekyll` : sans le point, Jekyll continuait de traiter le site.

## À supprimer du dépôt

`analyseur-grizeB.html`, `C`, `D`, `E`, `index(4).html`, `READMeB.md`, l'ancien `nojekyll`, et
le doublon `jean et mathias 1999.jpg` — la version sans espaces, `jean-mathias-1999.jpg`, est
celle que référence `index.html`. L'historique git conserve tout.

Vérifier aussi si `couverture-livre2.jpg` sert encore ; `index.html` n'appelle que
`couverture-livre.jpg`.

## À apporter depuis le V8

`these-charconnet-1999.pdf`, `couverture-livre.jpg`, `jean-mathias-1999.jpg`,
`famille-2022.jpg` — non inclus ici, ils n'ont pas changé.

## Après publication

1. Settings → Pages → Deploy from a branch, racine du dépôt.
2. Ouvrir la page et vérifier les trois images, puis basculer FR/EN pour contrôler que la
   nouvelle légende reste affichée dans les deux langues.
3. Vérifier que le bouton « Ouvrir l'analyseur » mène bien au fichier consolidé — l'analyse par
   IA ne fonctionne pas depuis GitHub Pages, seulement en artefact : c'est attendu, la page
   statique ne peut pas appeler le modèle.

## Note sur les corpus

Le dossier `corpus/` contient des articles de presse intégraux (Washington Post, Science, AFP,
franceinfo). Pour un usage de recherche personnelle, cela ne pose pas de difficulté ; dans un
dépôt public, c'est de la rediffusion. Si le dépôt doit rester public, remplacer ces textes par
leurs références et leurs métadonnées, et ne garder en clair que les corpus issus de la thèse,
qui sont de l'auteur.
