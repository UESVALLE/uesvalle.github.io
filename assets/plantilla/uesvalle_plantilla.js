/* =============================================================================
   PLANTILLA DE TABLEROS UESVALLE · v1.1 · comportamiento común
   Uso en cada tablero (antes del JS propio):
     <script src="../../assets/plantilla/uesvalle_plantilla.js?v=1.0"></script>
     UESPlantilla.init({ raiz:'../../', proceso:'eis', evento:'sismo2026', tablero:'alojamientos_temporales' });
   - Barra de procesos: se arma con data/portal/catalogo_tableros.json (el mismo del portal).
     Si el catálogo no está disponible, muestra los procesos con enlace al portal.
   - Pestañas: botones .tabs [data-tab] y secciones .module[data-mod].
   - Filtros activos: UESPlantilla.activos(elemento, [{texto, quitar}], limpiarTodo)
   ============================================================================= */
(() => {
'use strict';
const PROCESOS = [
  {id:'ach', n:'1', nombre:'Agua para consumo humano y saneamiento básico', corto:'Agua y saneamiento', c:'var(--p-ach)'},
  {id:'aym', n:'2', nombre:'Alimentos y medicamentos', corto:'Alimentos y medicamentos', c:'var(--p-aym)'},
  {id:'zoo', n:'3', nombre:'Zoonosis y ETV', corto:'Zoonosis y ETV', c:'var(--p-zoo)'},
  {id:'eis', n:'4', nombre:'Establecimientos de interés sanitario', corto:'EIS', c:'var(--p-eis)'}
];
const esc = v => String(v ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const CHEV = '<svg viewBox="0 0 24 24" class="ico" aria-hidden="true"><path d="M6 9l6 6 6-6"/></svg>';
let CFG = {};

function menuItems(cat, filtro){
  const ts = cat.tableros.filter(filtro);
  if(!ts.length) return '<span>Próximamente</span>';
  return ts.map(t => t.estado === 'publicado'
    ? `<a href="${esc(CFG.raiz + t.url)}" class="${t.id === CFG.tablero ? 'here' : ''}"${t.id === CFG.tablero ? ' aria-current="page"' : ''}>${esc(t.titulo)}<small>${esc([t.version, t.publicado ? 'publicado ' + t.publicado.split('-').reverse().join('/') : ''].filter(Boolean).join(' · '))}</small></a>`
    : `<span>${esc(t.titulo)} · próximamente</span>`).join('');
}

function buildNav(cat){
  const nav = document.getElementById('procnav');
  if(!nav) return;
  const items = PROCESOS.map(p => ({key:p.id, label:`${p.n}. ${p.corto}`, title:p.nombre, c:p.c, cur:p.id === CFG.proceso,
    html: cat ? menuItems(cat, t => t.proceso === p.id) : `<a href="${esc(CFG.raiz)}index.html">Ver en el portal de tableros</a>`}));
  if(cat && cat.eventos) cat.eventos.forEach(e => items.push({key:e.id, label:e.corto, title:e.nombre, c:e.color, cur:e.id === CFG.evento,
    html: menuItems(cat, t => t.evento === e.id)}));
  nav.innerHTML = `<div class="in"><span class="lbl">Procesos</span>${items.map(it => `
    <div class="pn-item${it.cur ? ' cur' : ''}" style="--c:${it.c}">
      <button type="button" class="pn-btn" aria-expanded="false" title="${esc(it.title)}"><i></i>${esc(it.label)}${CHEV}</button>
      <div class="pn-menu" role="menu">${it.html}</div></div>`).join('')}</div>`;
  nav.querySelectorAll('.pn-item').forEach(it => {
    const b = it.querySelector('.pn-btn');
    b.addEventListener('click', e => { e.stopPropagation(); const o = !it.classList.contains('open'); closeMenus(); it.classList.toggle('open', o); b.setAttribute('aria-expanded', o); });
  });
}
function closeMenus(){ document.querySelectorAll('.pn-item.open').forEach(i => { i.classList.remove('open'); i.querySelector('.pn-btn').setAttribute('aria-expanded','false'); }); }

function initTabs(){
  const bar = document.querySelector('.tabs[role="tablist"]');
  if(!bar) return;
  document.body.classList.add('tabbed');
  const btns = [...bar.querySelectorAll('[data-tab]')];
  const pick = (id, scroll) => {
    if(!btns.some(b => b.dataset.tab === id)) id = btns[0].dataset.tab;
    btns.forEach(b => { const on = b.dataset.tab === id; b.setAttribute('aria-selected', on); b.tabIndex = on ? 0 : -1; });
    document.querySelectorAll('.module[data-mod]').forEach(m => m.classList.toggle('on', m.dataset.mod === id));
    if(history.replaceState) history.replaceState(null, '', location.pathname + location.search + '#' + id);
    if(scroll) bar.scrollIntoView({behavior:'smooth', block:'start'});
    document.dispatchEvent(new CustomEvent('uesv:tab', {detail:id}));
  };
  btns.forEach((b, i) => {
    b.addEventListener('click', () => pick(b.dataset.tab));
    b.addEventListener('keydown', e => {
      const d = e.key === 'ArrowRight' ? 1 : e.key === 'ArrowLeft' ? -1 : 0;
      if(d){ e.preventDefault(); const n = btns[(i + d + btns.length) % btns.length]; n.focus(); pick(n.dataset.tab); }
    });
  });
  pick((location.hash || '').replace('#', '').split('?')[0] || btns[0].dataset.tab);
  window.UESPlantilla.tab = pick;
}

function activos(el, items, limpiarTodo){
  if(!el) return;
  el.innerHTML = `<b>Filtros activos</b>` + (items.length
    ? items.map((it, i) => `<span class="chip-f">${esc(it.texto)}<button type="button" data-i="${i}" aria-label="Quitar filtro ${esc(it.texto)}">×</button></span>`).join('') + `<button type="button" class="clear-all">Limpiar filtros</button>`
    : '<span class="none">Sin filtros aplicados</span>');
  el.querySelectorAll('.chip-f button').forEach(b => b.onclick = () => items[+b.dataset.i].quitar());
  const all = el.querySelector('.clear-all'); if(all) all.onclick = limpiarTodo;
}

window.UESPlantilla = {
  init(cfg){
    CFG = Object.assign({raiz:'../../'}, cfg);
    document.addEventListener('click', closeMenus);
    document.addEventListener('keydown', e => { if(e.key === 'Escape') closeMenus(); });
    initTabs();
    if(!document.getElementById('procnav')) return;   // barra de procesos opcional
    fetch(CFG.raiz + 'data/portal/catalogo_tableros.json?v=' + Date.now())
      .then(r => r.ok ? r.json() : null).catch(() => null)
      .then(cat => buildNav(cat));
  },
  activos,
  tab(){}
};
})();
