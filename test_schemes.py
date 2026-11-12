# -*- coding: utf-8 -*-
import apparieur_schemes as A
S = A.charger_schemes("schemes.json")
def sch(i): return next(s for s in S if s["id"] == i)

# 1. détection + degré figure
art = {"titre": "Alice Huang, cette Mata Hari du silicium, inquiète Nvidia."}
r = A.apparier(art, S)
ids = [h["id"] for h in r["schemes"]]
assert "mata_hari" in ids, ids
occ = next(h for h in r["schemes"] if h["id"] == "mata_hari")["occurrences"][0]
assert occ["degre_theta5"] == "figure", occ

# 2. degré comparaison
art2 = {"texte": "Elle est soupçonnée comme une espionne au service de Pékin."}
r2 = A.apparier(art2, S)
occ2 = next(h for h in r2["schemes"] if h["id"] == "espionnage_chinois")["occurrences"][0]
assert occ2["degre_theta5"] == "comparaison", occ2

# 3. degré θ5 complet (classe nommée)
art3 = {"texte": "Huang, dernier avatar de l'homme contre la machine."}
r3 = A.apparier(art3, S)
occ3 = next(h for h in r3["schemes"] if h["id"] == "homme_vs_machine")["occurrences"][0]
assert occ3["degre_theta5"] == "theta5_complet", occ3

# 4. filature : riche vs pauvre
riche = {"texte": "Le code génétique : l'ADN est un texte de quatre lettres, les bases nucléotidiques ; les gènes sont des mots, les chromosomes des volumes ; on lit, on écrit et on édite le génome (CRISPR), par transcription et traduction."}
pauvre = {"texte": "On parle beaucoup du code génétique aujourd'hui."}
fr = A.score_filature(riche, sch("texte_genome"))
fp = A.score_filature(pauvre, sch("texte_genome"))
assert fr["score"] > 0.6 and fp["score"] < 0.4, (fr, fp)

# 5. candidat θ5 lexicalisé
assert "Mata Hari / silicium" in A.candidats_theta5("une Mata Hari du silicium"), A.candidats_theta5("une Mata Hari du silicium")

print("TOUS LES TESTS PASSENT ✓")
print("  filature texte/génome — riche:", fr["score"], "| pauvre:", fp["score"])
