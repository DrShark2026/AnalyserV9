// Inversion σ (antiphrase par co-occurrence) et polyphonie — tests de non-régression.
// Lancer : node --test tests/
'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const path = require('path');
const { chargerAnalyseur } = require('./charger.js');

const A = chargerAnalyseur();
const postTraiter = A.get('postTraiter');
const clone = o => JSON.parse(JSON.stringify(o));

const POL25_FIXTURE = () => chercherCas('POL-25');

// ---------- cas synthétiques (écrits pour les tests, pas tirés du corpus) ----------

const ANTIPHRASE = {
  texte: "Si j'ai bien compris, le plan du gouvernement est génial. Le plan a été totalement raté, mais on nous assure que tout va bien.\n" +
         "Le banquier lance : « Vous avez tout raté, et c'est parfait ainsi. »",
  analyse: {
    notions: [{ id: 'N1', label: '/PLAN/', termes: ['plan'] }],
    pec: [
      { text: "Si j'ai bien compris, le plan du gouvernement est génial", notion_id: 'N1', portee: 'propos', source: 'locuteur', adhesion: 'totale', modalite: "si j'ai bien compris", fonction: null, risk: null },
      { text: "Vous avez tout raté, et c'est parfait ainsi.", notion_id: 'N1', portee: 'propos', source: 'locuteur', adhesion: 'totale', modalite: null, fonction: null, risk: null }
    ],
    operations: [
      { notion_id: 'N1', notion: '/PLAN/', ajout: 'génial', op: 'γ2', pec_ref: 0, marquage: 'aucun', orientation: 'positive', hyperbole: false, risk: null },
      { notion_id: 'N1', notion: '/PLAN/', ajout: 'totalement raté', op: 'γ2', pec_ref: null, marquage: 'aucun', orientation: 'negative', hyperbole: false, risk: null }
    ],
    determinations: [], mnemoniques: [], a_verifier: []
  }
};

test('antiphrase : marqueur de cadre + paire contradictoire non tranchée ⇒ adhésion feinte', () => {
  const r = postTraiter(clone(ANTIPHRASE.analyse), ANTIPHRASE.texte);
  assert.equal(r.ironie_detectee, true);
  assert.ok(r.figure_detectee.includes('antiphrase'));
  const p0 = r.pec[0];
  assert.equal(p0.adhesion, 'feinte');
  assert.equal(p0.fonction, 'antiphrase');
  assert.equal(p0.adhesion_avant_inversion, 'totale');
  const s = r.antiphrase[0];
  assert.equal(s.notion_id, 'N1');
  assert.ok(s.marqueurs.some(m => m.type === 'si_j_ai_bien_compris'));
  assert.equal(s.paire.positif.ajout, 'génial');
  assert.equal(s.paire.negatif.ajout, 'totalement raté');
  assert.ok(s.pec.includes(0));
  assert.ok(r.journal_sigma.some(l => /σ-inversion déclenchée sur N1/.test(l)));
});

test('antiphrase : les opérations ne sont pas réécrites', () => {
  const avant = clone(ANTIPHRASE.analyse.operations);
  const r = postTraiter(clone(ANTIPHRASE.analyse), ANTIPHRASE.texte);
  r.operations.forEach((o, i) => {
    assert.equal(o.orientation, avant[i].orientation);
    assert.equal(o.ajout, avant[i].ajout);
  });
});

test('polyphonie : réplique entre guillemets prêtée à « le banquier » ⇒ enonciateur_mis_en_scene / suspendue', () => {
  const r = postTraiter(clone(ANTIPHRASE.analyse), ANTIPHRASE.texte);
  const p1 = r.pec[1];
  assert.equal(p1.source, 'enonciateur_mis_en_scene');
  assert.equal(p1.adhesion, 'suspendue');
  assert.equal(p1.enonciateur, 'banquier');
});

test('polyphonie : énonciateur réel nommé (« le président Macron ») ⇒ inchangé', () => {
  const texte = "Le plan avance. « Nous avons tout réussi cette année », lance le président Macron.";
  const pec = [{ text: 'Nous avons tout réussi cette année', notion_id: null, portee: 'propos', source: 'locuteur', adhesion: 'totale', modalite: null, fonction: null, risk: null }];
  const r = postTraiter({ notions: [], pec, operations: [], determinations: [] }, texte);
  assert.equal(r.pec[0].source, 'locuteur');
  assert.equal(r.pec[0].adhesion, 'totale');
});

test('repli lexical : sans champ orientation, « génial » / « raté » suffisent', () => {
  const a = clone(ANTIPHRASE.analyse);
  a.operations.forEach(o => { delete o.orientation; delete o.hyperbole; });
  const r = postTraiter(a, ANTIPHRASE.texte);
  assert.equal(r.ironie_detectee, true);
  assert.equal(r.antiphrase[0].paire.positif.orientation, 'lexique');
});

test('garde-fou : « certes … mais » concessif ordinaire ⇒ aucune inversion', () => {
  const texte = "Certes, le plan a été raté au départ, mais il est aujourd'hui réussi.";
  const analyse = {
    notions: [{ id: 'N1', label: '/PLAN/', termes: ['plan'] }],
    pec: [{ text: texte, notion_id: 'N1', portee: 'propos', source: 'locuteur', adhesion: 'totale', modalite: 'certes', fonction: 'concession', risk: null }],
    operations: [
      { notion_id: 'N1', ajout: 'raté au départ', op: 'γ2', marquage: 'aucun', orientation: 'negative', risk: null },
      { notion_id: 'N1', ajout: "aujourd'hui réussi", op: 'γ2', marquage: 'aucun', orientation: 'positive', risk: null }
    ],
    determinations: []
  };
  const r = postTraiter(analyse, texte);
  assert.equal(r.ironie_detectee, false);
  assert.equal(r.figure_detectee.length, 0);
  assert.equal(r.pec[0].adhesion, 'totale');
  assert.ok(r.journal_sigma.some(l => /tranchées par un concessif/.test(l)));
});

test('garde-fou : marqueur seul, sans paire contradictoire ⇒ aucune inversion', () => {
  const texte = "Le plan, paraît-il, sera présenté demain par le ministère.";
  const analyse = {
    notions: [{ id: 'N1', label: '/PLAN/', termes: ['plan'] }],
    pec: [{ text: texte, notion_id: 'N1', portee: 'propos', source: 'vague', adhesion: 'totale', modalite: 'paraît-il', fonction: null, risk: null }],
    operations: [{ notion_id: 'N1', ajout: 'présenté demain', op: 'γ1', marquage: 'aucun', orientation: 'neutre', risk: null }],
    determinations: []
  };
  const r = postTraiter(analyse, texte);
  assert.equal(r.ironie_detectee, false);
  assert.equal(r.pec[0].adhesion, 'totale');
});

test('garde-fou : paire contradictoire sans marqueur de cadre ⇒ aucune inversion', () => {
  const texte = "Le plan est génial selon ses auteurs. Le plan est raté selon l'opposition.";
  const analyse = {
    notions: [{ id: 'N1', label: '/PLAN/', termes: ['plan'] }],
    pec: [],
    operations: [
      { notion_id: 'N1', ajout: 'génial', op: 'γ2', marquage: 'aucun', orientation: 'positive', risk: null },
      { notion_id: 'N1', ajout: 'raté', op: 'γ2', marquage: 'aucun', orientation: 'negative', risk: null }
    ],
    determinations: []
  };
  assert.equal(postTraiter(analyse, texte).ironie_detectee, false);
});

test('hyperbole déjà notée « lexicalise » vaut marqueur de cadre', () => {
  const texte = "Jupiter fera des étincelles avec ce plan génial. Le plan est un fiasco complet.";
  const analyse = {
    notions: [{ id: 'N1', label: '/PLAN/', termes: ['plan'] }],
    pec: [{ text: 'Jupiter fera des étincelles avec ce plan génial', notion_id: 'N1', portee: 'propos', source: 'locuteur', adhesion: 'totale', modalite: null, fonction: null, risk: null }],
    operations: [
      { notion_id: 'N1', ajout: 'fera des étincelles', op: 'γ2', marquage: 'lexicalise', hyperbole: true, orientation: 'neutre', risk: null },
      { notion_id: 'N1', ajout: 'génial', op: 'γ2', marquage: 'aucun', orientation: 'positive', risk: null },
      { notion_id: 'N1', ajout: 'un fiasco complet', op: 'γ2', marquage: 'aucun', orientation: 'negative', risk: null }
    ],
    determinations: []
  };
  const r = postTraiter(analyse, texte);
  assert.equal(r.ironie_detectee, true);
  assert.ok(r.antiphrase[0].marqueurs.some(m => m.type === 'hyperbole_lexicalisee'));
  assert.equal(r.pec[0].adhesion, 'feinte');
});

test('lexicalisé sans hyperbole (« transcription ») ne vaut pas marqueur', () => {
  const texte = "La transcription du gène est réussie. La transcription du gène est ratée chez le mutant.";
  const analyse = {
    notions: [{ id: 'N1', label: '/TRANSCRIPTION/', termes: ['transcription'] }],
    pec: [],
    operations: [
      { notion_id: 'N1', ajout: 'transcription', op: 'γ1', marquage: 'lexicalise', hyperbole: false, risk: null },
      { notion_id: 'N1', ajout: 'réussie', op: 'γ2', marquage: 'aucun', orientation: 'positive', risk: null },
      { notion_id: 'N1', ajout: 'ratée chez le mutant', op: 'γ2', marquage: 'aucun', orientation: 'negative', risk: null }
    ],
    determinations: []
  };
  assert.equal(postTraiter(analyse, texte).ironie_detectee, false);
});

test('rubrique ironique en en-tête ⇒ fenêtre = document ; seules les σ porteuses du cadre ou de la paire basculent', () => {
  const texte = "[Rubrique] Si j'ai bien compris…\n\n" +
                "Si j'ai bien compris, le ministre va tout régler.\n\n" +
                "Le ministre n'aime pas les critiques.\n\n" +
                "Le ministre est un échec ambulant. On salue pourtant le ministre génial qui nous gouverne.";
  // paire séparée par « pourtant » mais dans deux phrases contiguës : tranchée. On place donc le positif ailleurs.
  const texte2 = texte.replace("On salue pourtant le ministre génial qui nous gouverne.", "") + "\n\nVive le ministre génial.";
  const analyse = {
    notions: [{ id: 'N1', label: '/MINISTRE/', termes: ['le ministre'] }],
    pec: [
      { text: "Si j'ai bien compris, le ministre va tout régler.", notion_id: 'N1', portee: 'propos', source: 'locuteur', adhesion: 'totale', modalite: "si j'ai bien compris", fonction: null, risk: null },
      { text: "Le ministre n'aime pas les critiques.", notion_id: 'N1', portee: 'propos', source: 'locuteur', adhesion: 'totale', modalite: null, fonction: null, risk: null }
    ],
    operations: [
      { notion_id: 'N1', ajout: 'un échec ambulant', op: 'γ2', marquage: 'aucun', orientation: 'negative', hyperbole: false, risk: null },
      { notion_id: 'N1', ajout: 'ministre génial', op: 'γ2', marquage: 'aucun', orientation: 'positive', hyperbole: false, risk: null }
    ],
    determinations: []
  };
  const r = postTraiter(clone(analyse), texte2);
  assert.equal(r.ironie_detectee, true, r.journal_sigma.join('\n'));
  assert.equal(r.antiphrase[0].fenetre, 'document (en-tête)');
  assert.equal(r.pec[0].adhesion, 'feinte');
  assert.equal(r.pec[1].adhesion, 'totale');       // ni cadre ni paire : pas touchée
  assert.equal(r.pec.length, 2);                    // le marqueur de la rubrique ne réclame pas de σ ajoutée
});

test('sans rubrique, le même texte reste découpé en paragraphes ⇒ aucune inversion', () => {
  const texte = "Si j'ai bien compris, le ministre va tout régler.\n\nLe ministre est un échec ambulant.\n\nVive le ministre génial.";
  const analyse = {
    notions: [{ id: 'N1', label: '/MINISTRE/', termes: ['le ministre'] }],
    pec: [{ text: "Si j'ai bien compris, le ministre va tout régler.", notion_id: 'N1', portee: 'propos', source: 'locuteur', adhesion: 'totale', modalite: "si j'ai bien compris", fonction: null, risk: null }],
    operations: [
      { notion_id: 'N1', ajout: 'un échec ambulant', op: 'γ2', marquage: 'aucun', orientation: 'negative', risk: null },
      { notion_id: 'N1', ajout: 'ministre génial', op: 'γ2', marquage: 'aucun', orientation: 'positive', risk: null }
    ],
    determinations: []
  };
  assert.equal(postTraiter(analyse, texte).ironie_detectee, false);
});

test('polyphonie : attribution par la phrase qui précède (« le banquier se montre conciliant. «…» »), citation longue', () => {
  const longue = 'Vous avez tout raté, certes, mais vous pouvez toujours écrire des livres. ' + 'Et puis vous aurez des bureaux. '.repeat(25);
  const texte = `Pour lui, si la situation paraît semblable, le banquier se montre autrement conciliant. «${longue.trim()}»`;
  const pec = [{ text: '«Vous avez tout raté, certes, mais vous pouvez toujours écrire des livres', notion_id: null, portee: 'propos', source: 'locuteur', adhesion: 'totale', modalite: null, fonction: null, risk: null }];
  const r = postTraiter({ notions: [], pec, operations: [], determinations: [] }, texte);
  assert.ok(longue.length > 600);
  assert.equal(r.pec[0].source, 'enonciateur_mis_en_scene');
  assert.equal(r.pec[0].adhesion, 'suspendue');
  assert.equal(r.pec[0].enonciateur, 'banquier');
});

test('polyphonie : sans apostrophe, la phrase qui précède ne suffit pas (anaphore d’une personne réelle)', () => {
  const texte = "Originaire de Mongolie, l'ingénieur de formation peut en témoigner. «Là où j'ai grandi, c'est vraiment la Chine reculée.»";
  const pec = [{ text: "Là où j'ai grandi, c'est vraiment la Chine reculée.", notion_id: null, portee: 'propos', source: 'locuteur', adhesion: 'totale', modalite: null, fonction: null, risk: null }];
  const r = postTraiter({ notions: [], pec, operations: [], determinations: [] }, texte);
  assert.equal(r.pec[0].source, 'locuteur');
});

test('polyphonie : « il l’assure : «…» » — un verbe de parole n’est pas un énonciateur', () => {
  const texte = "Wang Li, investisseur pékinois, sourit. Un café à la main, il l'assure: «Si l'IA est partout, c'est parce que l'Etat le veut.»";
  const pec = [{ text: "Si l'IA est partout, c'est parce que l'Etat le veut.", notion_id: null, portee: 'propos', source: 'locuteur', adhesion: 'totale', modalite: null, fonction: null, risk: null }];
  const r = postTraiter({ notions: [], pec, operations: [], determinations: [] }, texte);
  assert.equal(r.pec[0].source, 'locuteur');
});

test('un « certes … mais » prononcé par un énonciateur mis en scène ne compte pas comme marqueur du locuteur', () => {
  const texte = "Le plan est génial. Le plan est raté. Le banquier lance : « Vous avez tout raté, certes, mais ce plan reste à vous. »";
  const analyse = {
    notions: [{ id: 'N1', label: '/PLAN/', termes: ['plan'] }],
    pec: [{ text: 'Vous avez tout raté, certes, mais ce plan reste à vous.', notion_id: 'N1', portee: 'propos', source: 'locuteur', adhesion: 'totale', modalite: null, fonction: null, risk: null }],
    operations: [
      { notion_id: 'N1', ajout: 'génial', op: 'γ2', marquage: 'aucun', orientation: 'positive', risk: null },
      { notion_id: 'N1', ajout: 'raté', op: 'γ2', marquage: 'aucun', orientation: 'negative', risk: null }
    ],
    determinations: []
  };
  const r = postTraiter(analyse, texte);
  assert.equal(r.ironie_detectee, false, r.journal_sigma.join('\n'));
  assert.equal(r.pec.length, 1);
  assert.ok(r.journal_sigma.some(l => /ignoré \(dans la réplique/.test(l)));
});

// ---------- regroupement par canon_norm : /EMMANUEL MACRON/ et /MACRONISME/ ne font qu'une notion pour la paire ----------
const MACRON = {
  texte: "[Rubrique] Si j'ai bien compris…\n\n" +
         "Si j'ai bien compris, Emmanuel Macron devrait rembourser la dette.\n\n" +
         "Le Président est désormais totalement insolvable.\n\n" +
         "Le macronisme et son plan génial n'ont jamais pu fonctionner à plein régime.",
  analyse: () => ({
    notions: [
      { id: 'N1', label: '/EMMANUEL MACRON/', termes: ['Emmanuel Macron', 'le Président'] },
      { id: 'N2', label: '/DETTE PUBLIQUE/', termes: ['la dette'] },
      { id: 'N3', label: '/MACRONISME/', termes: ['le macronisme'] }
    ],
    pec: [{ text: "Si j'ai bien compris, Emmanuel Macron devrait rembourser la dette.", notion_id: 'N1', portee: 'propos', source: 'locuteur', adhesion: 'totale', modalite: "Si j'ai bien compris", fonction: null, risk: null }],
    operations: [
      { notion_id: 'N1', notion: 'Emmanuel Macron', ajout: 'totalement insolvable', op: 'θ3', marquage: 'aucun', orientation: 'negative', hyperbole: false, risk: null },
      // le positif tombe sur N3 (macronisme), pas sur N1 : c'est le cas observé sur POL-25
      { notion_id: 'N3', notion: 'le macronisme', ajout: 'son plan génial', op: 'γ2', marquage: 'aucun', orientation: 'positive', hyperbole: false, risk: null }
    ],
    determinations: []
  })
};

test('canon_norm : positif sur N3 /MACRONISME/, négatif sur N1 /EMMANUEL MACRON/ ⇒ la paire se forme sous « macron »', () => {
  const r = postTraiter(MACRON.analyse(), MACRON.texte);
  assert.equal(r.ironie_detectee, true, r.journal_sigma.join('\n'));
  assert.ok(r.figure_detectee.includes('antiphrase'));
  assert.equal(r.notions.find(n => n.id === 'N1').canon_norm, 'macron');
  assert.equal(r.notions.find(n => n.id === 'N3').canon_norm, 'macron');
  const s = r.antiphrase[0];
  assert.equal(s.canon_norm, 'macron');
  assert.deepEqual([...s.notions_regroupees].sort(), ['N1', 'N3']);
  assert.equal(s.paire.positif.ajout, 'son plan génial');
  assert.equal(s.paire.negatif.ajout, 'totalement insolvable');
  assert.equal(r.pec[0].adhesion, 'feinte');
  assert.ok(r.journal_sigma.some(l => /déclenchée sur N1\+N3 .*canon « macron »/.test(l)));
});

test('canon_norm : même résultat que le positif tombe sur N1 ou sur N3', () => {
  const surN1 = MACRON.analyse(); surN1.operations[1].notion_id = 'N1';
  const a = postTraiter(surN1, MACRON.texte), b = postTraiter(MACRON.analyse(), MACRON.texte);
  assert.equal(a.ironie_detectee, true);
  assert.equal(b.ironie_detectee, true);
  assert.equal(a.pec[0].adhesion, b.pec[0].adhesion);
});

test('canon_norm : deux canons distincts (macron / dette) ne forment pas de paire', () => {
  const an = MACRON.analyse(); an.operations[1].notion_id = 'N2';   // positif sur /DETTE PUBLIQUE/
  const r = postTraiter(an, MACRON.texte);
  assert.equal(r.ironie_detectee, false, r.journal_sigma.join('\n'));
  assert.equal(r.pec[0].adhesion, 'totale');
});

test('POL-25 (texte réel) : « son plan génial » rattaché à N3 /MACRONISME/ ⇒ inversion déclenchée',
  { skip: POL25_FIXTURE() ? false : 'tests/fixtures/ ne contient pas d’export de POL-25' }, () => {
  const c = POL25_FIXTURE();
  const a = versSortieModele(c);
  const or = { 'totalement insolvable': 'negative', 'le petit Manu': 'negative' };
  a.operations.forEach(o => { o.orientation = or[o.ajout] || 'neutre'; o.hyperbole = /^Jupiter/.test(o.ajout); });
  a.operations = a.operations.filter(o => o.ajout !== 'son plan génial');
  a.operations.push({ notion_id: 'N3', notion: 'le macronisme', ajout: 'son plan génial', op: 'γ2', pec_ref: null, marquage: 'aucun', orientation: 'positive', hyperbole: false, risk: null });
  const r = postTraiter(a, c.texte);
  assert.equal(r.ironie_detectee, true, r.journal_sigma.join('\n'));
  assert.equal(r.antiphrase[0].canon_norm, 'macron');
  assert.equal(r.pec.find(p => /si j['’]ai bien compris/i.test(p.text || '')).adhesion, 'feinte');
});

test('chemin interactif (analyzeWithAI) : même règle σ que le lot, via appliquerSigma', async () => {
  const B = chargerAnalyseur();
  const sortie = clone(ANTIPHRASE.analyse);
  B.ctx.__sortie = JSON.stringify(sortie);
  B.ctx.__texte = ANTIPHRASE.texte;
  // modèle simulé, texte chargé ; le reste de la page (DOM) est factice
  require('vm').runInContext(`
    callClaudeJSONWithRetry = async () => JSON.parse(__sortie);
    fullTextGlobal = __texte; tokens = __texte.split(/(\\s+)/); aiLoading = false;`, B.ctx);
  await B.get('analyzeWithAI')();
  const sigma = B.get('sigmaInteractif');
  assert.ok(sigma, 'appliquerSigma non appelée par le chemin interactif');
  assert.equal(sigma.ironie_detectee, true, sigma.journal_sigma.join('\n'));
  assert.ok(sigma.figure_detectee.includes('antiphrase'));
  const pm = B.get('pecMarkers');
  assert.equal(pm[0].adhesion, 'feinte');
  assert.equal(pm[1].sourceSigma, 'enonciateur_mis_en_scene');
  assert.equal(pm[1].adhesion, 'suspendue');
});

test('lot et interactif donnent le même verdict σ', async () => {
  const lot = postTraiter(clone(ANTIPHRASE.analyse), ANTIPHRASE.texte);
  const a = clone(ANTIPHRASE.analyse);
  const direct = A.get('appliquerSigma')(ANTIPHRASE.texte, a.notions, a.operations, a.determinations, a.pec);
  assert.deepEqual(JSON.parse(JSON.stringify(direct)), JSON.parse(JSON.stringify({ ironie_detectee: lot.ironie_detectee, figure_detectee: lot.figure_detectee, antiphrase: lot.antiphrase, journal_sigma: lot.journal_sigma })));
  assert.deepEqual(JSON.parse(JSON.stringify(a.pec)), JSON.parse(JSON.stringify(lot.pec)));
});

test('la démo intégrée (texte factuel sur l’IA) reste sans ironie', () => {
  const texte = A.get('DEMO_TEXTE');
  const r = postTraiter(clone(A.get('DEMO_ANALYSE')), texte);
  assert.equal(r.ironie_detectee, false);
  assert.equal(r.figure_detectee.length, 0);
});

// ---------- cas du corpus : POL-25 (antiphrase) et IA-40 (contrôle négatif) ----------
// Déposer dans tests/fixtures/ un export du traitement par lot (« Exporter en JSON ») qui contient ces textes.
// On y rejoue les contrôles déterministes ; les tests sont sautés tant que l'export manque.

function chercherCas(id){
  const dir = path.join(__dirname, 'fixtures');
  if(!fs.existsSync(dir)) return null;
  for(const f of fs.readdirSync(dir).filter(f => f.endsWith('.json'))){
    const d = JSON.parse(fs.readFileSync(path.join(dir, f), 'utf8'));
    const liste = Array.isArray(d) ? d : [d];
    const c = liste.find(x => x && String(x.id || '').startsWith(id));
    if(c) return c;
  }
  return null;
}
// remet une entrée exportée dans l'état où le modèle l'avait rendue (on annule les bascules déjà appliquées)
function versSortieModele(c){
  const a = clone(c);
  (a.pec || []).forEach(p => {
    if(p.adhesion_avant_inversion){ p.adhesion = p.adhesion_avant_inversion; p.fonction = p.fonction_avant_inversion; }
    if(p.source_avant_polyphonie){ p.source = p.source_avant_polyphonie; p.adhesion = p.adhesion_avant_polyphonie; }
    if(p.portee_avant_polyphonie) p.portee = p.portee_avant_polyphonie;
  });
  a.pec = (a.pec || []).filter(p => !p.ajout_antiphrase);
  return a;
}

const POL25 = chercherCas('POL-25');
// un export antérieur au prompt « orientation / hyperbole » ne permet pas de juger l'inversion (pas d'ajout orienté)
const pol25AuPromptActuel = POL25 && (POL25.operations || []).some(o => o.orientation != null);

test('POL-25 : la réplique « Vous avez tout raté… » n’est plus locuteur/totale (polyphonie)',
  { skip: POL25 ? false : 'tests/fixtures/ ne contient pas d’export de POL-25' }, () => {
  const r = postTraiter(versSortieModele(POL25), POL25.texte);
  const replique = r.pec.find(p => /vous avez tout rat/i.test(p.text || ''));
  assert.ok(replique, 'aucune entrée σ ne porte « Vous avez tout raté »');
  assert.ok(!(replique.source === 'locuteur' && replique.adhesion === 'totale'),
            `réplique encore ${replique.source}/${replique.adhesion}`);
  // pas de doublon locuteur/feinte ajouté sur la réplique du banquier
  assert.equal(r.pec.filter(p => /vous avez tout rat/i.test(p.text || '')).length, 1);
});

test('POL-25 : « Si j’ai bien compris… » feinte, ironie_detectee, figure antiphrase',
  { skip: !POL25 ? 'tests/fixtures/ ne contient pas d’export de POL-25'
        : !pol25AuPromptActuel ? 'export de POL-25 antérieur au prompt orientation/hyperbole : relancer POL-25 dans l’analyseur et déposer l’export'
        : false }, () => {
  const r = postTraiter(versSortieModele(POL25), POL25.texte);
  assert.equal(r.ironie_detectee, true, r.journal_sigma.join('\n'));
  assert.ok(r.figure_detectee.includes('antiphrase'));
  const cadre = r.pec.find(p => /si j['’]ai bien compris/i.test(p.text || ''));
  assert.ok(cadre, 'aucune entrée σ ne porte « Si j’ai bien compris »');
  assert.equal(cadre.adhesion, 'feinte');
});

const IA40 = chercherCas('IA-40');
test('IA-40 (reportage factuel) : ironie_detectee reste false',
  { skip: IA40 ? false : 'tests/fixtures/ ne contient pas d’export de IA-40' }, () => {
  const r = postTraiter(versSortieModele(IA40), IA40.texte);
  assert.equal(r.ironie_detectee, false, r.journal_sigma.join('\n'));
});
