(() => {
'use strict';
const DATA = '../../data/alojamientos_temporales/current/dashboard_data.json';
const GEO = 'assets/geo/valle_municipios.json';
const EVID = '../../data/alojamientos_temporales/evidencias/';
const $ = s => document.querySelector(s);
const $$ = s => Array.from(document.querySelectorAll(s));
const fmt = new Intl.NumberFormat('es-CO');
const esc = v => String(v ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const norm = v => String(v ?? '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toUpperCase().trim();
const COMP = [['agua','Agua'],['saneamiento','Saneamiento'],['alimentos','Alimentos'],['animales','Animales']];
const ESTADO = {S:'Sin observación', O:'Con observación documentada', V:'Por validar'};
const MESES = ['enero','febrero','marzo','abril','mayo','junio','julio','agosto','septiembre','octubre','noviembre','diciembre'];
const INTERNAL = new URLSearchParams(location.search).get('seguimiento') === '1';
const LABEL_OFFSET = {'El Cairo':[-30,-2],'Ansermanuevo':[30,-8],'Versalles':[-38,4],'El Dovio':[-30,12],'Ulloa':[-10,-12],'Obando':[12,4],'Restrepo':[-18,0],'Yotoco':[12,-8]};
let DB = null;

function fecha(v, larga){
  if(!v) return '—';
  const [y,m,d] = String(v).split('-').map(Number);
  return larga ? `${d} de ${MESES[m-1]} de ${y}` : `${String(d).padStart(2,'0')}/${String(m).padStart(2,'0')}/${y}`;
}
const pct = (a,b) => b ? Math.round(a/b*100) : 0;

const I = {
  people:'<circle cx="9" cy="8" r="3"/><path d="M3.5 20v-1a5.5 5.5 0 0 1 11 0v1"/><circle cx="17" cy="9" r="2.4"/><path d="M15.6 14.2a4.5 4.5 0 0 1 5.9 4.3V20"/>',
  house:'<path d="M3.5 11 12 4l8.5 7"/><path d="M5.5 9.5V20h13V9.5"/><path d="M10 20v-5h4v5"/>',
  pin:'<path d="M12 21s-6.5-6.2-6.5-11a6.5 6.5 0 0 1 13 0c0 4.8-6.5 11-6.5 11z"/><circle cx="12" cy="10" r="2.3"/>',
  family:'<circle cx="8" cy="6.5" r="2.6"/><path d="M4 20v-5.5a4 4 0 0 1 8 0V20"/><circle cx="17" cy="11" r="2"/><path d="M14 20v-2.5a3 3 0 0 1 6 0V20"/>',
  baby:'<circle cx="12" cy="10" r="5.5"/><path d="M10 9.6h.01M14 9.6h.01"/><path d="M10.4 12.3q1.6 1.2 3.2 0"/><path d="M12 4.5q1.5-1.5 3 0"/><path d="M8 20.5q4-2.6 8 0"/>',
  child:'<circle cx="12" cy="8" r="2.8"/><path d="M8 20v-3.5a4 4 0 0 1 8 0V20"/><path d="M8.5 13 6 11M15.5 13 18 11"/>',
  teen:'<circle cx="12" cy="6.5" r="2.9"/><path d="M7 21v-3a5 5 0 0 1 10 0v3"/><path d="M9.5 3.8q2.5-1.6 5 0"/>',
  young:'<circle cx="12" cy="6.3" r="3"/><path d="M6 21v-2a6 6 0 0 1 12 0v2"/><path d="M9.5 14.5 12 17l2.5-2.5"/>',
  adult:'<circle cx="12" cy="6.3" r="3"/><path d="M5.5 21v-1.5a6.5 6.5 0 0 1 13 0V21"/><path d="M12 13.2v4.5"/>',
  elder:'<circle cx="10.5" cy="5.5" r="2.7"/><path d="M10.5 9v5.5l-3 6.5M10.5 14.5l3 6.5M8 11.5h5"/><path d="M17 12.5V21M17 12.5a1.6 1.6 0 0 1 3.2 0"/>',
  unknown:'<circle cx="12" cy="12" r="8.5"/><path d="M10 9.5a2 2 0 1 1 3 1.7c-.6.4-1 .8-1 1.6M12 16h.01"/>',
  man:'<circle cx="12" cy="5.5" r="2.8"/><path d="M8.5 10.5h7v6h-1.8V21h-3.4v-4.5H8.5z"/>',
  woman:'<circle cx="12" cy="5.5" r="2.8"/><path d="M12 9.5 7.5 17.5h9z"/><path d="M10.5 17.5V21M13.5 17.5V21"/>',
  wheel:'<circle cx="10" cy="4.5" r="2"/><path d="M10 7.5v6h5l2.5 5"/><path d="M10 10.5h4"/><path d="M7 11.5a5.5 5.5 0 1 0 7.2 6.5"/>',
  heart:'<path d="M12 20s-7.5-4.6-7.5-10A4.2 4.2 0 0 1 12 7.3 4.2 4.2 0 0 1 19.5 10c0 5.4-7.5 10-7.5 10z"/>',
  hands:'<path d="M12 20s-7.5-4.6-7.5-10A4.2 4.2 0 0 1 12 7.3 4.2 4.2 0 0 1 19.5 10c0 5.4-7.5 10-7.5 10z"/><path d="M9 12h6M12 9v6"/>',
  shield:'<path d="M12 3l7.5 3v5.5c0 4.6-3.2 8.2-7.5 9.5-4.3-1.3-7.5-4.9-7.5-9.5V6z"/><path d="M8.8 12.2l2.2 2.2 4.3-4.3"/>',
  drop:'<path d="M12 3.5s-6 6.6-6 11a6 6 0 0 0 12 0c0-4.4-6-11-6-11z"/><path d="M9.5 15a2.5 2.5 0 0 0 2.5 2.5"/>',
  toilet:'<path d="M7 3.5h6v7H7z"/><path d="M4.5 10.5h15a7.5 7.5 0 0 1-6 7.3V20.5H9v-3"/>',
  food:'<path d="M7 3v7a2 2 0 0 0 2 2v9M5 3v5M9 3v5"/><path d="M17 21V3c-2.2 1.6-3.2 4.2-3.2 7.2V13H17"/>',
  camera:'<path d="M4 8.5h3l1.6-2.5h6.8L17 8.5h3v10.5H4z"/><circle cx="12" cy="13.5" r="3.3"/>',
  paw:'<circle cx="6.5" cy="10.5" r="1.8"/><circle cx="10" cy="6" r="1.8"/><circle cx="14" cy="6" r="1.8"/><circle cx="17.5" cy="10.5" r="1.8"/><path d="M12 12c-2.5 0-5 3.4-5 5.4 0 1.6 1.5 2.5 3 2l2-.6 2 .6c1.5.5 3-.4 3-2 0-2-2.5-5.4-5-5.4z"/>'
};
const ico = (k, cls='ico') => `<svg class="${cls}" viewBox="0 0 24 24" aria-hidden="true">${I[k]}</svg>`;
const COMP_ICON = {agua:'drop', saneamiento:'toilet', alimentos:'food', animales:'paw'};

function render(){
  const k = DB.kpis, P = DB.poblacion;
  $('#cutDate').textContent = fecha(DB.metadata.corte, true);
  $('#updated').innerHTML = `<i></i>Actualizado ${fecha((DB.metadata.generado || '').slice(0,10))}`;
  $('#lede').textContent = `Estado de los alojamientos temporales y albergues habilitados en el Valle del Cauca tras el ${DB.metadata.evento.charAt(0).toLowerCase()+DB.metadata.evento.slice(1)}.`;

  const kpi = (cls, icon, n, label, sub, target, extra='') => `
    <button type="button" class="kpi ${cls}" data-go="${target}">
      <span class="ic">${ico(icon)}</span>
      <span><span class="n">${n}</span><span class="l">${label}</span>${extra}<span class="s">${sub}</span><span class="go">Clic para consultar</span></span>
    </button>`;
  $('#kpis').innerHTML =
    kpi('k1','people',fmt.format(k.personas),'Personas alojadas',`en ${fmt.format(k.nucleos)} núcleos familiares${k.por_validar ? ` · ${fmt.format(k.por_validar)} por validar` : ''}`,'poblacion',
      `<span class="split" aria-hidden="true"><i class="a" style="width:${pct(k.censadas,k.personas)}%"></i><i class="b" style="width:${pct(k.por_validar,k.personas)}%"></i></span>`) +
    kpi('k2','house',k.alojamientos,'Sitios habilitados',`${k.alojamientos_temporales} alojamientos temporales y ${k.albergues} albergue${k.albergues === 1 ? '' : 's'}`,'estado') +
    kpi('k3','pin',k.municipios,'Municipios','con alojamientos, de los 42 del departamento','territorio') +
    kpi('k4','family',fmt.format(k.dependientes),'Niñas, niños, adolescentes y personas mayores',`${k.dependientes_pct} % de las personas con curso de vida registrado`,'poblacion');
  $$('.kpi[data-go]').forEach(b => b.onclick = () => UESPlantilla.tab(b.dataset.go, true));

  const n = DB.alojamientos.length;
  $('#components').innerHTML = COMP.map(([key,label]) => {
    const r = DB.condiciones_resumen[key];
    const w = x => (x/n*100).toFixed(2);
    const partes = [];
    if(r.O) partes.push(`${r.O} con observación`);
    if(r.V) partes.push(`${r.V} por validar`);
    const resto = partes.join(' y ');
    return `<div class="comp">
      <div class="t"><span class="ci">${ico(COMP_ICON[key])}</span><span>${label}</span><b>${r.S}<small> / ${n}</small></b></div>
      <div class="stack" role="img" aria-label="${label}: ${r.S} sin observación, ${r.O} con observación, ${r.V} por validar">
        ${r.S?`<i class="S" style="width:${w(r.S)}%"></i>`:''}${r.O?`<i class="O" style="width:${w(r.O)}%"></i>`:''}${r.V?`<i class="V" style="width:${w(r.V)}%"></i>`:''}
      </div>
      <div class="d">sin observación${resto?`; ${resto}`:''}</div>
    </div>`;
  }).join('');

  $('#fMun').insertAdjacentHTML('beforeend', DB.municipios.map(m => `<option>${esc(m.municipio)}</option>`).join(''));
  $('#fMun').onchange = drawRows;
  $('#fComp').onchange = drawRows;
  $('#fFoto').onchange = drawRows;
  $('#btnClear').onclick = () => { $('#fMun').value = ''; $('#fComp').value = ''; $('#fFoto').value = ''; drawRows(); };
  drawRows();

  // ---- distribución territorial: indicadores, lectura y lista por municipio
  const MUN = DB.municipios;
  const maxA = MUN.reduce((a,b) => b.alojamientos > a.alojamientos ? b : a);
  const sitioMax = DB.alojamientos.reduce((a,b) => b.personas > a.personas ? b : a);
  const top2 = [...MUN].sort((a,b) => b.personas - a.personas).slice(0,2);
  const pctTop2 = pct(top2[0].personas + top2[1].personas, k.personas);
  const nucMax = MUN.reduce((a,b) => (b.nucleos || 0) > (a.nucleos || 0) ? b : a);
  const perNuc = k.nucleos ? (k.personas / k.nucleos).toLocaleString('es-CO', {maximumFractionDigits:1}) : '—';
  const cobert = pct(k.municipios, 42);
  $('#terrKpis').innerHTML = `
    <div class="tk"><span class="tk-l">Municipios con sitios</span><b>${k.municipios}<small> de 42</small></b>
      <span class="tk-bar" aria-hidden="true"><i style="width:${cobert}%"></i></span><span class="tk-s">${cobert} % del departamento</span></div>
    <div class="tk"><span class="tk-l">Sitios habilitados</span><b>${k.alojamientos}</b>
      <span class="tk-s">${k.alojamientos_temporales} alojamientos temporales y ${k.albergues} albergue${k.albergues === 1 ? '' : 's'}</span></div>
    <div class="tk"><span class="tk-l">Núcleos familiares</span><b>${fmt.format(k.nucleos)}</b>
      <span class="tk-s">${perNuc} personas por núcleo en promedio</span></div>
    <div class="tk"><span class="tk-l">Concentración</span><b>${pctTop2} %</b>
      <span class="tk-s">de las personas está en ${esc(top2[0].municipio)} y ${esc(top2[1].municipio)}</span></div>`;
  $('#terrLede').innerHTML = `<b>${esc(maxA.municipio)}</b> concentra ${maxA.alojamientos} de los ${k.alojamientos} sitios. `
    + `<b>${esc(sitioMax.municipio)}</b> tiene el sitio con mayor número de personas (${fmt.format(sitioMax.personas)}${sitioMax.tipo === 'Albergue' ? ', albergue' : ''}). `
    + `${esc(nucMax.municipio)} reúne más núcleos familiares (${nucMax.nucleos}).`;
  const maxM = Math.max(...MUN.map(m => m.personas));
  if($('#lgPv')) $('#lgPv').hidden = !k.por_validar;
  $('#munBars').innerHTML = `<div class="mrow mhead" role="row"><span role="columnheader">Municipio</span><span role="columnheader"></span><span class="n" role="columnheader">Personas</span><span class="n" role="columnheader">Núcleos</span><span class="n" role="columnheader">Sitios</span></div>`
    + MUN.map(m => `
    <div class="mrow bar clk" data-mun="${esc(m.municipio)}" role="row" tabindex="0" title="${esc(m.municipio)}: ${m.personas} personas, ${m.nucleos ?? '—'} núcleos familiares, ${m.alojamientos} sitio(s). Clic para ver sus sitios">
      <span class="lb" role="cell">${esc(m.municipio)}</span>
      <span class="tr" role="cell" aria-hidden="true"><i class="a" style="width:${m.censadas/maxM*100}%"></i><i class="b" style="width:${m.por_validar/maxM*100}%"></i></span>
      <b class="n" role="cell">${fmt.format(m.personas)}</b>
      <span class="n" role="cell">${m.nucleos ?? '—'}</span>
      <span class="n" role="cell">${m.alojamientos}</span>
    </div>`).join('')
    + `<div class="mrow mtot" role="row"><span role="cell">Total</span><span role="cell"></span><b class="n" role="cell">${fmt.format(k.personas)}</b><b class="n" role="cell">${fmt.format(k.nucleos)}</b><b class="n" role="cell">${k.alojamientos}</b></div>`;

  // población
  $('#pobLede').textContent = `${fmt.format(P.censadas)} personas caracterizadas individualmente en ${P.municipios} municipios${P.pendientes ? `; ${P.pendientes} aún pendientes de clasificación por curso de vida y aseguramiento` : ''}.`;
  const LIFE = [['Pendiente','unknown','Pendiente de clasificación'],['Primera','baby','Primera infancia'],['Infancia','child','Infancia'],['Adolesc','teen','Adolescencia'],['Joven','young','Juventud'],['Adultez','adult','Adultez'],['Persona mayor','elder','Personas mayores'],['S/D','unknown','Sin dato']];
  const maxC = Math.max(...P.curso_vida.map(x => x.personas));
  $('#courseBars').innerHTML = P.curso_vida.map(x => {
    const L = LIFE.find(l => x.grupo.startsWith(l[0])) || ['', 'unknown', x.grupo];
    const edad = ((x.grupo.match(/\(([^)]+)\)/)||[])[1] || '').replace(' años o más','+').replace(' años','');
    const dep = /Primera|Infancia|Adolesc|Persona mayor/.test(x.grupo);
    return `<div class="life-row ${dep?'dep':''}${x.grupo.startsWith('Pendiente')?' pend':''}" title="${esc(x.grupo)}">
      <span class="ib">${ico(L[1])}</span>
      <span><span class="nm">${L[2]}<small>${esc(edad)}</small></span><span class="tr" style="display:block"><i style="width:${x.personas/maxC*100}%"></i></span></span>
      <b class="v">${fmt.format(x.personas)}</b></div>`;
  }).join('');
  const h = P.sexo.hombres, mu = P.sexo.mujeres, ph = pct(h,h+mu);
  $('#sex').innerHTML = `<div class="sexcards">
      <div class="sexc">${ico('man')}<div><b>${h}</b><span>Hombres · ${ph} %</span></div></div>
      <div class="sexc m">${ico('woman')}<div><b>${mu}</b><span>Mujeres · ${100-ph} %</span></div></div></div>`;
  const GI = {'Personas con discapacidad':['wheel','#2e6f9e'],'Afrocolombianas':['people','#8a5a2b'],'Indígenas':['people','#2f8a86'],'Gestantes':['heart','#b8567f']};
  $('#groups').innerHTML = P.interes.map(g => { const [ic,c] = GI[g.grupo] || ['people','#1f4e79'];
    return `<div class="gcard" style="--c:${c}"><span class="ib">${ico(ic)}</span><div><b>${fmt.format(g.personas)}</b><span>${esc(g.grupo)}</span></div></div>`; }).join('');
  $('#insured').innerHTML = `${ico('shield')}<div><b>${P.asegurados_pct} %</b><span>con afiliación en salud · ${P.no_asegurados} sin afiliación registrada${P.pendientes ? ` · ${P.pendientes} pendientes de clasificación` : ''}</span></div>`;
  const maxE = Math.max(...P.aseguramiento.map(x => x.personas));
  $('#epsBars').innerHTML = P.aseguramiento.map(x => `
    <div class="bar"><span class="lb">${esc(x.eps)}</span>
      <span class="tr"><i class="${x.eps.startsWith('Pendiente') ? 'b' : 'c'}" style="width:${x.personas/maxE*100}%"></i></span>
      <b class="v">${fmt.format(x.personas)}</b></div>`).join('');

  $('#method').innerHTML = DB.metodologia.map(t => `<li>${esc(t)}</li>`).join('');
  $('#src').innerHTML = `${esc(DB.metadata.fuente_publica)} · corte ${fecha(DB.metadata.corte)} · ${esc(DB.metadata.version)}`;
  $('#btnPrint').onclick = () => window.print();

  // clic en una barra municipal: filtra el estado de los alojamientos (filtro cruzado)
  $$('#munBars .mrow.clk').forEach(el => {
    const go = () => filtrarMunicipio(el.dataset.mun);
    el.onclick = go; el.onkeydown = e => { if(e.key === 'Enter' || e.key === ' '){ e.preventDefault(); go(); } };
  });
  $('#carga').innerHTML = [
    ['Fuente', DB.metadata.fuente_publica],
    ['Corte de la información', fecha(DB.metadata.corte)],
    ['Datos generados', fecha((DB.metadata.generado || '').slice(0,10)) + ' ' + (DB.metadata.generado || '').slice(11,16)],
    ['Registros', `${DB.alojamientos.length} alojamientos · ${k.fotos || 0} fotografías`]
  ].map(([l,v]) => `<div>${esc(l)}<b>${esc(v)}</b></div>`).join('');

  if(INTERNAL && DB.seguimiento){ $('#tabInterno').hidden = false; renderInternal(); }
  bindModal();
  drawMap();
}

function filtrarMunicipio(m){
  $('#fMun').value = m; drawRows(); UESPlantilla.tab('estado', true);
}
function pintarActivos(){
  const items = [];
  const fm = $('#fMun'), fc = $('#fComp'), ff = $('#fFoto');
  if(fm.value) items.push({texto:`Municipio: ${fm.value}`, quitar:() => { fm.value = ''; drawRows(); }});
  if(fc.value) items.push({texto:fc.options[fc.selectedIndex].text, quitar:() => { fc.value = ''; drawRows(); }});
  if(ff.value) items.push({texto:ff.options[ff.selectedIndex].text, quitar:() => { ff.value = ''; drawRows(); }});
  UESPlantilla.activos($('#activos'), items, () => { fm.value = ''; fc.value = ''; ff.value = ''; drawRows(); });
}
function drawRows(){
  const fm = $('#fMun').value, fc = $('#fComp').value, ff = $('#fFoto').value;
  const nf = a => (a.fotos || []).length;
  const rows = DB.alojamientos.filter(a => (!fm || a.municipio === fm) && (!fc || a.condiciones[fc].estado === 'O') && (!ff || (ff === 'con' ? nf(a) > 0 : nf(a) === 0)));
  $('#count').textContent = `${rows.length} de ${DB.alojamientos.length} alojamientos`;
  pintarActivos();
  if(!rows.length){ $('#rows').innerHTML = `<tr><td colspan="8" class="empty">Ningún alojamiento cumple el filtro. Cambie los filtros o use Limpiar.</td></tr>`; return; }
  let prev = null;
  $('#rows').innerHTML = rows.map(a => {
    const first = a.municipio !== prev; prev = a.municipio;
    const occ = a.ocupacion_pct != null
      ? `<div class="occ"><span class="tr"><i style="width:${Math.min(100,a.ocupacion_pct)}%"></i></span>${a.ocupacion_pct} %</div>`
      : `<span class="occ">—</span>`;
    return `<tr class="${first?'grp':''}" data-id="${esc(a.id)}" tabindex="0" aria-label="Ver ficha de ${esc(a.nombre)}">
      <td class="mun ${first?'':'rep'}">${esc(a.municipio)}</td>
      <td class="site">${esc(a.nombre)}${a.tipo === 'Albergue' ? ' <span class="tag alb">Albergue</span>' : ''}${nf(a)?` <span class="cam" title="Registro fotográfico: ${nf(a)} foto${nf(a)>1?'s':''}" aria-label="Con registro fotográfico, ${nf(a)} foto${nf(a)>1?'s':''}">${ico('camera')}<small>${nf(a)}</small></span>`:''}${a.estado!=='En operación'?' <span class="tag pv">Estado por validar</span>':''}${a.sector?`<small class="sec">${esc(a.sector)}</small>`:''}</td>
      <td class="num" data-l="Personas"><b>${fmt.format(a.personas)}</b>${a.poblacion==='Por validar'?'<span class="tag pv">por validar</span>':''}</td>
      <td class="occ-td${a.ocupacion_pct == null ? ' nocap' : ''}" data-l="Ocupación">${occ}</td>
      ${COMP.map(([key,label]) => `<td class="c" data-l="${label}"><span class="cell ${a.condiciones[key].estado}" title="${label}: ${ESTADO[a.condiciones[key].estado]}" aria-label="${label}: ${ESTADO[a.condiciones[key].estado]}"></span></td>`).join('')}
    </tr>`;
  }).join('');
  $$('#rows tr[data-id]').forEach(tr => {
    tr.onclick = () => openFicha(tr.dataset.id);
    tr.onkeydown = e => { if(e.key === 'Enter' || e.key === ' '){ e.preventDefault(); openFicha(tr.dataset.id); } };
  });
}

function openFicha(id){
  const a = DB.alojamientos.find(x => x.id === id); if(!a) return;
  $('#modalBody').innerHTML = `
    <div class="f-head"><span class="eyebrow dark">Ficha · ${esc(a.tipo || 'Alojamiento temporal')}</span><h2 id="mTitle">${esc(a.nombre)}</h2><p>${esc(a.municipio)}${a.sector?` · ${esc(a.sector)}`:''}</p></div>
    <div class="f-grid">
      <div><span>Personas</span><b>${fmt.format(a.personas)}</b>${a.poblacion==='Por validar'?'<span class="tag pv" style="margin:4px 0 0">por validar</span>':''}</div>
      <div><span>Capacidad</span><b>${a.capacidad ?? '—'}</b></div>
      <div><span>Ocupación</span><b>${a.ocupacion_pct != null ? a.ocupacion_pct+' %' : '—'}</b></div>
      <div><span>Estado</span><b style="font-size:17px">${esc(a.estado)}</b></div>
    </div>
    <div class="f-cond">
      ${COMP.map(([key,label]) => `<div><span class="cell ${a.condiciones[key].estado}" title="${ESTADO[a.condiciones[key].estado]}"></span><b>${label}</b><span>${esc(a.condiciones[key].texto || 'Por validar.')}</span></div>`).join('')}
    </div>
    ${fotosHtml(a)}
    <div class="f-meta">
      ${a.observacion?`<p><b>Observación de campo:</b> ${esc(a.observacion)}</p>`:''}
      ${a.infraestructura?`<p><b>Infraestructura:</b> ${esc(a.infraestructura)}</p>`:''}
      ${a.direccion?`<p><b>Ubicación:</b> ${esc(a.direccion)}</p>`:''}
      <p><b>Última verificación en campo:</b> ${a.ultima_verificacion ? fecha(a.ultima_verificacion) : 'por validar'}</p>
    </div>`;
  const m = $('#modal'); m.classList.add('open'); m.setAttribute('aria-hidden','false');
  document.body.classList.add('lock');
  $$('#modalBody .th').forEach(b => b.onclick = () => openLightbox(a, Number(b.dataset.i)));
  $('.modal-x').focus();
}
function fotosHtml(a){
  const f = a.fotos || [];
  if(!f.length) return `<div class="f-photos empty-ph">${ico('camera')}<span>Sin registro fotográfico cargado para este alojamiento.</span></div>`;
  return `<div class="f-photos"><h3>${ico('camera')} Registro fotográfico <small>${f.length} foto${f.length>1?'s':''}</small></h3>
    <div class="gal">${f.map((x,i) => `<button type="button" class="th" data-i="${i}" aria-label="Ampliar foto ${i+1} de ${f.length}"><img loading="lazy" src="${EVID}${encodeURI(x)}" alt="Registro fotográfico ${i+1} de ${f.length} · ${esc(a.nombre)}"></button>`).join('')}</div></div>`;
}
let LB = null;
function openLightbox(a, i){
  LB = {a, i};
  const box = $('#lightbox'); box.classList.add('open'); box.setAttribute('aria-hidden','false');
  showLb();
  $('#lbClose').focus();
}
function showLb(){
  const f = LB.a.fotos, n = f.length;
  LB.i = (LB.i + n) % n;
  const img = $('#lbImg');
  img.src = EVID + encodeURI(f[LB.i]);
  img.alt = `Registro fotográfico ${LB.i+1} de ${n} · ${LB.a.nombre}`;
  $('#lbCap').textContent = `${LB.a.nombre} · ${LB.a.municipio} · foto ${LB.i+1} de ${n}`;
  $('#lbPrev').hidden = $('#lbNext').hidden = n < 2;
}
function closeLightbox(){ const b = $('#lightbox'); b.classList.remove('open'); b.setAttribute('aria-hidden','true'); LB = null; }
function closeModal(){ const m = $('#modal'); m.classList.remove('open'); m.setAttribute('aria-hidden','true'); document.body.classList.remove('lock'); }
function bindModal(){
  $$('[data-close]').forEach(x => x.onclick = closeModal);
  $$('[data-lbclose]').forEach(x => x.onclick = closeLightbox);
  $('#lbPrev').onclick = () => { LB.i--; showLb(); };
  $('#lbNext').onclick = () => { LB.i++; showLb(); };
  document.addEventListener('keydown', e => {
    if(LB){ if(e.key === 'Escape') closeLightbox(); if(e.key === 'ArrowLeft'){ LB.i--; showLb(); } if(e.key === 'ArrowRight'){ LB.i++; showLb(); } return; }
    if(e.key === 'Escape') closeModal();
  });
  let x0 = null;
  $('#lightbox').addEventListener('touchstart', e => { x0 = e.touches[0].clientX; }, {passive:true});
  $('#lightbox').addEventListener('touchend', e => {
    if(x0 === null || !LB) return; const dx = e.changedTouches[0].clientX - x0; x0 = null;
    if(Math.abs(dx) > 45){ LB.i += dx < 0 ? 1 : -1; showLb(); }
  });
}

function renderInternal(){
  $('#internal').hidden = false;
  const s = DB.seguimiento;
  $('#internalBody').innerHTML = `
    <div class="table-wrap"><table class="int-table">
      <thead><tr><th>Tipo</th><th>Municipio</th><th>Alojamiento</th><th>Detalle</th></tr></thead>
      <tbody>${s.map(x => `<tr><td>${esc(x.tipo)}</td><td>${esc(x.municipio)}</td><td>${esc(x.alojamiento)}</td><td>${esc(x.detalle)}</td></tr>`).join('')}</tbody>
    </table></div>
    <div class="int-val">${DB.validaciones.map(v => `<span>${v.ok?'✓':'✗'} ${esc(v.control)}: ${v.calculado}</span>`).join('')}
      <span>Datos generados ${esc(DB.metadata.generado.replace('T',' '))}</span></div>`;
}

// ---------- mapa (SVG local, sin servicios externos)
function drawMap(){
  fetch(GEO + '?v=4').then(r => { if(!r.ok) throw new Error('geo'); return r.json(); }).then(geo => {
    const feats = geo.features;
    let x0=Infinity,x1=-Infinity,y0=Infinity,y1=-Infinity;
    const each = (g, fn) => (g.type === 'Polygon' ? [g.coordinates] : g.coordinates).forEach(p => p.forEach(r => r.forEach(fn)));
    feats.forEach(f => each(f.geometry, ([x,y]) => { x0=Math.min(x0,x); x1=Math.max(x1,x); y0=Math.min(y0,y); y1=Math.max(y1,y); }));
    const kx = Math.cos((y0+y1)/2*Math.PI/180), W = 520, s = W/((x1-x0)*kx), H = Math.round((y1-y0)*s), pad = 8;
    const P = ([x,y]) => [pad+(x-x0)*kx*s, pad+(y1-y)*s];
    const byKey = Object.fromEntries(DB.municipios.map(m => [norm(m.municipio), m]));
    const color = v => !v ? '#e4eaef' : v > 60 ? '#173f6b' : v > 30 ? '#2f6fa8' : v > 10 ? '#6e9bc8' : '#a9c4de';
    const polys = [], labels = [];
    feats.forEach(f => {
      const m = byKey[f.properties.clave];
      const rings = f.geometry.type === 'Polygon' ? [f.geometry.coordinates] : f.geometry.coordinates;
      const d = rings.map(poly => poly.map(r => 'M' + r.map(c => P(c).map(v => v.toFixed(1)).join(',')).join('L') + 'Z').join('')).join('');
      polys.push(`<path d="${d}" fill="${color(m && m.personas)}" class="${m?'on':''}" data-mun="${m?esc(m.municipio):''}"><title>${esc(f.properties.nombre)}${m?`: ${m.personas} personas · ${m.nucleos ?? '—'} núcleos familiares · ${m.alojamientos} sitio(s)`:''}</title></path>`);
      if(m){
        let best = null, ba = 0;
        rings.forEach(poly => { const r = poly[0]; let a=0,cx=0,cy=0;
          for(let i=0,j=r.length-1;i<r.length;j=i++){ const q=r[j][0]*r[i][1]-r[i][0]*r[j][1]; a+=q; cx+=(r[j][0]+r[i][0])*q; cy+=(r[j][1]+r[i][1])*q; }
          if(Math.abs(a) > ba){ ba = Math.abs(a); best = [cx/(3*a), cy/(3*a)]; } });
        const off = LABEL_OFFSET[m.municipio] || [0,0];
        const [lx0,ly0] = P(best), lx = lx0 + off[0], ly = ly0 + off[1];
        labels.push(`<text x="${lx.toFixed(1)}" y="${ly.toFixed(1)}" text-anchor="middle">${esc(m.municipio)}</text><text class="v" x="${lx.toFixed(1)}" y="${(ly+12).toFixed(1)}" text-anchor="middle">${m.personas}</text>`);
      }
    });
    $('#map').innerHTML = `<svg viewBox="0 0 ${W+pad*2} ${H+pad*2}" role="img" aria-label="Mapa del Valle del Cauca con los ${DB.municipios.length} municipios que tienen alojamientos temporales">${polys.join('')}${labels.join('')}</svg>
      <div class="map-scale" aria-hidden="true">
        <span><i style="background:#a9c4de"></i>1 a 10</span><span><i style="background:#6e9bc8"></i>11 a 30</span>
        <span><i style="background:#2f6fa8"></i>31 a 60</span><span><i style="background:#173f6b"></i>Más de 60 personas</span>
        <span><i style="background:#e4eaef"></i>Sin alojamientos</span></div>`;
    $$('#map path.on').forEach(p => p.onclick = () => {
      filtrarMunicipio(p.dataset.mun);
    });
  }).catch(() => { $('#map').innerHTML = '<div class="map-msg">Mapa no disponible. La distribución por municipio se muestra en las barras.</div>'; });
}

UESPlantilla.init({raiz:'../../', proceso:'eis', evento:'sismo2026', tablero:'alojamientos_temporales'});

fetch(DATA + '?v=5&ts=' + Date.now())
  .then(r => { if(!r.ok) throw new Error('No se encontró dashboard_data.json'); return r.json(); })
  .then(d => { DB = d; render(); })
  .catch(err => {
    document.getElementById('sheet').innerHTML = `<div class="module" style="padding:40px"><h2>No se pudieron cargar los datos</h2><p>${esc(err.message)}.</p><p>Abra el tablero con el BAT de instalación, desde la estructura UESVALLE (servidor local, puerto 8766).</p></div>`;
  });
})();
