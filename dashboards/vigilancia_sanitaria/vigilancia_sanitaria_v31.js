/* UESVALLE · Vigilancia Sanitaria ATI V3.1 */
(()=>{
'use strict';
const CUT='2026-09-08';
const DATA='../../data/vigilancia_sanitaria/current/';
const root=document.getElementById('ati-v31-shell');
if(!root)return;
const panel=document.getElementById('panel-ati');
const esc=v=>String(v??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));
const norm=v=>String(v??'').toLocaleLowerCase('es').normalize('NFD').replace(/[\u0300-\u036f]/g,'');
const n=v=>Number.isFinite(+v)?+v:0;
const dateVal=v=>{const d=new Date((v||'')+'T00:00:00');return isNaN(d)?null:d};
const daysSince=v=>{const d=dateVal(v),c=dateVal(CUT);return d&&c?Math.round((c-d)/86400000):null};
const fmtDate=v=>{const d=dateVal(v);return d?d.toLocaleDateString('es-CO',{day:'2-digit',month:'2-digit',year:'numeric'}):'Sin fecha'};
const statusClass=s=>{s=norm(s);if(s.includes('cerrado'))return'closed';if(s.includes('trasladado')||s.includes('reubicado'))return'moved';if(s.includes('habilitado'))return'empty';if(s.includes('sin verificar'))return'unknown';return'active'};
let OP=[],HIST=[],GEO=[];
let listFilter={q:'',mun:'',state:''};

root.innerHTML=`
  <div class="v31-viewbar" role="tablist" aria-label="Vistas de alojamientos temporales">
    <button class="v31-viewbtn active" data-v31="panorama">Panorama diario</button>
    <button class="v31-viewbtn" data-v31="mapa">Mapa</button>
    <button class="v31-viewbtn" data-v31="listado">Listado</button>
    <button class="v31-viewbtn" data-v31="diagnostico">Diagnóstico sanitario</button>
  </div>
  <section class="v31-panel active" data-v31-panel="panorama"><div class="v31-note">Cargando estado operacional…</div></section>
  <section class="v31-panel" data-v31-panel="mapa"></section>
  <section class="v31-panel" data-v31-panel="listado"></section>
  <section class="v31-panel" data-v31-panel="diagnostico"><div class="v31-diag-intro"><h3>Diagnóstico sanitario</h3><p>Esta vista conserva la ficha técnica, priorización, hallazgos y registro fotográfico del módulo original. Use los filtros que aparecen debajo.</p></div></section>`;

function switchView(name,scroll=false){
  root.querySelectorAll('[data-v31]').forEach(b=>b.classList.toggle('active',b.dataset.v31===name));
  root.querySelectorAll('[data-v31-panel]').forEach(x=>x.classList.toggle('active',x.dataset.v31Panel===name));
  panel?.classList.toggle('v31-diag-mode',name==='diagnostico');
  if(name==='listado')renderList();
  if(name==='mapa')renderMap();
  if(name==='panorama')renderPanorama();
  if(scroll)root.scrollIntoView({behavior:'smooth',block:'start'});
}
root.querySelectorAll('[data-v31]').forEach(b=>b.addEventListener('click',()=>switchView(b.dataset.v31,false)));

function currentRows(){return OP.filter(r=>r.vigencia==='Vigente')}
function statusCounts(){
  const c={};OP.forEach(r=>c[r.estado_actual]=(c[r.estado_actual]||0)+1);return c;
}
function population(){return currentRows().reduce((a,r)=>a+n(r.poblacion_actual),0)}
function statusLabel(s){const map={'Activo - ocupado':'Ocupado','Habilitado - sin ocupación':'Habilitado sin ocupación','Cerrado / desmontado':'Cerrado','Trasladado / reubicado':'Reubicado','Sin verificar':'Sin verificar'};return map[s]||s||'Sin verificar'}
function statusBadge(s){return `<span class="v31-badge ${statusClass(s)}">${esc(statusLabel(s))}</span>`}
function freshness(r){const d=daysSince(r.fecha_estado);if(d===null)return'';return d>7?`<span class="v31-badge stale">${d} días</span>`:`<span class="muted">${d===0?'Hoy':d+' días'}</span>`}

function renderPanorama(){
  const el=root.querySelector('[data-v31-panel="panorama"]');
  if(!OP.length){el.innerHTML='<div class="v31-note">No fue posible cargar el estado operacional V3.1.</div>';return}
  const c=statusCounts(), vig=currentRows().length, active=c['Activo - ocupado']||0, closed=c['Cerrado / desmontado']||0, moved=c['Trasladado / reubicado']||0, unknown=c['Sin verificar']||0, empty=c['Habilitado - sin ocupación']||0;
  const categories=[['Ocupados',active],['Habilitados sin ocupación',empty],['Sin verificar',unknown],['Cerrados',closed],['Reubicados',moved]];
  const max=Math.max(...categories.map(x=>x[1]),1);
  const byMun={};currentRows().forEach(r=>{const m=r.municipio||'Sin municipio';const x=byMun[m]||(byMun[m]={v:0,a:0,p:0,last:''});x.v++;if(r.estado_actual==='Activo - ocupado')x.a++;x.p+=n(r.poblacion_actual);if((r.fecha_estado||'')>x.last)x.last=r.fecha_estado||''});
  const munRows=Object.entries(byMun).sort((a,b)=>a[0].localeCompare(b[0],'es')).map(([m,x])=>`<tr><td><b>${esc(m)}</b></td><td class="num">${x.v}</td><td class="num">${x.a}</td><td class="num">${x.p}</td><td>${fmtDate(x.last)}</td></tr>`).join('');
  el.innerHTML=`
    <div class="v31-note"><strong>Corte operacional V3.1 · 08/09/2026.</strong> Se separan sitio histórico, vigencia y estado actual. <b>Cerrado</b> solo se asigna cuando existe evidencia explícita; 0 personas no equivale automáticamente a cierre. La población corresponde al último reporte disponible por sitio y <b>no es un censo simultáneo</b>.</div>
    <div class="v31-kpis">
      <button class="v31-kpi" data-go-state=""><span class="v">${vig}</span><span class="l">Alojamientos vigentes</span><span class="s">${OP.length} sitios históricos registrados</span></button>
      <button class="v31-kpi active" data-go-state="Activo - ocupado"><span class="v">${active}</span><span class="l">Ocupados</span><span class="s">Con personas en el último reporte</span></button>
      <button class="v31-kpi empty" data-go-state="Habilitado - sin ocupación"><span class="v">${empty}</span><span class="l">Habilitados sin ocupación</span><span class="s">Disponibles, actualmente vacíos</span></button>
      <button class="v31-kpi unknown" data-go-state="Sin verificar"><span class="v">${unknown}</span><span class="l">Sin verificar</span><span class="s">Requieren actualización específica</span></button>
      <button class="v31-kpi closed" data-go-state="Cerrado / desmontado"><span class="v">${closed}</span><span class="l">Cerrados</span><span class="s">Con evidencia de cierre operacional</span></button>
      <button class="v31-kpi moved" data-go-state="Trasladado / reubicado"><span class="v">${moved}</span><span class="l">Reubicados</span><span class="s">Conservados en el histórico</span></button>
    </div>
    <div class="v31-grid2">
      <div class="v31-card"><h3>Ubicación municipal de alojamientos vigentes</h3><div class="v31-table-wrap"><table class="v31-table" style="min-width:580px"><thead><tr><th>Municipio</th><th>Vigentes</th><th>Ocupados</th><th>Personas</th><th>Último seguimiento</th></tr></thead><tbody>${munRows}</tbody></table></div></div>
      <div class="v31-card"><h3>Estado operacional</h3><div class="v31-status-bars">${categories.map(([name,val])=>`<div class="v31-status-row"><span>${esc(name)}</span><div class="v31-bar"><span style="width:${Math.round(val/max*100)}%"></span></div><b>${val}</b></div>`).join('')}</div><div class="v31-source-legend"><span class="v31-source-chip">UESVALLE · diagnóstico directo</span><span class="v31-source-chip">PIC/Gobernación · complementaria</span></div><p><strong>${population()} personas</strong> en la suma de los últimos reportes disponibles de sitios vigentes; las fechas no son simultáneas.</p><p>El seguimiento técnico de agua y saneamiento se maneja semanalmente; el estado operacional puede actualizarse con reporte corto.</p><p><a href="${DATA}ati_operacion_v31.csv" download>Descargar estado ATI</a> · <a href="${DATA}manifest_actualizacion_20260908.csv" download>Descargar manifiesto del corte</a></p></div>
    </div>`;
  el.querySelectorAll('[data-go-state]').forEach(b=>b.addEventListener('click',()=>{listFilter.state=b.dataset.goState||'';switchView('listado',true)}));
}

function renderMap(){
  const el=root.querySelector('[data-v31-panel="mapa"]');
  const located=GEO.filter(r=>Number.isFinite(+r.latitud)&&Number.isFinite(+r.longitud));
  const pending=GEO.length-located.length;
  const mun=[...new Set(currentRows().map(r=>r.municipio).filter(Boolean))].sort((a,b)=>a.localeCompare(b,'es'));
  el.innerHTML=`<div class="v31-mapbox"><div><div class="map-icon">⌖</div><h3>Georreferenciación exacta de ATI</h3><p>El mapa queda preparado para coordenadas reales del alojamiento. En este corte no se usan centroides municipales ni puntos aproximados para evitar ubicar establecimientos en lugares incorrectos.</p><div class="v31-map-metrics"><span>${located.length} georreferenciados</span><span>${pending} pendientes</span><span>${mun.length} municipios con ATI vigentes</span></div></div></div>
  <div class="v31-card" style="margin-top:14px"><h3>Municipios con alojamientos vigentes</h3><p>${mun.map(x=>esc(x)).join(' · ')}</p><p>Las coordenadas se diligencian una sola vez en el maestro ATI y luego alimentan automáticamente esta vista.</p></div>`;
}

function filtered(){
  const q=norm(listFilter.q),m=listFilter.mun,s=listFilter.state;
  return OP.filter(r=>(!q||norm([r.municipio,r.establecimiento,r.ubicacion,r.direccion].join(' ')).includes(q))&&(!m||r.municipio===m)&&(!s||r.estado_actual===s));
}
function renderList(){
  const el=root.querySelector('[data-v31-panel="listado"]');
  const muns=[...new Set(OP.map(r=>r.municipio).filter(Boolean))].sort((a,b)=>a.localeCompare(b,'es'));
  const states=[...new Set(OP.map(r=>r.estado_actual).filter(Boolean))];
  const rows=filtered();
  el.innerHTML=`
    <div class="v31-note"><strong>Listado operacional y trazabilidad.</strong> Incluye sitios vigentes, cerrados y reubicados. Esto permite consultar dónde estuvieron ubicados los alojamientos sin borrar el histórico.</div>
    <div class="v31-toolbar"><label>Buscar<input id="v31-q" value="${esc(listFilter.q)}" placeholder="Municipio o alojamiento"></label><label>Municipio<select id="v31-m"><option value="">Todos</option>${muns.map(x=>`<option ${x===listFilter.mun?'selected':''}>${esc(x)}</option>`).join('')}</select></label><label>Estado<select id="v31-s"><option value="">Todos</option>${states.map(x=>`<option ${x===listFilter.state?'selected':''}>${esc(x)}</option>`).join('')}</select></label><button class="v31-reset" id="v31-reset">Limpiar</button></div>
    <div class="v31-table-wrap"><table class="v31-table"><thead><tr><th>Municipio</th><th>Alojamiento / ubicación</th><th>Estado</th><th>Personas</th><th>Fecha estado</th><th>Antigüedad</th><th>Vigencia</th><th>Consulta</th></tr></thead><tbody>${rows.map(r=>`<tr><td><b>${esc(r.municipio)}</b></td><td><b>${esc(r.establecimiento)}</b><div class="muted">${esc(r.ubicacion||r.direccion||'Ubicación no documentada')}</div></td><td>${statusBadge(r.estado_actual)}</td><td class="num">${r.poblacion_actual===null||r.poblacion_actual===''?'—':n(r.poblacion_actual)}</td><td>${fmtDate(r.fecha_estado)}</td><td>${freshness(r)}</td><td>${esc(r.vigencia)}</td><td><button class="v31-linkbtn" data-hist="${esc(r.id_establecimiento)}">Historial</button><button class="v31-linkbtn" data-diag="${esc(r.id_establecimiento)}">Diagnóstico</button></td></tr>`).join('')}</tbody></table></div>
    <div class="v31-history v31-card" id="v31-history"></div>`;
  el.querySelector('#v31-q').addEventListener('input',e=>{listFilter.q=e.target.value;renderList()});
  el.querySelector('#v31-m').addEventListener('change',e=>{listFilter.mun=e.target.value;renderList()});
  el.querySelector('#v31-s').addEventListener('change',e=>{listFilter.state=e.target.value;renderList()});
  el.querySelector('#v31-reset').addEventListener('click',()=>{listFilter={q:'',mun:'',state:''};renderList()});
  el.querySelectorAll('[data-hist]').forEach(b=>b.addEventListener('click',()=>showHistory(b.dataset.hist)));
  el.querySelectorAll('[data-diag]').forEach(b=>b.addEventListener('click',()=>openDiagnosis(b.dataset.diag)));
}
function showHistory(id){
  const box=root.querySelector('#v31-history');if(!box)return;
  const r=OP.find(x=>x.id_establecimiento===id);const h=HIST.filter(x=>x.id_establecimiento===id).sort((a,b)=>b.fecha.localeCompare(a.fecha));
  box.classList.add('open');
  box.innerHTML=`<h3>Trazabilidad · ${esc(r?.municipio||'')} · ${esc(r?.establecimiento||id)}</h3><p>${esc(r?.motivo_estado||'')}</p><div class="v31-timeline">${h.length?h.map(x=>`<div class="v31-event"><div class="date">${fmtDate(x.fecha)}</div><div class="event-title">${esc(x.estado)}${x.poblacion===null?'':` · ${n(x.poblacion)} personas`}</div><div class="source">${esc(x.fuente)}</div>${x.nota?`<div class="note">${esc(x.nota)}</div>`:''}</div>`).join(''):'<p>Sin eventos adicionales.</p>'}</div>`;
  box.scrollIntoView({behavior:'smooth',block:'nearest'});
}
function openDiagnosis(id){
  const r=OP.find(x=>x.id_establecimiento===id);switchView('diagnostico',true);
  const search=document.getElementById('ati-search');if(search&&r){search.value=r.establecimiento||r.municipio||'';search.dispatchEvent(new Event('input',{bubbles:true}));}
}


function mergeById(base,patch,key){
  const out=[...(base||[])];
  (patch||[]).forEach(p=>{const i=out.findIndex(x=>String(x[key]||'')===String(p[key]||''));if(i<0)out.push(p);else{const old=out[i];out[i]={...old,...p,fotos:(p.fotos&&p.fotos.length)?p.fotos:(old.fotos||[])};out[i].n_fotos=(out[i].fotos||[]).length;}});
  return out;
}
function mergeCem(base,patch){
  const out=[...(base||[])];
  (patch||[]).forEach(p=>{const pm=norm(p.municipio),pn=norm(p.nombre);let i=out.findIndex(x=>norm(x.municipio)===pm&&(norm(x.nombre)===pn||norm(x.nombre).includes(pn)||pn.includes(norm(x.nombre))));if(i<0)out.push(p);else{const old=out[i];out[i]={...old,...p,fotos:(p.fotos&&p.fotos.length)?p.fotos:(old.fotos||[])};out[i].n_fotos=(out[i].fotos||[]).length;}});
  return out;
}
function recalcMunicipalClient(){
  const muns=[...new Set([...(state.ati||[]),...(state.cem||[])].map(r=>r.municipio).filter(Boolean))].sort((a,b)=>String(a).localeCompare(String(b),'es'));
  return muns.map(m=>{const aa=state.ati.filter(r=>norm(r.municipio)===norm(m)),cc=state.cem.filter(r=>norm(r.municipio)===norm(m));return {municipio:m,cementerios:cc.length,cementerios_alta_critica:cc.filter(r=>['Alta','Crítica'].includes(r.prioridad_sanitaria)).length,cementerios_restriccion:cc.filter(r=>norm(r.restriccion)==='si'||r.flag_restriccion==='Sí').length,ati_sitios:aa.length,ati_alta_critica:aa.filter(r=>['Alta','Crítica'].includes(r.prioridad_global)).length,ati_no_concluyente:aa.filter(r=>r.prioridad_global==='No concluyente').length,poblacion_documentada:aa.reduce((a,r)=>a+n(r.poblacion_ultima||r.poblacion_total),0),fotos_cementerios:cc.reduce((a,r)=>a+n(r.n_fotos),0),fotos_ati:aa.reduce((a,r)=>a+n(r.n_fotos),0)};});
}
function refreshBaseDiagnosis(){
  try{
    state.mun=recalcMunicipalClient();
    renderKPIs();renderSummaries();renderATI();renderCem();renderMunicipal();
    const first=document.querySelector('#kpis .kpi .label');if(first)first.textContent='Sitios ATI históricos';
    const sub=document.querySelector('#kpis .kpi .sub');if(sub)sub.textContent=`${OP.length?currentRows().length:16} alojamientos vigentes`;
    // completar filtros con municipios que llegaron en el parche
    [['#ati-mun',state.ati,'municipio'],['#cem-mun',state.cem,'municipio']].forEach(([sel,arr,key])=>{const e=document.querySelector(sel);if(!e)return;const current=e.value;e.innerHTML='<option value="">Todos</option>';[...new Set(arr.map(x=>x[key]).filter(Boolean))].sort((a,b)=>String(a).localeCompare(String(b),'es')).forEach(v=>e.insertAdjacentHTML('beforeend',`<option value="${esc(v)}">${esc(v)}</option>`));e.value=current;});
  }catch(e){console.warn('V3.1: no fue posible refrescar la vista diagnóstica base',e);}
}
async function applyDiagnosisPatches(){
  try{
    const [ap,cp]=await Promise.all([
      fetch(DATA+'ati_v31_patch.json?'+Date.now()).then(r=>r.ok?r.json():[]),
      fetch(DATA+'cementerios_v31_patch.json?'+Date.now()).then(r=>r.ok?r.json():[])
    ]);
    let tries=0;while((!state.ati.length||!state.cem.length)&&tries<50){await new Promise(r=>setTimeout(r,100));tries++;}
    state.ati=mergeById(state.ati,ap,'id_establecimiento');
    state.cem=mergeCem(state.cem,cp);
    refreshBaseDiagnosis();
  }catch(e){console.warn('V3.1: parches de diagnóstico no aplicados',e);}
}
applyDiagnosisPatches();

Promise.all([
  fetch(DATA+'ati_operacion_v31.json?'+Date.now()).then(r=>{if(!r.ok)throw new Error('ati_operacion_v31.json');return r.json()}),
  fetch(DATA+'ati_historial_estados.json?'+Date.now()).then(r=>r.ok?r.json():[]),
  fetch(DATA+'ati_geo.json?'+Date.now()).then(r=>r.ok?r.json():[])
]).then(([op,hist,geo])=>{OP=op;HIST=hist;GEO=geo;renderPanorama();renderMap();renderList();switchView('panorama');}).catch(err=>{
  root.querySelector('[data-v31-panel="panorama"]').innerHTML=`<div class="v31-note"><strong>Error:</strong> no fue posible cargar los datos V3.1 (${esc(err.message)}). Ejecute nuevamente el actualizador local.</div>`;
});
})();
