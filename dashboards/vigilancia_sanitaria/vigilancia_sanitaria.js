const state={ati:[],cem:[],mun:[],page:{ati:1,cem:1},filters:{atiPri:[],cemLevel:[],cemPri:[]}};
const PAGE_SIZE={ati:2,cem:2};
const $=s=>document.querySelector(s); const $$=s=>[...document.querySelectorAll(s)];
const esc=v=>String(v??'').replace(/[&<>'"]/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[m]));
const norm=v=>String(v??'').toLocaleLowerCase('es').normalize('NFD').replace(/[\u0300-\u036f]/g,'');
const priClass=p=>{p=norm(p);if(p.includes('critic'))return'p-critical';if(p.includes('alta'))return'p-high';if(p.includes('media'))return'p-medium';if(p.includes('baja'))return'p-low';return'p-unknown'};
const priOrder={'Baja':1,'Media':2,'Alta':3,'Crítica':4,'No concluyente':0};
const chip=p=>`<span class="chip ${priClass(p)}">${esc(p||'No concluyente')}</span>`;
const display=v=>{const s=String(v??'').trim();return s||'No documentado'};
let lightboxItems=[]; let lightboxIndex=0;

Promise.all([
 fetch('../../data/vigilancia_sanitaria/current/ati_establecimientos.json').then(r=>r.json()),
 fetch('../../data/vigilancia_sanitaria/current/cementerios.json').then(r=>r.json()),
 fetch('../../data/vigilancia_sanitaria/current/resumen_municipal.json').then(r=>r.json())
]).then(([ati,cem,mun])=>{state.ati=ati;state.cem=cem;state.mun=mun;init()}).catch(err=>{
 document.body.insertAdjacentHTML('afterbegin',`<div style="padding:12px;background:#fee;color:#800">No fue posible cargar los datos. Abra el tablero con <b>01_ABRIR_VIGILANCIA_SANITARIA_LOCAL.bat</b>. ${esc(err.message)}</div>`)
});

function init(){renderKPIs();setupTabs();populateFilters();renderSummaries();bindFilters();renderATI();renderCem();renderMunicipal();bindModal()}

function renderKPIs(){
 const cemHi=state.cem.filter(x=>['Alta','Crítica'].includes(x.prioridad_sanitaria)).length;
 const atiHi=state.ati.filter(x=>['Alta','Crítica'].includes(x.prioridad_global)).length;
 $('#kpis').innerHTML=[
  ['green',state.ati.length,'Alojamiento Temporal',`${new Set(state.ati.map(x=>x.municipio)).size} municipios`,'ati-all'],
  ['',state.cem.length,'Cementerios consolidados','establecimientos evaluados en el corte','cem-all'],
  ['orange',atiHi,'ATI en prioridad alta','seleccionar alojamientos con prioridad alta','ati-high'],
  ['red',cemHi,'Cementerios clasificación Alta/Crítica','seleccionar prioridades Alta y Crítica','cem-high']
 ].map(([c,v,l,s,a])=>`<button type="button" class="kpi ${c}" data-kpi-action="${a}" title="Aplicar filtro en el módulo"><span class="value">${v}</span><span class="label">${l}</span><span class="sub">${s}</span><span class="kpi-hint">Clic para consultar</span></button>`).join('');
 $$('[data-kpi-action]').forEach(b=>b.addEventListener('click',()=>applyKpiAction(b.dataset.kpiAction)));
}

function clearFields(ids){ids.forEach(s=>{const el=$(s);if(el)el.value=''})}

function groupKey(group){return group==='ati-pri'?'atiPri':group==='cem-level'?'cemLevel':'cemPri'}
function getGroupValues(group){return state.filters[groupKey(group)]||[]}
function setGroupValues(group,values){state.filters[groupKey(group)]=[...new Set((values||[]).filter(Boolean))]}
function toggleGroupValue(group,value){const arr=getGroupValues(group);setGroupValues(group,arr.includes(value)?arr.filter(v=>v!==value):[...arr,value])}
function clearGroup(group){setGroupValues(group,[])}
function removeGroupValue(group,value){setGroupValues(group,getGroupValues(group).filter(v=>v!==value))}
function sameValues(a,b){return a.length===b.length&&a.every(v=>b.includes(v))}

function showTab(name,scroll=true){
 $$('.tab[data-tab]').forEach(x=>x.classList.toggle('active',x.dataset.tab===name));
 $$('.tab-panel').forEach(x=>x.classList.toggle('active',x.id==='panel-'+name));
 if(scroll) $('.tabs').scrollIntoView({behavior:'smooth',block:'start'});
}
function applyKpiAction(action){
 if(action==='ati-all'){
  clearFields(['#ati-search','#ati-mun','#ati-photo']); clearGroup('ati-pri'); state.page.ati=1; showTab('ati'); renderATI();
 }else if(action==='cem-all'){
  clearFields(['#cem-search','#cem-mun','#cem-photo']); clearGroup('cem-level'); clearGroup('cem-pri'); state.page.cem=1; showTab('cem'); renderCem();
 }else if(action==='ati-high'){
  clearFields(['#ati-search','#ati-mun','#ati-photo']); setGroupValues('ati-pri',['Alta']); state.page.ati=1; showTab('ati'); renderATI();
 }else if(action==='cem-high'){
  clearFields(['#cem-search','#cem-mun','#cem-photo']); clearGroup('cem-level'); setGroupValues('cem-pri',['Alta','Crítica']); state.page.cem=1; showTab('cem'); renderCem();
 }
 syncInteractiveStates();
}

function setupTabs(){ $$('.tab[data-tab]').forEach(b=>b.addEventListener('click',()=>showTab(b.dataset.tab,true))) }
function uniq(arr,key){return [...new Set(arr.map(x=>x[key]).filter(Boolean))].sort((a,b)=>String(a).localeCompare(String(b),'es'))}
function fill(sel,values){const el=$(sel);values.forEach(v=>el.insertAdjacentHTML('beforeend',`<option value="${esc(v)}">${esc(v)}</option>`))}
function populateFilters(){
 fill('#ati-mun',uniq(state.ati,'municipio'));fill('#ati-pri',['Baja','Media','Alta','No concluyente']);
 fill('#cem-mun',uniq(state.cem,'municipio'));fill('#cem-level',['Sin afectación','Leve','Moderada','Grave','Crítica','No consignado']);fill('#cem-pri',['Baja','Media','Alta','Crítica','No concluyente']);
}
function dist(arr,key,order){return order.map(v=>[v,arr.filter(x=>x[key]===v).length])}
function affectClass(n){
 const x=norm(n); if(x==='sin afectacion')return'low'; if(x==='leve')return'mild'; if(x==='moderada')return'medium'; if(x==='grave')return'high'; if(x==='critica')return'critical'; return'unknown';
}
function barClass(group,n){return group==='cem-level'?affectClass(n):priClass(n).replace('p-','')}
function summaryTone(group,n){return barClass(group,n)}
function compactBand(title,rows,group){
 return `<div class="summary-band" data-band-group="${group}"><span class="band-title">${esc(title)}</span><div class="band-items">${rows.map(([n,v])=>`<button type="button" class="summary-pill tone-${summaryTone(group,n)}" data-summary-group="${group}" data-summary-value="${esc(n)}" title="Agregar o quitar del filtro: ${esc(n)}"><span class="summary-dot"></span><span class="summary-name">${esc(n)}</span><b>${v}</b></button>`).join('')}</div></div>`
}
function renderSummaries(){
 $('#ati-summary').innerHTML=compactBand('Prioridad sanitaria',dist(state.ati,'prioridad_global',['Baja','Media','Alta','No concluyente']),'ati-pri');
 $('#cem-summary').innerHTML=compactBand('Afectación',dist(state.cem,'nivel_fuente',['Sin afectación','Leve','Moderada','Grave','Crítica','No consignado']),'cem-level')+compactBand('Prioridad sanitaria',dist(state.cem,'prioridad_sanitaria',['Baja','Media','Alta','Crítica']),'cem-pri');
 $$('[data-summary-group]').forEach(b=>b.addEventListener('click',()=>applySummaryFilter(b.dataset.summaryGroup,b.dataset.summaryValue)));
}
function applySummaryFilter(group,value){
 toggleGroupValue(group,value);
 if(group==='ati-pri'){ state.page.ati=1; showTab('ati',false); renderATI(); }
 else { state.page.cem=1; showTab('cem',false); renderCem(); }
 syncInteractiveStates();
}
function bindFilters(){
 ['#ati-search','#ati-mun','#ati-photo'].forEach(s=>$(s).addEventListener('input',()=>{state.page.ati=1;renderATI()}));
 ['#cem-search','#cem-mun','#cem-photo'].forEach(s=>$(s).addEventListener('input',()=>{state.page.cem=1;renderCem()}));
 $('#ati-clear').addEventListener('click',()=>{clearFields(['#ati-search','#ati-mun','#ati-photo']);clearGroup('ati-pri');state.page.ati=1;renderATI()});
 $('#cem-clear').addEventListener('click',()=>{clearFields(['#cem-search','#cem-mun','#cem-photo']);clearGroup('cem-level');clearGroup('cem-pri');state.page.cem=1;renderCem()});
 $('#mun-search').addEventListener('input',renderMunicipal)
}
function syncInteractiveStates(){
 $$('[data-summary-group]').forEach(b=>{
  const g=b.dataset.summaryGroup,v=b.dataset.summaryValue;
  b.classList.toggle('active',getGroupValues(g).includes(v));
 });
 $$('[data-kpi-action]').forEach(b=>b.classList.remove('active'));
 if(sameValues(getGroupValues('cem-pri'),['Alta','Crítica']) && getGroupValues('cem-level').length===0)$('[data-kpi-action="cem-high"]')?.classList.add('active');
 else if(sameValues(getGroupValues('ati-pri'),['Alta']))$('[data-kpi-action="ati-high"]')?.classList.add('active');
}

function photoBlock(r,type){
 const photos=r.fotos||[]; const name=type==='ati'?r.establecimiento:r.nombre; const caption=`${r.municipio} · ${name}`;
 if(!photos.length)return `<div class="record-photo no-photo"><div class="photo-placeholder"><strong>Sin registro fotográfico asociado</strong><small>La ficha sanitaria sí está disponible para revisión.</small></div></div>`;
 return `<div class="record-photo card-photo-carousel" data-card-gallery>
   <div class="card-photo-track">${photos.map((p,i)=>`<button type="button" class="card-photo-slide ${i===0?'active':''}" data-card-photo data-photo="${esc(p)}" data-caption="${esc(caption+' · fotografía '+(i+1))}" aria-label="Ampliar fotografía ${i+1} de ${photos.length}"><img src="${esc(p)}" alt="${esc(caption)}" loading="lazy"></button>`).join('')}</div>
   ${photos.length>1?`<button type="button" class="card-photo-nav prev" data-card-prev aria-label="Fotografía anterior">‹</button><button type="button" class="card-photo-nav next" data-card-next aria-label="Fotografía siguiente">›</button>`:''}
   <span class="photo-count" data-card-count>1 / ${photos.length}</span><span class="photo-zoom-hint">Clic para ampliar</span>
 </div>`
}
function bindCardGalleries(container){
 $$(container+' [data-card-gallery]').forEach(g=>{
  const slides=[...g.querySelectorAll('[data-card-photo]')]; let idx=0;
  const show=i=>{idx=(i+slides.length)%slides.length;slides.forEach((s,j)=>s.classList.toggle('active',j===idx));const c=g.querySelector('[data-card-count]');if(c)c.textContent=`${idx+1} / ${slides.length}`};
  g.querySelector('[data-card-prev]')?.addEventListener('click',e=>{e.stopPropagation();show(idx-1)});
  g.querySelector('[data-card-next]')?.addEventListener('click',e=>{e.stopPropagation();show(idx+1)});
  const items=slides.map(s=>({src:s.dataset.photo,cap:s.dataset.caption}));
  slides.forEach((s,i)=>s.addEventListener('click',e=>{e.stopPropagation();openLightboxGroup(items,i)}));
 });
}
function pageRows(rows,module){
 const size=PAGE_SIZE[module]||6; const pages=Math.max(1,Math.ceil(rows.length/size)); state.page[module]=Math.min(Math.max(1,state.page[module]),pages); const start=(state.page[module]-1)*size;
 return {rows:rows.slice(start,start+size),pages,start,size};
}

function repaginate(module){
 const cardsId=module==='ati'?'ati-cards':'cem-cards';
 const box=document.getElementById(cardsId);
 const beforeTop=box?box.getBoundingClientRect().top:null;
 module==='ati'?renderATI():renderCem();
 if(beforeTop!==null){
   const afterBox=document.getElementById(cardsId);
   const afterTop=afterBox?afterBox.getBoundingClientRect().top:null;
   if(afterTop!==null){ window.scrollBy({top:afterTop-beforeTop,left:0,behavior:'instant'}); }
 }
}

function renderPagination(id,module,total,pages){
 const el=$(id); const size=PAGE_SIZE[module]||6; if(total<=size){el.innerHTML='';return}
 const current=state.page[module];
 el.innerHTML=`<button class="page-btn prev" ${current===1?'disabled':''} data-page="${current-1}">‹ Anterior</button><label class="page-select-wrap">Página <select class="page-select" aria-label="Ir a página">${Array.from({length:pages},(_,i)=>i+1).map(n=>`<option value="${n}" ${n===current?'selected':''}>${n}</option>`).join('')}</select> de ${pages}</label><button class="page-btn next" ${current===pages?'disabled':''} data-page="${current+1}">Siguiente ›</button>`;
 el.querySelector('.page-select')?.addEventListener('change',e=>{state.page[module]=+e.target.value;repaginate(module)});
 el.querySelectorAll('[data-page]').forEach(b=>b.addEventListener('click',()=>{if(b.disabled)return;state.page[module]=+b.dataset.page;repaginate(module)}));
}
function municipalityLabel(m){return `<span class="municipality-label"><small>Municipio</small><b>${esc(m)}</b></span>`}

function atiFindings(r){
 const parts=[];
 const component=(label,priority,note)=>{
  const p=String(priority||'').trim(); const n=String(note||'').trim();
  if(['Alta','Crítica','Media'].includes(p)&&n)parts.push(n);
  if(p==='No concluyente'&&n)parts.push(`${label}: ${n}`);
 };
 component('Locativo/EIS',r.locativo_prioridad,r.locativo_nota);
 component('Alimentos',r.alimentos_prioridad,r.alimentos_nota);
 component('Vectores/Zoonosis',r.vectores_prioridad,r.vectores_nota);
 if(r.prioridad_global==='No concluyente'){
  const extra=String(r.observaciones||'').trim();
  const base='La información disponible no permite completar la valoración de las tres líneas sanitarias; se requiere nueva verificación.';
  return shortText(extra?`${base} ${extra}`:base,300);
 }
 if(parts.length)return shortText([...new Set(parts)].join(' '),300);
 return 'No se documentaron hallazgos sanitarios relevantes en las líneas evaluadas.';
}
function atiAlertFlagsHTML(r){
 const tags=[];
 const add=(label,cls='')=>{if(label&&!tags.some(x=>x[0]===label))tags.push([label,cls])};
 const pClass=p=>p==='Alta'||p==='Crítica'?'high':p==='Media'?'medium':'unknown';
 if(['Alta','Crítica','Media'].includes(r.locativo_prioridad))add(`Locativo/EIS · ${r.locativo_prioridad}`,pClass(r.locativo_prioridad));
 if(['Alta','Crítica','Media'].includes(r.alimentos_prioridad))add(`Alimentos · ${r.alimentos_prioridad}`,pClass(r.alimentos_prioridad));
 if(['Alta','Crítica','Media'].includes(r.vectores_prioridad))add(`Vectores/Zoonosis · ${r.vectores_prioridad}`,pClass(r.vectores_prioridad));
 if([r.locativo_prioridad,r.alimentos_prioridad,r.vectores_prioridad].includes('No concluyente'))add('Evaluación incompleta','unknown');
 const combined=norm([r.estado_operativo,r.locativo_nota,r.alimentos_nota,r.vectores_nota,r.observaciones].filter(Boolean).join(' '));
 if(combined.includes('reubic'))add('Reubicación','high');
 if(combined.includes('agua intermitente')||combined.includes('suministro de agua intermitente'))add('Agua','medium');
 if(combined.includes('lavado de manos'))add('Lavado de manos','high');
 if(combined.includes('vigilancia zoonot')||combined.includes('animales en el alojamiento'))add('Vigilancia zoonótica','medium');
 if(!tags.length)return'';
 return `<div class="flags ati-alerts">${tags.slice(0,4).map(([n,c])=>`<span class="flag ati-alert ${c}">${esc(n)}</span>`).join('')}</div>`;
}

function renderATI(){
 const q=norm($('#ati-search').value),m=$('#ati-mun').value,ph=$('#ati-photo').value,priSet=getGroupValues('ati-pri');
 let rows=state.ati.filter(x=>(!q||norm(x.municipio+' '+x.establecimiento).includes(q))&&(!m||x.municipio===m)&&(!priSet.length||priSet.includes(x.prioridad_global))&&matchesPhotoFilter(x,ph));
 rows.sort((x,y)=>(priOrder[y.prioridad_global]||0)-(priOrder[x.prioridad_global]||0)||x.municipio.localeCompare(y.municipio,'es'));
 const pg=pageRows(rows,'ati'); const end=Math.min(pg.start+pg.size,rows.length);
 $('#ati-count').textContent=rows.length?`Mostrando ${pg.start+1}–${end} de ${rows.length} alojamientos temporales`:'Sin alojamientos para los filtros seleccionados';
 $('#ati-cards').innerHTML=pg.rows.map(r=>`<article class="record-card ati-review-card">${photoBlock(r,'ati')}<div class="card-body"><div class="card-topline ati-heading">${municipalityLabel(r.municipio)}${chip(r.prioridad_global)}</div><h3>${esc(r.establecimiento)}</h3><section class="visit-sheet ati-visit-sheet"><div class="visit-sheet-title"><span>Ficha de seguimiento</span><b>${esc(display(r.fecha_ultima_visita))}</b></div><div class="visit-facts ati-visit-facts"><div><span>Prioridad sanitaria</span><strong>${esc(r.prioridad_global)}</strong></div><div><span>Población documentada</span><strong>${esc(display(r.poblacion_ultima))}</strong></div><div><span>Estado operativo</span><strong>${esc(display(r.estado_operativo))}</strong></div></div><div class="ati-line-priorities"><div><span>Locativo / EIS</span>${chip(r.locativo_prioridad)}</div><div><span>Alimentos</span>${chip(r.alimentos_prioridad)}</div><div><span>Vectores/Zoonosis</span>${chip(r.vectores_prioridad)}</div></div><div class="visit-findings ati-findings"><span>Hallazgos principales</span><p>${esc(atiFindings(r))}</p>${atiAlertFlagsHTML(r)}</div></section><div class="card-actions"><button class="detail-btn visit-detail-btn" data-detail="ati" data-id="${esc(r.id_establecimiento)}">Ver ficha sanitaria completa →</button></div></div></article>`).join('')||'<p>No hay resultados con los filtros seleccionados.</p>';
 renderATIActiveFilters();renderPagination('#ati-pagination','ati',rows.length,pg.pages);bindDetailButtons();bindCardGalleries('#ati-cards');syncInteractiveStates();
}
function flagsHTML(r){const f=[['Restricción/cierre',r.flag_restriccion],['Restos expuestos',r.flag_exposicion_restos],['Riesgo colapso',r.flag_riesgo_colapso],['Bóvedas abiertas',r.flag_bovedas_abiertas],['Salud pública',r.flag_salud_publica]];return `<div class="flags">${f.map(([n,v])=>`<span class="flag ${norm(v)==='si'?'alert':''}">${n}: ${esc(v)}</span>`).join('')}</div>`}
function renderCemActiveFilters(){
 const box=$('#cem-active-filters'); if(!box)return;
 const chips=[];
 getGroupValues('cem-level').forEach(v=>chips.push(`<button type="button" class="active-filter-chip" data-clear-cem-filter="level" data-filter-value="${esc(v)}"><span>Afectación</span>${esc(v)} ×</button>`));
 getGroupValues('cem-pri').forEach(v=>chips.push(`<button type="button" class="active-filter-chip priority" data-clear-cem-filter="pri" data-filter-value="${esc(v)}"><span>Prioridad</span>${esc(v)} ×</button>`));
 box.innerHTML=chips.join('')||'<span class="filter-empty">Sin filtro de afectación o prioridad</span>';
 box.querySelectorAll('[data-clear-cem-filter]').forEach(b=>b.addEventListener('click',()=>{
  const k=b.dataset.clearCemFilter,v=b.dataset.filterValue;
  if(k==='level')removeGroupValue('cem-level',v);
  if(k==='pri')removeGroupValue('cem-pri',v);
  state.page.cem=1;renderCem();
 }));
}
function renderATIActiveFilters(){
 const box=$('#ati-active-filters'); if(!box)return;
 const chips=[];
 getGroupValues('ati-pri').forEach(v=>chips.push(`<button type="button" class="active-filter-chip priority" data-clear-ati-filter="pri" data-filter-value="${esc(v)}"><span>Prioridad</span>${esc(v)} ×</button>`));
 box.innerHTML=chips.join('')||'<span class="filter-empty">Sin filtro de prioridad</span>';
 box.querySelectorAll('[data-clear-ati-filter]').forEach(b=>b.addEventListener('click',()=>{
  removeGroupValue('ati-pri',b.dataset.filterValue); state.page.ati=1; renderATI();
 }));
}
function hasPhotos(r){return Array.isArray(r.fotos)&&r.fotos.length>0}
function matchesPhotoFilter(r,v){return !v||(v==='con'&&hasPhotos(r))||(v==='sin'&&!hasPhotos(r))}
function shortText(v,max=230){const t=display(v);return t.length>max?t.slice(0,max-1).trimEnd()+'…':t}
function alertFlagsHTML(r){
 const f=[['Restricción/cierre',r.flag_restriccion],['Restos expuestos',r.flag_exposicion_restos],['Riesgo colapso',r.flag_riesgo_colapso],['Bóvedas abiertas',r.flag_bovedas_abiertas],['Salud pública',r.flag_salud_publica]].filter(([,v])=>norm(v)==='si');
 return f.length?`<div class="flags visit-alerts">${f.map(([n])=>`<span class="flag alert">${n}</span>`).join('')}</div>`:'';
}
function renderCem(){
 const q=norm($('#cem-search').value),m=$('#cem-mun').value,ph=$('#cem-photo').value,levelSet=getGroupValues('cem-level'),priSet=getGroupValues('cem-pri');
 let rows=state.cem.filter(x=>(!q||norm(x.municipio+' '+x.nombre).includes(q))&&(!m||x.municipio===m)&&(!levelSet.length||levelSet.includes(x.nivel_fuente))&&(!priSet.length||priSet.includes(x.prioridad_sanitaria))&&matchesPhotoFilter(x,ph));
 rows.sort((x,y)=>(priOrder[y.prioridad_sanitaria]||0)-(priOrder[x.prioridad_sanitaria]||0)||x.municipio.localeCompare(y.municipio,'es'));
 const pg=pageRows(rows,'cem'); const end=Math.min(pg.start+pg.size,rows.length);
 const multi=[levelSet.length?`afectación ${levelSet.join(', ')}`:'',priSet.length?`prioridad ${priSet.join(', ')}`:''].filter(Boolean).join(' · ');
 $('#cem-count').textContent=rows.length?`Mostrando ${pg.start+1}–${end} de ${rows.length} cementerios${multi?` · ${multi}`:''}`:'Sin cementerios para los filtros seleccionados';
 $('#cem-cards').innerHTML=pg.rows.map(r=>`<article class="record-card cemetery-review-card">${photoBlock(r,'cem')}<div class="card-body"><div class="card-topline cemetery-heading">${municipalityLabel(r.municipio)}${chip(r.prioridad_sanitaria)}</div><h3>${esc(r.nombre)}</h3><section class="visit-sheet"><div class="visit-sheet-title"><span>Ficha de visita</span><b>${esc(display(r.fecha))}</b></div><div class="visit-facts"><div><span>Afectación</span><strong>${esc(r.nivel_fuente)}</strong></div><div><span>Prioridad sanitaria</span><strong>${esc(r.prioridad_sanitaria)}</strong></div><div><span>Restricción / cierre</span><strong>${esc(display(r.restriccion))}</strong></div></div><div class="visit-findings"><span>Hallazgos principales</span><p>${esc(shortText(r.danos))}</p></div>${alertFlagsHTML(r)}</section><div class="card-actions"><button class="detail-btn visit-detail-btn" data-detail="cem" data-index="${state.cem.indexOf(r)}">Ver ficha sanitaria completa →</button></div></div></article>`).join('')||'<p>No hay resultados con los filtros seleccionados.</p>';
 renderCemActiveFilters();renderPagination('#cem-pagination','cem',rows.length,pg.pages);bindDetailButtons();bindCardGalleries('#cem-cards');syncInteractiveStates();
}
function renderMunicipal(){const q=norm($('#mun-search').value);const rows=state.mun.filter(x=>!q||norm(x.municipio).includes(q)).sort((a,b)=>a.municipio.localeCompare(b.municipio,'es'));$('#mun-table tbody').innerHTML=rows.map(r=>`<tr><td><b>${esc(r.municipio)}</b></td><td>${r.cementerios}</td><td>${r.cementerios_alta_critica}</td><td>${r.cementerios_restriccion}</td><td>${r.ati_sitios}</td><td>${r.ati_alta_critica}</td><td>${r.ati_no_concluyente}</td><td>${r.poblacion_documentada||'—'}</td><td>${(+r.fotos_cementerios||0)+(+r.fotos_ati||0)}</td></tr>`).join('')}
function bindDetailButtons(){$$('[data-detail]').forEach(b=>b.onclick=()=>{if(b.dataset.detail==='ati')openATI(state.ati.find(x=>x.id_establecimiento===b.dataset.id));else openCem(state.cem[+b.dataset.index])})}
function gallery(photos,caption){
 if(!photos?.length)return'<div class="empty-gallery">No hay fotografía asociada a este establecimiento en el corte consolidado.</div>';
 return `<div class="photo-carousel"><div class="gallery-toolbar"><span><b>${photos.length}</b> fotografía${photos.length===1?'':'s'} · clic para ampliar</span><div><button class="gallery-nav" data-gallery-prev aria-label="Fotos anteriores">‹</button><button class="gallery-nav" data-gallery-next aria-label="Fotos siguientes">›</button></div></div><div class="gallery" data-gallery-track>${photos.map((p,i)=>`<button class="photo-slide" data-photo="${esc(p)}" data-caption="${esc(caption+' · fotografía '+(i+1))}"><img src="${esc(p)}" alt="${esc(caption)}" loading="lazy"><span>${i+1} / ${photos.length}</span></button>`).join('')}</div></div>`
}
function bindGallery(){
 const track=$('[data-gallery-track]'); if(!track)return; const slides=[...track.querySelectorAll('[data-photo]')];
 const move=dir=>track.scrollBy({left:dir*track.clientWidth,behavior:'smooth'});
 $('[data-gallery-prev]')?.addEventListener('click',()=>move(-1)); $('[data-gallery-next]')?.addEventListener('click',()=>move(1));
 const items=slides.map(s=>({src:s.dataset.photo,cap:s.dataset.caption})); slides.forEach((s,i)=>s.addEventListener('click',()=>openLightboxGroup(items,i)));
}
function modalOpen(html){$('#modal-content').innerHTML=html;$('#detail-modal').classList.add('open');$('#detail-modal').setAttribute('aria-hidden','false');document.body.style.overflow='hidden';bindGallery()}
function openATI(r){if(!r)return;modalOpen(`<div class="modal-hero"><span class="eyebrow light">ALOJAMIENTO TEMPORAL</span><h2 id="modal-title">${esc(r.establecimiento)}</h2><p><b>Municipio: ${esc(r.municipio)}</b> · ${chip(r.prioridad_global)}</p></div><div class="modal-body"><div class="warning-box">La población corresponde a la última visita consolidada del sitio. No debe sumarse con cifras de otros momentos como censo simultáneo.</div><div class="detail-grid"><div class="detail-item"><span>Municipio</span><strong>${esc(r.municipio)}</strong></div><div class="detail-item"><span>Última visita</span><strong>${esc(display(r.fecha_ultima_visita))}</strong></div><div class="detail-item"><span>Estado operativo</span><strong>${esc(display(r.estado_operativo))}</strong></div><div class="detail-item"><span>Población</span><strong>${esc(display(r.poblacion_ultima))}</strong></div><div class="detail-item"><span>Agua</span><strong>${esc(display(r.agua_disponible))}</strong></div><div class="detail-item"><span>Fuente agua</span><strong>${esc(display(r.fuente_agua))}</strong></div><div class="detail-item"><span>Baterías sanitarias</span><strong>${esc(display(r.baterias_sanitarias))}</strong></div><div class="detail-item"><span>Animales</span><strong>${esc(display(r.animales))}</strong></div></div><div class="detail-section ati-modal-findings"><h3>Hallazgos principales</h3><p>${esc(atiFindings(r))}</p>${atiAlertFlagsHTML(r)}</div><div class="three-lines"><article class="line-detail"><h4>Locativo / EIS ${chip(r.locativo_prioridad)}</h4><p><b>${esc(r.locativo_estado)}</b></p><p>${esc(display(r.locativo_nota))}</p><p>${esc(display(r.agua_general))} · ${esc(display(r.excretas))}</p></article><article class="line-detail"><h4>Alimentos ${chip(r.alimentos_prioridad)}</h4><p><b>${esc(r.alimentos_estado)}</b></p><p>${esc(display(r.alimentos_nota))}</p><p>${esc(display(r.alimentos_general))}</p></article><article class="line-detail"><h4>Vectores / zoonosis ${chip(r.vectores_prioridad)}</h4><p><b>${esc(r.vectores_estado)}</b></p><p>${esc(display(r.vectores_nota))}</p><p>${esc(display(r.vectores_general))}</p></article></div><div class="detail-section"><h3>Observaciones y trazabilidad</h3><p>${esc(display(r.observaciones))}</p><p class="small-note"><b>Fuente:</b> ${esc(display(r.fuente))} · ${esc(display(r.tipo_fuente))}</p></div><div class="detail-section photo-section"><h3>Registro fotográfico</h3>${gallery(r.fotos,r.municipio+' · '+r.establecimiento)}</div></div>`)}
function openCem(r){if(!r)return;modalOpen(`<div class="modal-hero"><span class="eyebrow light">CEMENTERIO</span><h2 id="modal-title">${esc(r.nombre)}</h2><p><b>Municipio: ${esc(r.municipio)}</b> · Afectación: <b>${esc(r.nivel_fuente)}</b> · Prioridad sanitaria: ${chip(r.prioridad_sanitaria)}</p></div><div class="modal-body"><div class="warning-box">La clasificación de afectación es el valor conservado de la fuente. La prioridad sanitaria se usa para ordenar el seguimiento y no reemplaza evaluación estructural ni concepto sanitario formal.</div><div class="detail-grid"><div class="detail-item"><span>Municipio</span><strong>${esc(r.municipio)}</strong></div><div class="detail-item"><span>Fecha visita</span><strong>${esc(display(r.fecha))}</strong></div><div class="detail-item"><span>Completitud</span><strong>${esc(r.completitud_pct)}%</strong></div><div class="detail-item"><span>Restricción/cierre</span><strong>${esc(display(r.restriccion))}</strong></div><div class="detail-item"><span>Restos expuestos</span><strong>${esc(display(r.exposicion_restos))}</strong></div><div class="detail-item"><span>Bóvedas abiertas</span><strong>${esc(display(r.bovedas_abiertas))}</strong></div><div class="detail-item"><span>Riesgo colapso</span><strong>${esc(display(r.riesgo_colapso))}</strong></div><div class="detail-item"><span>Salud pública</span><strong>${esc(display(r.salud_publica))}</strong></div></div><div class="detail-section"><h3>Daños / hallazgos principales</h3><p>${esc(display(r.danos))}</p></div><div class="detail-section"><h3>Agua, residuos y seguridad</h3><div class="detail-grid"><div class="detail-item"><span>Agua</span><strong>${esc(display(r.agua))}</strong></div><div class="detail-item"><span>Gestión residuos</span><strong>${esc(display(r.residuos_gestion))}</strong></div><div class="detail-item"><span>Señalización</span><strong>${esc(display(r.senalizacion))}</strong></div><div class="detail-item"><span>Vías internas</span><strong>${esc(display(r.vias_seguras))}</strong></div></div></div><div class="detail-section"><h3>Observaciones y trazabilidad</h3><p>${esc(display(r.observaciones))}</p><p class="small-note"><b>Fuente:</b> ${esc(display(r.fuente_principal))} · ${esc(display(r.tipo_fuente))}</p></div><div class="detail-section photo-section"><h3>Registro fotográfico</h3>${gallery(r.fotos,r.municipio+' · '+r.nombre)}</div></div>`)}
function bindModal(){
 $$('[data-close]').forEach(x=>x.onclick=closeModal); $('[data-light-close]').onclick=closeLightbox;
 $('#lightbox-prev').addEventListener('click',()=>stepLightbox(-1)); $('#lightbox-next').addEventListener('click',()=>stepLightbox(1));
 document.addEventListener('keydown',e=>{if(e.key==='Escape'){closeModal();closeLightbox()}else if($('#lightbox').classList.contains('open')&&e.key==='ArrowLeft')stepLightbox(-1);else if($('#lightbox').classList.contains('open')&&e.key==='ArrowRight')stepLightbox(1)});
}
function closeModal(){if($('#detail-modal').classList.contains('open')){$('#detail-modal').classList.remove('open');$('#detail-modal').setAttribute('aria-hidden','true');document.body.style.overflow=''}}
function openLightboxGroup(items,index=0){lightboxItems=items||[];lightboxIndex=Math.max(0,Math.min(index,lightboxItems.length-1));if(!lightboxItems.length)return;renderLightbox();$('#lightbox').classList.add('open');$('#lightbox').setAttribute('aria-hidden','false')}
function renderLightbox(){const item=lightboxItems[lightboxIndex];if(!item)return;$('#lightbox-img').src=item.src;$('#lightbox-caption').textContent=`${item.cap} · ${lightboxIndex+1} de ${lightboxItems.length}`;const multi=lightboxItems.length>1;$('#lightbox-prev').style.display=multi?'grid':'none';$('#lightbox-next').style.display=multi?'grid':'none'}
function stepLightbox(dir){if(lightboxItems.length<2)return;lightboxIndex=(lightboxIndex+dir+lightboxItems.length)%lightboxItems.length;renderLightbox()}
function closeLightbox(){$('#lightbox').classList.remove('open');$('#lightbox').setAttribute('aria-hidden','true');lightboxItems=[]}
