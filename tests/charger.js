// Charge le <script> de analyseur-grize.html dans un contexte Node, avec un DOM factice,
// pour tester les contrôles déterministes sans navigateur ni appel au modèle.
'use strict';
const fs = require('fs');
const path = require('path');
const vm = require('vm');

function factice(){
  const f = function(){ return proxy; };
  const proxy = new Proxy(f, {
    get(_, k){
      if(k === Symbol.toPrimitive) return () => '';
      if(k === 'then') return undefined;               // pas une promesse
      if(k === 'length') return 0;
      return proxy;
    },
    set(){ return true; },
    apply(){ return proxy; },
    construct(){ return proxy; }
  });
  return proxy;
}

function chargerAnalyseur(){
  const html = fs.readFileSync(path.join(__dirname, '..', 'analyseur-grize.html'), 'utf8');
  const scripts = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m => m[1]);
  if(!scripts.length) throw new Error('aucun <script> dans analyseur-grize.html');
  const dom = factice();
  const ctx = { console: { log(){}, info(){}, warn(){}, error: console.error },
                document: dom, window: dom, localStorage: dom, navigator: dom,
                setTimeout, clearTimeout, URL: dom, Blob: function(){}, fetch: () => Promise.reject(new Error('hors ligne')) };
  vm.createContext(ctx);
  // les déclarations const/let/function de premier niveau restent accessibles via runInContext
  scripts.forEach(s => vm.runInContext(s, ctx));
  return { ctx, get: nom => vm.runInContext(nom, ctx) };
}

module.exports = { chargerAnalyseur };
