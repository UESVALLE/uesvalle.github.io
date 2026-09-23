(() => {
'use strict';
const DATA = '../../data/cementerios/current/dashboard_data.json';
const GEO = 'assets/geo/valle_municipios.json';
const $ = s => document.querySelector(s);
const $$ = s => Array.from(document.querySelectorAll(s));
const fmt = new Intl.NumberFormat('es-CO');
const esc = v => String(v ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const norm = v => String(v ?? '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toUpperCase().trim();
const MESES = ['enero','febrero','marzo','abril','mayo','junio','julio','agosto','septiembre','octubre','noviembre','diciembre'];
const INTERNAL = new URLSearchParams(location.search).get('seguimiento') === '1';
const LEVELS = ['Sin afectación','Leve','Moderada','Grave','Crítica'];
const PRIORITIES = ['Baja','Media','Alta','Crítica'];
const LEVEL_RANK = {'Sin afectación':0,'Leve':1,'Moderada':2,'Grave':3,'Crítica':4};
const ESTADO = {S:'Sin hallazgo', O:'Con hallazgo documentado', V:'Por validar'};
const COMP = [['restriccion','Restricción'],['restos','Restos expuestos'],['colapso','Riesgo de colapso'],['salud','Salud pública']];
let DB = null, LB = null;

function fecha(v, larga){
  if(!v) return '—';
  const [y,m,d] = String(v).split('-').map(Number);
  return larga ? `${d} de ${MESES[m-1]} de ${y}` : `${String(d).padStart(2,'0')}/${String(m).padStart(2,'0')}/${y}`;
}
const pct=(a,b)=>b?Math.round(a/b*100):0;

const I={
 cemetery:'<path d="M5 21h14M7 21V9h10v12M10 9V5h4v4M9 13h6M9 17h6"/>',
 pin:'<path d="M12 21s-6.5-6.2-6.5-11a6.5 6.5 0 0 1 13 0c0 4.8-6.5 11-6.5 11z"/><circle cx="12" cy="10" r="2.3"/>',
 alert:'<path d="M12 3 2.8 20h18.4z"/><path d="M12 9v5M12 17h.01"/>',
 shield:'<path d="M12 3l7.5 3v5.5c0 4.6-3.2 8.2-7.5 9.5-4.3-1.3-7.5-4.9-7.5-9.5V6z"/><path d="M8.8 12.2l2.2 2.2 4.3-4.3"/>',
 camera:'<path d="M4 8.5h3l1.6-2.5h6.8L17 8.5h3v10.5H4z"/><circle cx="12" cy="13.5" r="3.3"/>',
 check:'<path d="M5 12.5l4 4L19 7"/>',
 bones:'<circle cx="7" cy="7" r="2"/><circle cx="17" cy="17" r="2"/><path d="M8.5 8.5l7 7M15.5 8.5l-7 7"/>'
};
const ico=(k,cls='ico')=>`<svg class="${cls}" viewBox="0 0 24 24" aria-hidden="true">${I[k]}</svg>`;
const affClass=v=>({'Sin afectación':'aff-none','Leve':'aff-mild','Moderada':'aff-mod','Grave':'aff-grave','Crítica':'aff-crit'}[v]||'');
const priClass=v=>({'Baja':'pri-low','Media':'pri-med','Alta':'pri-high','Crítica':'pri-crit'}[v]||'');
const badgeAff=v=>`<span class="badge ${affClass(v)}">${esc(v||'No consignado')}</span>`;
const badgePri=v=>`<span class="badge ${priClass(v)}">${esc(v||'No concluyente')}</span>`;

function render(){
  const k=DB.kpis;
  $('#cutDate').textContent = matchMedia('(max-width:720px)').matches ? fecha(DB.metadata.corte) : fecha(DB.metadata.corte,true);
  $('#lede').textContent = `Estado sanitario de ${fmt.format(k.cementerios)} cementerios individualizados en ${fmt.format(k.municipios)} municipios del Valle del Cauca tras el ${DB.metadata.evento.toLowerCase()}.`;

  const kpi=(cls,icon,n,label,sub,target,extra='')=>`<button type="button" class="kpi ${cls}" data-go="${target}"><span class="ic">${ico(icon)}</span><span><span class="n">${n}</span><span class="l">${label}</span>${extra}<span class="s">${sub}</span><span class="go">Clic para consultar</span></span></button>`;
  $('#kpis').innerHTML =
    kpi('k1','cemetery',k.cementerios,'Cementerios evaluados',`${k.con_afectacion} con afectación y ${k.sin_afectacion} sin afectación`,'mod-estado',`<span class="split" aria-hidden="true"><i class="a" style="width:${pct(k.sin_afectacion,k.cementerios)}%"></i><i class="b" style="width:${pct(k.con_afectacion,k.cementerios)}%"></i></span>`) +
    kpi('k2','pin',k.municipios,'Municipios','con cementerios individualizados','mod-territorio') +
    kpi('k3','alert',k.alta_critica,'Prioridad Alta/Crítica','cementerios priorizados para seguimiento','mod-poblacion') +
    kpi('k4','camera',k.fotos,'Evidencias fotográficas',`${k.con_fotos} cementerios con fotografías`,'mod-estado');
  $$('.kpi[data-go]').forEach(b=>b.onclick=()=>document.getElementById(b.dataset.go).scrollIntoView({behavior:'smooth'}));

  const n=DB.cementerios.length;
  $('#components').innerHTML = COMP.map(([key,label])=>{
    const r=DB.hallazgos_resumen.find(x=>x.clave===key) || {si:0,no:0,por_validar:n};
    const w=x=>(x/n*100).toFixed(2);
    return `<div class="comp"><div class="t"><span class="ci">${ico(key==='restos'?'bones':key==='restriccion'?'shield':'alert')}</span><span>${label}</span><b>${r.no}<small> / ${n}</small></b></div><div class="stack" role="img" aria-label="${label}: ${r.no} sin hallazgo, ${r.si} con hallazgo, ${r.por_validar} por validar">${r.no?`<i class="S" style="width:${w(r.no)}%"></i>`:''}${r.si?`<i class="O" style="width:${w(r.si)}%"></i>`:''}${r.por_validar?`<i class="V" style="width:${w(r.por_validar)}%"></i>`:''}</div><div class="d">sin hallazgo${r.si?`; ${r.si} con hallazgo`:''}${r.por_validar?`; ${r.por_validar} por validar`:''}</div></div>`;
  }).join('');

  DB.municipios.map(x=>x.municipio).sort((a,b)=>a.localeCompare(b,'es')).forEach(v=>$('#fMun').insertAdjacentHTML('beforeend',`<option>${esc(v)}</option>`));
  LEVELS.forEach(v=>$('#fNivel').insertAdjacentHTML('beforeend',`<option>${esc(v)}</option>`));
  PRIORITIES.forEach(v=>$('#fPri').insertAdjacentHTML('beforeend',`<option>${esc(v)}</option>`));
  ['#fMun','#fNivel','#fPri','#fFoto'].forEach(s=>$(s).onchange=drawRows);
  $('#btnClear').onclick=()=>{['#fMun','#fNivel','#fPri','#fFoto'].forEach(s=>$(s).value='');drawRows();};
  drawRows();

  const maxM=Math.max(...DB.municipios.map(m=>m.cementerios),1);
  const top=DB.municipios.slice().sort((a,b)=>b.cementerios-a.cementerios||a.municipio.localeCompare(b.municipio,'es'))[0];
  $('#terrLede').textContent = `${top.municipio} concentra ${top.cementerios} cementerio${top.cementerios===1?'':'s'} de los ${k.cementerios} registros individualizados. El mapa utiliza el máximo nivel de afectación documentado por municipio.`;
  $('#munBars').innerHTML = DB.municipios.slice().sort((a,b)=>b.cementerios-a.cementerios||a.municipio.localeCompare(b.municipio,'es')).map(m=>`<div class="bar" title="${esc(m.municipio)}: ${m.cementerios} cementerio(s); ${m.afectados} con afectación"><span class="lb">${esc(m.municipio)} <small>${m.afectados?`· ${m.afectados} afectados`:''}</small></span><span class="tr"><i class="a" style="width:${m.afectados/maxM*100}%"></i><i class="b" style="width:${Math.max(0,m.cementerios-m.afectados)/maxM*100}%"></i></span><b class="v">${m.cementerios}</b></div>`).join('');

  renderProfile();
  $('#method').innerHTML=DB.metodologia.map(t=>`<li>${esc(t)}</li>`).join('');
  $('#src').innerHTML=`${esc(DB.metadata.fuente_publica)} · corte ${fecha(DB.metadata.corte)} · ${esc(DB.metadata.version)}`;
  $('#btnPrint').onclick=()=>window.print();

  const tabs=$$('.tabs a');
  if('IntersectionObserver' in window){
    const io=new IntersectionObserver(es=>es.forEach(e=>{if(e.isIntersecting)tabs.forEach(t=>t.classList.toggle('on',t.getAttribute('href')==='#'+e.target.id));}),{rootMargin:'-40% 0px -55% 0px'});
    ['mod-estado','mod-territorio','mod-poblacion','mod-metodo'].forEach(id=>io.observe(document.getElementById(id)));
  }
  $$('.tabs a[href="#mod-metodo"]').forEach(a=>a.addEventListener('click',()=>{$('#methodBox').open=true;}));
  if(INTERNAL && DB.seguimiento) renderInternal();
  bindModal();
  drawMap();
}

function drawRows(){
  const fm=$('#fMun').value, fn=$('#fNivel').value, fp=$('#fPri').value, ff=$('#fFoto').value;
  const nf=a=>(a.fotos||[]).length;
  const rows=DB.cementerios.filter(a=>(!fm||a.municipio===fm)&&(!fn||a.nivel_fuente===fn)&&(!fp||a.prioridad_sanitaria===fp)&&(!ff||(ff==='con'?nf(a)>0:nf(a)===0)))
    .sort((a,b)=>a.municipio.localeCompare(b.municipio,'es')-(0)|| (LEVEL_RANK[b.nivel_fuente]||0)-(LEVEL_RANK[a.nivel_fuente]||0));
  $('#count').textContent=`${rows.length} de ${DB.cementerios.length} cementerios`;
  if(!rows.length){$('#rows').innerHTML='<tr><td colspan="8" class="empty">Ningún cementerio cumple el filtro. Cambie los filtros o use Limpiar.</td></tr>';return;}
  let prev=null;
  $('#rows').innerHTML=rows.map(a=>{
    const first=a.municipio!==prev; prev=a.municipio;
    return `<tr class="${first?'grp':''}" data-id="${esc(a.id)}" tabindex="0" aria-label="Ver ficha de ${esc(a.nombre)}"><td class="mun ${first?'':'rep'}">${esc(a.municipio)}</td><td class="site">${esc(a.nombre)}${nf(a)?` <span class="cam" title="Registro fotográfico: ${nf(a)} foto${nf(a)>1?'s':''}">${ico('camera')}<small>${nf(a)}</small></span>`:''}${a.ubicacion?`<small class="sec">${esc(a.ubicacion)}</small>`:''}</td><td>${badgeAff(a.nivel_fuente)}</td><td>${badgePri(a.prioridad_sanitaria)}</td>${COMP.map(([key,label])=>`<td class="c" data-l="${label}"><span class="cell ${a.estados?.[key]||'V'}" title="${label}: ${ESTADO[a.estados?.[key]||'V']}"></span></td>`).join('')}</tr>`;
  }).join('');
  $$('#rows tr[data-id]').forEach(tr=>{tr.onclick=()=>openFicha(tr.dataset.id);tr.onkeydown=e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();openFicha(tr.dataset.id);}};});
}

function renderProfile(){
  const maxA=Math.max(...DB.afectacion_resumen.map(x=>x.n),1);
  const iconMap={'Sin afectación':'check','Leve':'shield','Moderada':'alert','Grave':'alert','Crítica':'alert'};
  $('#affBars').innerHTML=DB.afectacion_resumen.map(x=>`<div class="life-row ${['Grave','Crítica'].includes(x.nivel)?'dep':''}"><span class="ib">${ico(iconMap[x.nivel]||'shield')}</span><span><span class="nm">${esc(x.nivel)}</span><span class="tr" style="display:block"><i style="width:${x.n/maxA*100}%"></i></span></span><b class="v">${x.n}</b></div>`).join('');
  const pc={'Baja':'#5a9160','Media':'#e0a33a','Alta':'#c9822b','Crítica':'#b8567f'};
  $('#priCards').innerHTML=DB.prioridad_resumen.map(x=>`<div class="gcard" style="--c:${pc[x.prioridad]||'#1f4e79'}"><span class="ib">${ico(x.prioridad==='Baja'?'shield':'alert')}</span><div><b>${x.n}</b><span>${esc(x.prioridad)}</span></div></div>`).join('');
  const maxH=Math.max(...DB.hallazgos_resumen.map(x=>x.si),1);
  $('#findingBars').innerHTML=DB.hallazgos_resumen.map(x=>`<div class="bar finding-bar"><span class="lb">${esc(x.hallazgo)}</span><span class="tr"><i class="c" style="width:${x.si/maxH*100}%"></i></span><b class="v">${x.si}</b></div>`).join('');
}

function openFicha(id){
  const a=DB.cementerios.find(x=>x.id===id); if(!a)return;
  $('#modalBody').innerHTML=`<div class="f-head"><span class="eyebrow dark">Ficha del cementerio</span><h2 id="mTitle">${esc(a.nombre)}</h2><p>${esc(a.municipio)}${a.aro?` · ${esc(a.aro)}`:''}</p>${badgeAff(a.nivel_fuente)} ${badgePri(a.prioridad_sanitaria)}</div><div class="f-grid"><div><span>Fecha visita</span><b>${fecha(a.fecha)}</b></div><div><span>Acta</span><b>${esc(a.acta_display||'—')}</b></div><div><span>Restricción</span><b>${esc(a.restriccion||'No documentado')}</b></div><div><span>Completitud</span><b>${fmt.format(a.completitud_pct)} %</b></div></div><div class="f-cond">${COMP.map(([key,label])=>`<div><span class="cell ${a.estados?.[key]||'V'}" title="${ESTADO[a.estados?.[key]||'V']}"></span><b>${label}</b><span>${esc(detailFor(a,key))}</span></div>`).join('')}</div><div class="f-findings"><h3>Daños / hallazgos principales</h3><p>${esc(a.danos||'No documentado en la fuente consolidada.')}</p></div>${fotosHtml(a)}<div class="f-meta">${a.observaciones?`<p><b>Observaciones:</b> ${esc(a.observaciones)}</p>`:''}${a.direccion?`<p><b>Ubicación:</b> ${esc(a.direccion)}</p>`:''}<p class="trace"><b>Fuente:</b> ${esc(a.fuente_principal||'No documentada')} · ${esc(a.tipo_fuente||'')}</p><p><b>Nota metodológica:</b> la afectación conserva el valor de la fuente; la prioridad sanitaria es operativa y no reemplaza concepto estructural ni sanitario formal.</p></div>`;
  const m=$('#modal');m.classList.add('open');m.setAttribute('aria-hidden','false');document.body.classList.add('lock');
  $$('#modalBody .th').forEach(b=>b.onclick=()=>openLightbox(a,Number(b.dataset.i)));$('.modal-x').focus();
}
function detailFor(a,key){
  if(key==='restriccion')return a.restriccion||'No documentado';
  if(key==='restos')return a.exposicion_restos||'No documentado';
  if(key==='colapso')return a.riesgo_colapso||'No documentado';
  if(key==='salud')return a.salud_publica||'No documentado';
  return 'No documentado';
}
function fotosHtml(a){
  const f=a.fotos||[];
  if(!f.length)return `<div class="f-photos empty-ph">${ico('camera')}<span>Sin registro fotográfico cargado para este cementerio.</span></div>`;
  return `<div class="f-photos"><h3>${ico('camera')} Registro fotográfico <small>${f.length} foto${f.length>1?'s':''}</small></h3><div class="gal">${f.map((x,i)=>`<button type="button" class="th" data-i="${i}" aria-label="Ampliar foto ${i+1} de ${f.length}"><img loading="lazy" src="${esc(x)}" alt="Registro fotográfico ${i+1} de ${f.length} · ${esc(a.nombre)}"></button>`).join('')}</div></div>`;
}
function openLightbox(a,i){LB={a,i};const box=$('#lightbox');box.classList.add('open');box.setAttribute('aria-hidden','false');showLb();$('#lbClose').focus();}
function showLb(){const f=LB.a.fotos,n=f.length;LB.i=(LB.i+n)%n;$('#lbImg').src=f[LB.i];$('#lbImg').alt=`Registro fotográfico ${LB.i+1} de ${n} · ${LB.a.nombre}`;$('#lbCap').textContent=`${LB.a.nombre} · ${LB.a.municipio} · foto ${LB.i+1} de ${n}`;$('#lbPrev').hidden=$('#lbNext').hidden=n<2;}
function closeLightbox(){const b=$('#lightbox');b.classList.remove('open');b.setAttribute('aria-hidden','true');LB=null;}
function closeModal(){const m=$('#modal');m.classList.remove('open');m.setAttribute('aria-hidden','true');document.body.classList.remove('lock');}
function bindModal(){
  $$('[data-close]').forEach(x=>x.onclick=closeModal);$$('[data-lbclose]').forEach(x=>x.onclick=closeLightbox);
  $('#lbPrev').onclick=()=>{LB.i--;showLb();};$('#lbNext').onclick=()=>{LB.i++;showLb();};
  document.addEventListener('keydown',e=>{if(LB){if(e.key==='Escape')closeLightbox();if(e.key==='ArrowLeft'){LB.i--;showLb();}if(e.key==='ArrowRight'){LB.i++;showLb();}return;}if(e.key==='Escape')closeModal();});
  let x0=null;$('#lightbox').addEventListener('touchstart',e=>{x0=e.touches[0].clientX;},{passive:true});$('#lightbox').addEventListener('touchend',e=>{if(x0===null||!LB)return;const dx=e.changedTouches[0].clientX-x0;x0=null;if(Math.abs(dx)>45){LB.i+=dx<0?1:-1;showLb();}});
}
function renderInternal(){
  $('#internal').hidden=false;const s=DB.seguimiento||[];
  $('#internalBody').innerHTML=`<div class="table-wrap"><table class="int-table"><thead><tr><th>Tipo</th><th>Municipio</th><th>Cementerio</th><th>Detalle</th></tr></thead><tbody>${s.map(x=>`<tr><td>${esc(x.tipo)}</td><td>${esc(x.municipio)}</td><td>${esc(x.cementerio)}</td><td>${esc(x.detalle)}</td></tr>`).join('')}</tbody></table></div><div class="int-val">${DB.validaciones.map(v=>`<span>${v.ok?'✓':'✗'} ${esc(v.control)}: ${fmt.format(v.calculado)}</span>`).join('')}<span>Datos generados ${esc(DB.metadata.generado)}</span></div>`;
}

function drawMap(){
  fetch(GEO+'?v=3.0.1').then(r=>{if(!r.ok)throw new Error('geo');return r.json();}).then(geo=>{
    const feats=geo.features;let x0=Infinity,x1=-Infinity,y0=Infinity,y1=-Infinity;
    const each=(g,fn)=>(g.type==='Polygon'?[g.coordinates]:g.coordinates).forEach(p=>p.forEach(r=>r.forEach(fn)));
    feats.forEach(f=>each(f.geometry,([x,y])=>{x0=Math.min(x0,x);x1=Math.max(x1,x);y0=Math.min(y0,y);y1=Math.max(y1,y);}));
    const kx=Math.cos((y0+y1)/2*Math.PI/180),W=520,s=W/((x1-x0)*kx),H=Math.round((y1-y0)*s),pad=8;const P=([x,y])=>[pad+(x-x0)*kx*s,pad+(y1-y)*s];
    const byKey=Object.fromEntries(DB.municipios.map(m=>[norm(m.municipio),m]));
    const colors={'Sin afectación':'#5a9160','Leve':'#d7c76b','Moderada':'#e0a33a','Grave':'#c9822b','Crítica':'#9d3b54'};
    const polys=[],labels=[];
    feats.forEach(f=>{const m=byKey[f.properties.clave];const rings=f.geometry.type==='Polygon'?[f.geometry.coordinates]:f.geometry.coordinates;const d=rings.map(poly=>poly.map(r=>'M'+r.map(c=>P(c).map(v=>v.toFixed(1)).join(',')).join('L')+'Z').join('')).join('');polys.push(`<path d="${d}" fill="${m?(colors[m.peor_nivel]||'#a9c4de'):'#e4eaef'}" class="${m?'on':''}" data-mun="${m?esc(m.municipio):''}"><title>${esc(f.properties.nombre)}${m?`: ${m.cementerios} cementerio(s); máximo ${m.peor_nivel}`:''}</title></path>`);if(m){let best=null,ba=0;rings.forEach(poly=>{const r=poly[0];let a=0,cx=0,cy=0;for(let i=0,j=r.length-1;i<r.length;j=i++){const q=r[j][0]*r[i][1]-r[i][0]*r[j][1];a+=q;cx+=(r[j][0]+r[i][0])*q;cy+=(r[j][1]+r[i][1])*q;}if(Math.abs(a)>ba){ba=Math.abs(a);best=[cx/(3*a),cy/(3*a)];}});if(best){const [lx,ly]=P(best);labels.push(`<text x="${lx.toFixed(1)}" y="${ly.toFixed(1)}" text-anchor="middle">${esc(m.municipio)}</text><text class="v" x="${lx.toFixed(1)}" y="${(ly+12).toFixed(1)}" text-anchor="middle">${m.cementerios}</text>`);}}});
    $('#map').innerHTML=`<svg viewBox="0 0 ${W+pad*2} ${H+pad*2}" role="img" aria-label="Mapa del Valle del Cauca con ${DB.municipios.length} municipios con cementerios evaluados">${polys.join('')}${labels.join('')}</svg><div class="map-scale" aria-hidden="true"><span><i style="background:#5a9160"></i>Sin afectación</span><span><i style="background:#d7c76b"></i>Leve</span><span><i style="background:#e0a33a"></i>Moderada</span><span><i style="background:#c9822b"></i>Grave</span><span><i style="background:#9d3b54"></i>Crítica</span><span><i style="background:#e4eaef"></i>Sin registro</span></div>`;
    $$('#map path.on').forEach(p=>p.onclick=()=>{$('#fMun').value=p.dataset.mun;drawRows();document.getElementById('h-estado').scrollIntoView({behavior:'smooth'});});
  }).catch(()=>{$('#map').innerHTML='<div class="map-msg">Mapa no disponible. La distribución por municipio se muestra en las barras.</div>';});
}

fetch(DATA+'?v=3.0.1&ts='+Date.now()).then(r=>{if(!r.ok)throw new Error('No se encontró dashboard_data.json');return r.json();}).then(d=>{DB=d;render();}).catch(err=>{document.getElementById('sheet').innerHTML=`<div style="padding:40px"><h2>No se pudieron cargar los datos</h2><p>${esc(err.message)}.</p><p>Abra el tablero mediante un servidor local desde la estructura UESVALLE.</p></div>`;});
})();
