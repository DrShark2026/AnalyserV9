// Rejoue les contrôles déterministes sur un export du traitement par lot, sans appeler le modèle.
// Usage : node tests/rejouer.js <export.json> [préfixe d'id…]     ex. node tests/rejouer.js resultats.json POL-25
'use strict';
const fs = require('fs');
const { chargerAnalyseur } = require('./charger.js');
const [fichier, ...ids] = process.argv.slice(2);
if(!fichier){ console.error('usage : node tests/rejouer.js <export.json> [id…]'); process.exit(2); }
const postTraiter = chargerAnalyseur().get('postTraiter');
const d = JSON.parse(fs.readFileSync(fichier, 'utf8'));
const cas = (Array.isArray(d) ? d : [d]).filter(c => !ids.length || ids.some(i => String(c.id || '').startsWith(i)));
for(const c of cas){
  const a = JSON.parse(JSON.stringify(c));
  (a.pec || []).forEach(p => {   // on repart de la sortie du modèle
    if(p.adhesion_avant_inversion){ p.adhesion = p.adhesion_avant_inversion; p.fonction = p.fonction_avant_inversion; }
    if(p.source_avant_polyphonie){ p.source = p.source_avant_polyphonie; p.adhesion = p.adhesion_avant_polyphonie; }
    if(p.portee_avant_polyphonie) p.portee = p.portee_avant_polyphonie;
  });
  a.pec = (a.pec || []).filter(p => !p.ajout_antiphrase);
  const r = postTraiter(a, c.texte || '');
  console.log(`\n== ${c.id || '(sans id)'} — ironie_detectee=${r.ironie_detectee} figure_detectee=${JSON.stringify(r.figure_detectee)} risk_detected=${r.risk_detected}`);
  r.journal_sigma.forEach(l => console.log('  ' + l));
  r.pec.forEach((p, i) => console.log(`  σ[${i}] ${p.source}/${p.adhesion}${p.fonction ? ' (' + p.fonction + ')' : ''} — ${String(p.text || '').slice(0, 90)}`));
}
