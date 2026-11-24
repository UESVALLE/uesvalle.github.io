(() => {
'use strict';
/* Portal V2.2 · carga el catálogo, pinta las cifras del encabezado y el pie,
   y entrega el catálogo a rueda.js (evento "catalogo"). */
const CATALOGO = 'data/portal/catalogo_tableros.json';
const $ = s => document.querySelector(s);
const esc = v => String(v ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const fecha = v => { if(!v) return ''; const [y,m,d] = v.split('-'); return `${d}/${m}/${y}`; };

function render(C){
  const pub = C.tableros.filter(t => t.estado === 'publicado');
  const ult = pub.map(t => t.publicado).filter(Boolean).sort().pop();
  $('#stats').innerHTML = [
    [pub.length, 'tableros publicados'],
    [C.procesos.length, 'procesos misionales'],
    [C.eventos.length, 'eventos atendidos'],
    [fecha(ult), 'última publicación']
  ].map(([n,l]) => `<div class="stat"><b>${esc(n)}</b><span>${esc(l)}</span></div>`).join('');
  $('#footMeta').innerHTML = `<b>${esc(C.version)}</b> · catálogo ${fecha(C.actualizado)}<br>Procesos según ${esc(C.fuente_procesos)}`;
}

fetch(CATALOGO + '?v=' + Date.now())
  .then(r => { if(!r.ok) throw new Error(); return r.json(); })
  .then(C => { render(C); window.dispatchEvent(new CustomEvent('catalogo', {detail: C})); })
  .catch(() => {
    $('#rueda-panel').innerHTML = '<p class="p-desc">No se pudo cargar el catálogo de tableros. Abra el portal desde https://uesvalle.github.io/ o con el servidor local.</p>';
  });
})();
