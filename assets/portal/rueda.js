(() => {
'use strict';
/* Rueda de procesos misionales · Portal V2.1
   Lee el catálogo que carga portal.js (evento "catalogo") y dibuja:
   - 4 cuadrantes misionales con los colores del mapa de procesos UESVALLE
   - anillo exterior con eventos y tableros transversales
   - panel lateral con los tableros de la opción seleccionada */
const NS = 'http://www.w3.org/2000/svg';
const C0 = 320, R = 188, G = 6;
const esc = v => String(v ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const fmt = new Intl.NumberFormat('es-CO');
const fecha = v => { if(!v) return ''; const [y,m,d] = v.split('-'); return `${d}/${m}/${y}`; };
const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;

/* colores del mapa de procesos institucional */
const Q = {
  ach:{fill:'#79dde2', ink:'#0c5d66', pos:'tl', l:['Agua para Consumo Humano','y Saneamiento Básico']},
  zoo:{fill:'#79a22c', ink:'#ffffff', pos:'tr', l:['Zoonosis y Enfermedades','de Transmisión Vectorial']},
  aym:{fill:'#0b3480', ink:'#ffffff', pos:'bl', l:['Alimentos y','Medicamentos']},
  eis:{fill:'#f29120', ink:'#ffffff', pos:'br', l:['Establecimientos','de Interés Sanitario']}
};
const ICON = {
  ach:'<path d="M12 3.5s-6 6.6-6 11a6 6 0 0 0 12 0c0-4.4-6-11-6-11z"/><path d="M9.5 15a2.5 2.5 0 0 0 2.5 2.5"/>',
  zoo:'<circle cx="6.5" cy="10.5" r="1.8"/><circle cx="10" cy="6" r="1.8"/><circle cx="14" cy="6" r="1.8"/><circle cx="17.5" cy="10.5" r="1.8"/><path d="M12 12c-2.5 0-5 3.4-5 5.4 0 1.6 1.5 2.5 3 2l2-.6 2 .6c1.5.5 3-.4 3-2 0-2-2.5-5.4-5-5.4z"/>',
  aym:'<path d="M7 3v7a2 2 0 0 0 2 2v9M5 3v5M9 3v5"/><path d="M17 21V3c-2.2 1.6-3.2 4.2-3.2 7.2V13H17"/>',
  eis:'<path d="M4 21V8l8-4.5L20 8v13"/><path d="M9 21v-5h6v5M8 10.5h2M14 10.5h2"/>',
  lock:'<rect x="5" y="10.5" width="14" height="9.5" rx="2"/><path d="M8.5 10.5V7.5a3.5 3.5 0 0 1 7 0v3"/>',
  arrow:'<path d="M5 12h13M13 6.5l5.5 5.5-5.5 5.5"/>'
};
const ico = (k, cls='') => `<svg class="${cls}" viewBox="0 0 24 24" aria-hidden="true">${ICON[k] || ''}</svg>`;

/* anillo exterior: [id, desde°, hasta°] (0° = arriba, sentido horario) */
const RING = [
  {id:'sismo2026', a0:-62, a1:62},
  {id:'nino2026', a0:78, a1:162},
  {id:'transversal', a0:198, a1:282}
];
const RING_IN = 250, RING_OUT = 284;

const pol = (r, a) => { const t = a * Math.PI / 180; return [C0 + r * Math.sin(t), C0 - r * Math.cos(t)]; };
const f = n => n.toFixed(2);
function arcSeg(ri, ro, a0, a1){
  const L = (a1 - a0) > 180 ? 1 : 0, [x0,y0] = pol(ro,a0), [x1,y1] = pol(ro,a1), [x2,y2] = pol(ri,a1), [x3,y3] = pol(ri,a0);
  return `M${f(x0)} ${f(y0)}A${ro} ${ro} 0 ${L} 1 ${f(x1)} ${f(y1)}L${f(x2)} ${f(y2)}A${ri} ${ri} 0 ${L} 0 ${f(x3)} ${f(y3)}Z`;
}
function arcLine(r, a0, a1){
  const mid = ((a0 + a1) / 2 + 360) % 360, rev = mid > 90 && mid < 270;
  const [s, e] = rev ? [a1, a0] : [a0, a1];
  const [x0,y0] = pol(r,s), [x1,y1] = pol(r,e);
  return `M${f(x0)} ${f(y0)}A${r} ${r} 0 0 ${rev ? 0 : 1} ${f(x1)} ${f(y1)}`;
}
function quadPath(pos){
  const sx = pos[1] === 'l' ? -1 : 1, sy = pos[0] === 't' ? -1 : 1;
  const x0 = C0 + sx * G, y0 = C0 + sy * G;
  const xa = x0, ya = y0 + sy * R, xb = x0 + sx * R, yb = y0;
  const sweep = (sx * sy) > 0 ? 0 : 1;
  return `M${x0} ${y0}L${xa} ${ya}A${R} ${R} 0 0 ${sweep} ${xb} ${yb}Z`;
}

let CAT = null, sel = null;

function build(cat){
  CAT = cat;
  const host = document.getElementById('rueda');
  if(!host) return;
  const proc = Object.fromEntries(cat.procesos.map(p => [p.id, p]));
  const ev = Object.fromEntries(cat.eventos.map(e => [e.id, e]));
  const count = id => cat.tableros.filter(t => t.estado === 'publicado' && (t.proceso === id)).length;
  const countRing = id => cat.tableros.filter(t => t.estado === 'publicado' && (id === 'transversal' ? t.proceso === 'transversal' : t.evento === id)).length;

  let s = `<svg viewBox="0 0 640 640" role="group" aria-label="Mapa de procesos misionales de la UESVALLE. Seleccione un proceso o un evento para ver sus tableros.">
  <defs>
    <radialGradient id="rg-core" cx="50%" cy="50%" r="50%"><stop offset="0" stop-color="#ff4f86"/><stop offset="1" stop-color="#e8185a"/></radialGradient>
    <radialGradient id="rg-halo" cx="50%" cy="50%" r="50%"><stop offset=".55" stop-color="#5fc8ff" stop-opacity=".16"/><stop offset="1" stop-color="#5fc8ff" stop-opacity="0"/></radialGradient>
    <filter id="glow" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation="4" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
  </defs>
  <circle cx="${C0}" cy="${C0}" r="316" fill="url(#rg-halo)" pointer-events="none"/>
  <g class="orbit o1"><circle cx="${C0}" cy="${C0}" r="304" fill="none" stroke="#8fd3ff" stroke-opacity=".35" stroke-width="1" stroke-dasharray="2 9"/></g>
  <g class="orbit o2"><circle cx="${C0}" cy="${C0}" r="${RING_IN - 18}" fill="none" stroke="#bfe6ff" stroke-opacity=".28" stroke-width="1.2" stroke-dasharray="26 10 4 10"/>
    <circle cx="${C0}" cy="${C0 - (RING_IN - 18)}" r="3.5" fill="#e0a33a"/><circle cx="${C0}" cy="${C0 + (RING_IN - 18)}" r="2.5" fill="#8fd3ff"/></g>
  <g class="orbit o3"><circle cx="${C0 + 304}" cy="${C0}" r="3" fill="#8fd3ff"/><circle cx="${C0 - 304}" cy="${C0}" r="2" fill="#ffffff" opacity=".7"/></g>`;

  RING.forEach((r, i) => {
    const e = r.id === 'transversal' ? {nombre:'Transversales', corto:'Transversales', color:'#6c7fd8'} : ev[r.id];
    if(!e) return;
    const n = countRing(r.id);
    const label = (r.id === 'transversal' ? 'TRANSVERSALES' : e.corto.toUpperCase()) + `  ·  ${n}`;
    s += `<g class="seg" data-kind="ring" data-id="${r.id}" tabindex="0" role="button" aria-label="${esc(e.nombre)}: ${n} tableros" style="--c:${e.color};--d:${.5 + i * .12}s">
      <path class="seg-bg" d="${arcSeg(RING_IN, RING_OUT, r.a0, r.a1)}" fill="${e.color}"/>
      <path id="rp${i}" d="${arcLine((RING_IN + RING_OUT) / 2 + 4.5, r.a0 + 4, r.a1 - 4)}" fill="none"/>
      <text class="seg-t"><textPath href="#rp${i}" startOffset="50%" text-anchor="middle">${esc(label)}</textPath></text></g>`;
  });

  Object.entries(Q).forEach(([id, q], i) => {
    const p = proc[id]; if(!p) return;
    const sx = q.pos[1] === 'l' ? -1 : 1, sy = q.pos[0] === 't' ? -1 : 1;
    const cx = C0 + sx * R * .53, cy = C0 + sy * R * .5;
    const n = count(id);
    const top = sy < 0;
    const icy = top ? cy + 4 : cy - 4;
    const ly = top ? icy + 42 : icy - 50;
    const lx = C0 + sx * 106;
    const ny = top ? icy - 34 : icy + 44;
    s += `<g class="quad" data-kind="proc" data-id="${id}" tabindex="0" role="button" aria-label="${esc(p.nombre)}: ${n} tableros" style="--c:${q.fill};--dx:${sx * 9}px;--dy:${sy * 9}px;--d:${.1 + i * .1}s"><g class="q-in">
      <path class="q-bg" d="${quadPath(q.pos)}" fill="${q.fill}"/>
      <text class="q-t" x="${lx}" y="${ly}" text-anchor="middle" fill="${q.ink}">${q.l.map((l,j) => `<tspan x="${lx}" dy="${j ? 15 : 0}">${esc(l)}</tspan>`).join('')}</text>
      <circle cx="${cx}" cy="${icy}" r="24" fill="#fff" opacity=".96"/>
      <g class="q-ic" transform="translate(${cx - 14} ${icy - 14}) scale(${28 / 24})" style="color:${id === 'ach' ? '#0c5d66' : q.fill}">${ICON[id]}</g>
      <text class="q-n" x="${cx}" y="${ny}" text-anchor="middle" fill="${q.ink}">${n ? `${n} tablero${n > 1 ? 's' : ''}` : 'Próximamente'}</text></g></g>`;
  });

  const S = 104, K = 15;
  s += `<g class="core" tabindex="0" role="button" aria-label="Ver todos los procesos">
    <path d="M${C0} ${C0 - S}Q${C0 + K} ${C0 - K} ${C0 + S} ${C0}Q${C0 + K} ${C0 + K} ${C0} ${C0 + S}Q${C0 - K} ${C0 + K} ${C0 - S} ${C0}Q${C0 - K} ${C0 - K} ${C0} ${C0 - S}Z" fill="url(#rg-core)" filter="url(#glow)"/>
    <text x="${C0}" y="${C0 - 4}" text-anchor="middle" class="core-t">Procesos</text>
    <text x="${C0}" y="${C0 + 18}" text-anchor="middle" class="core-t">Misionales</text></g></svg>`;

  host.innerHTML = s;
  host.querySelectorAll('[data-kind]').forEach(g => {
    const go = () => select(g.dataset.kind, g.dataset.id);
    g.addEventListener('click', go);
    g.addEventListener('keydown', e => { if(e.key === 'Enter' || e.key === ' '){ e.preventDefault(); go(); } });
    g.addEventListener('mouseenter', () => host.classList.add('hovering'));
    g.addEventListener('mouseleave', () => host.classList.remove('hovering'));
  });
  const core = host.querySelector('.core');
  const reset = () => select(null, null);
  core.addEventListener('click', reset);
  core.addEventListener('keydown', e => { if(e.key === 'Enter' || e.key === ' '){ e.preventDefault(); reset(); } });
  const q = document.getElementById('q');
  if(q){
    q.addEventListener('input', () => {
      const v = norm(q.value.trim());
      if(v.length < 2){ select(sel && sel.kind, sel && sel.id, true); return; }
      buscar(v);
    });
  }
  select(null, null);
}

const norm = v => String(v ?? '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
function buscar(v){
  const host = document.getElementById('rueda');
  host.classList.remove('has-sel');
  host.querySelectorAll('[data-kind]').forEach(g => g.classList.remove('on'));
  const hay = t => {
    const p = CAT.procesos.find(x => x.id === t.proceso), e = CAT.eventos.find(x => x.id === t.evento);
    return norm([t.titulo, t.descripcion, t.tipo, p ? p.nombre + ' ' + p.corto : 'transversal', e ? e.nombre : ''].join(' ')).includes(v);
  };
  const ts = CAT.tableros.filter(hay).sort((a,b) => (a.estado === b.estado ? (b.publicado || '').localeCompare(a.publicado || '') : a.estado === 'publicado' ? -1 : 1));
  const panel = document.getElementById('rueda-panel');
  panel.style.setProperty('--c', '#e0a33a');
  panel.innerHTML = `<span class="p-eye">Búsqueda</span>
    <h2>${ts.length} resultado${ts.length === 1 ? '' : 's'}</h2>
    <div class="r-list">${ts.length ? ts.map(t => row(t, 'search')).join('') : '<p class="p-desc">Ningún tablero coincide. Pruebe con otra palabra o seleccione un proceso en la rueda.</p>'}</div>`;
}

function row(t, ctx){
  const p = CAT.procesos.find(x => x.id === t.proceso);
  const e = CAT.eventos.find(x => x.id === t.evento);
  const tags = [];
  if(ctx !== 'ring' && e) tags.push(`<span class="pt" style="--c:${e.color}">${esc(e.corto)}</span>`);
  if(ctx === 'ring' || ctx === 'search') tags.push(p ? `<span class="pt" style="--c:${Q[p.id] ? Q[p.id].fill : p.color}">${esc(p.corto)}</span>` : '<span class="pt" style="--c:#6c7fd8">Transversal</span>');
  if(t.tipo !== 'Tablero') tags.push(`<span class="pt ghost">${esc(t.tipo)}</span>`);
  const nuevo = t.publicado && (Date.now() - new Date(t.publicado + 'T12:00:00')) / 864e5 <= 15;
  if(nuevo) tags.push('<span class="pt new">Nuevo</span>');
  const meta = t.estado === 'publicado' ? [t.version, t.publicado ? fecha(t.publicado) : ''].filter(Boolean).join(' · ') : 'En preparación';
  const inner = `<span class="r-main"><b>${esc(t.titulo)}</b><span class="r-tags">${tags.join('')}</span></span>
    <span class="r-meta">${t.requiere_clave ? `<span class="r-lock" title="Requiere clave">${ico('lock')}</span>` : ''}${esc(meta)}</span>
    ${t.estado === 'publicado' ? `<span class="r-go">${ico('arrow')}</span>` : ''}`;
  return t.estado === 'publicado'
    ? `<a class="r-row" href="${esc(t.url)}">${inner}</a>`
    : `<div class="r-row soon">${inner}</div>`;
}

function select(kind, id, keepQuery){
  sel = id ? {kind, id} : null;
  const q = document.getElementById('q');
  if(q && !keepQuery) q.value = '';
  const host = document.getElementById('rueda');
  host.classList.toggle('has-sel', !!sel);
  host.querySelectorAll('[data-kind]').forEach(g => {
    const on = sel && g.dataset.kind === kind && g.dataset.id === id;
    g.classList.toggle('on', !!on);
    g.setAttribute('aria-pressed', on ? 'true' : 'false');
  });
  const panel = document.getElementById('rueda-panel');
  const order = (a, b) => (a.estado === b.estado ? (b.publicado || '').localeCompare(a.publicado || '') : a.estado === 'publicado' ? -1 : 1);

  if(!sel){
    const recientes = CAT.tableros.filter(t => t.estado === 'publicado').sort(order).slice(0, 5);
    panel.style.setProperty('--c', '#e0a33a');
    panel.innerHTML = `<span class="p-eye">Mapa de procesos</span>
      <h2>Explore los tableros por proceso</h2>
      <p class="p-desc">Seleccione un proceso misional en la rueda o un evento del anillo exterior para ver sus tableros.</p>
      <h3>Publicados recientemente</h3>
      <div class="r-list">${recientes.map(t => row(t, 'all')).join('')}</div>`;
  } else if(kind === 'proc'){
    const p = CAT.procesos.find(x => x.id === id);
    const ts = CAT.tableros.filter(t => t.proceso === id).sort((a,b) => (a.evento ? 1 : 0) - (b.evento ? 1 : 0) || order(a,b));
    panel.style.setProperty('--c', Q[id].fill);
    panel.innerHTML = `<span class="p-eye">Proceso misional</span>
      <h2>${esc(p.nombre)}</h2>
      <p class="p-desc">${esc(p.descripcion)}</p>
      <div class="p-kpi"><div><b>${fmt.format(p.poa_2026)}</b><span>actividades en el POA 2026</span></div>
        <div><b>${ts.filter(t => t.estado === 'publicado').length}</b><span>tableros publicados</span></div></div>
      <div class="r-list">${ts.length ? ts.map(t => row(t, 'proc')).join('') : '<div class="r-row soon"><span class="r-main"><b>Próximamente</b><span class="p-desc">Los tableros de este proceso se publicarán aquí.</span></span></div>'}</div>`;
  } else {
    const e = id === 'transversal'
      ? {nombre:'Tableros transversales', descripcion:'Tableros que apoyan a todos los procesos o a la gestión institucional.', color:'#6c7fd8'}
      : CAT.eventos.find(x => x.id === id);
    const ts = CAT.tableros.filter(t => id === 'transversal' ? t.proceso === 'transversal' : t.evento === id).sort(order);
    panel.style.setProperty('--c', e.color);
    panel.innerHTML = `<span class="p-eye">${id === 'transversal' ? 'Transversales' : 'Evento'}</span>
      <h2>${esc(e.nombre)}</h2>
      <p class="p-desc">${esc(e.descripcion)}</p>
      <div class="r-list">${ts.map(t => row(t, 'ring')).join('')}</div>`;
  }
  panel.classList.remove('swap'); void panel.offsetWidth; if(!reduce) panel.classList.add('swap');
}

window.addEventListener('catalogo', e => build(e.detail));
})();
