#!/bin/sh
# Un log par mois : si collecte.log date d'un mois passé (dernière écriture),
# il devient collecte_AAAA-MM.log et le service en recommence un neuf.
# Lancé par veille.service avant la collecte.
cd "$(dirname "$0")" || exit 0
[ -f collecte.log ] || exit 0
mois=$(date -r collecte.log +%Y-%m)
[ "$mois" = "$(date +%Y-%m)" ] && exit 0
cible="collecte_$mois.log"
if [ -e "$cible" ]; then
    cat collecte.log >> "$cible" && rm collecte.log
else
    mv collecte.log "$cible"
fi
