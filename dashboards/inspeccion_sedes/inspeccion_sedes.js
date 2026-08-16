(() => {
  "use strict";

  const DATA_URL = "../../data/inspeccion_sedes/current/inspecciones.json";
  const META_URL = "../../data/inspeccion_sedes/current/metadata.json";
  const COMPLEMENT_URLS = [
    {label:"Cartago", url:"../../data/inspeccion_sedes/current/complementarias/manifest_cartago_sin_hallazgo.json"},
    {label:"Tuluá", url:"../../data/inspeccion_sedes/current/complementarias/manifest_tulua_sin_hallazgo.json"}
  ];
  const PDF_HEADER_LOGO_URL = "./encabezado_informe_uesvalle.png";
  const nf = new Intl.NumberFormat("es-CO");
  const df = new Intl.DateTimeFormat("es-CO", {day:"numeric", month:"numeric", year:"numeric", hour:"numeric", minute:"2-digit", hour12:true});

  let DATA = [];
  let FILTERED = [];
  let META = null;
  let COMPLEMENTS = [];
  let charts = {};
  let dtFindings = null;
  let selectedId = null;
  let detailSede = "";
  let detailArea = "";
  let detailFindingIndex = 0;
  let detailPhotoIndex = 0;

  const $ = (id) => document.getElementById(id);
  const esc = (v) => String(v ?? "").replace(/[&<>'"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;","'":"&#39;",'"':"&quot;"}[c]));
  const norm = (v) => String(v ?? "").trim().toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
  const yes = (v) => norm(v) === "si";
  const levelClass = (v) => `badge-${norm(v).replace(/\s+/g,"-") || "por-determinar"}`;

  function areaCondition(r) {
    if (r?.es_hallazgo === true || norm(r?.resultado).includes("hallazgo")) return "Con hallazgo";
    if (r?.es_hallazgo === false || norm(r?.resultado).includes("sin afectacion")) return "Sin afectación observable";
    return "Por determinar";
  }

  function showStatus(message, kind="secondary") {
    const box = $("loadAlert");
    if (!box) return;
    const hidden = box.classList.contains("d-none");
    box.className = `status-body mt-3 alert alert-${kind}${hidden ? " d-none" : ""}`;
    box.textContent = message;
  }

  function setUpdateBadge() {
    const badge = $("lastUpdate");
    if (!badge || !META) return;
    const raw = META.procesado_en;
    if (!raw) { badge.textContent = "Actualizado: sin fecha"; return; }
    const dt = new Date(raw);
    badge.textContent = Number.isNaN(dt.getTime()) ? `Actualizado: ${raw}` : `Actualizado: ${df.format(dt)}`;
  }

  function populateSelect(id, values, allText) {
    const el = $(id);
    const current = el.value;
    el.innerHTML = `<option value="">${esc(allText)}</option>` + [...new Set(values.filter(Boolean))].sort((a,b)=>a.localeCompare(b,"es")).map(v => `<option value="${esc(v)}">${esc(v)}</option>`).join("");
    if ([...el.options].some(o => o.value === current)) el.value = current;
  }

  function populateFilters() {
    const sedesBase = ["ARO Cali","ARO Tuluá","ARO Cartago","Sede Principal UESVALLE", ...DATA.map(r=>r.sede)];
    populateSelect("fSede", sedesBase, "Todas");
    populateSelect("fCondicion", DATA.map(areaCondition), "Todas");
    populateSelect("fTipoDano", DATA.filter(r=>r.es_hallazgo).map(r=>r.tipo_dano), "Todos");
    populateSelect("fNivel", DATA.filter(r=>r.es_hallazgo).map(r=>r.nivel), "Todos");
  }

  function renderActiveFilters() {
    const wrap = $("activeFilters");
    const items = [
      ["Sede", $("fSede").value],
      ["Condición", $("fCondicion").value],
      ["Tipo de daño", $("fTipoDano").value],
      ["Nivel", $("fNivel").value]
    ].filter(([,v]) => v);
    wrap.innerHTML = items.length ? items.map(([k,v])=>`<span class="active-filter-chip">${esc(k)}: ${esc(v)}</span>`).join("") : `<span class="text-muted small">Sin filtros adicionales</span>`;
  }

  function applyFilters() {
    const sede = $("fSede").value;
    const condicion = $("fCondicion").value;
    const tipoDano = $("fTipoDano").value;
    const nivel = $("fNivel").value;
    FILTERED = DATA.filter(r =>
      (!sede || r.sede === sede) &&
      (!condicion || areaCondition(r) === condicion) &&
      (!tipoDano || r.tipo_dano === tipoDano) &&
      (!nivel || r.nivel === nivel)
    );
    renderActiveFilters();
    renderKPIs();
    renderCharts();
    renderSummaryTable();
    renderFindingsTable();
    syncDetailSelectorsFromGlobal();
    renderReportPreview();
  }

  function clearFilters() {
    ["fSede","fCondicion","fTipoDano","fNivel"].forEach(id => $(id).value = "");
    applyFilters();
  }

  function groupAreas(records) {
    const map = new Map();
    records.forEach(r => {
      const key = `${r.sede || ""}|||${r.area || ""}`;
      if (!map.has(key)) map.set(key, {sede:r.sede||"", area:r.area||"", records:[]});
      map.get(key).records.push(r);
    });
    return [...map.values()];
  }

  function metrics(records=FILTERED) {
    const hall = records.filter(r=>r.es_hallazgo);
    const areas = groupAreas(records);
    const affectedAreas = areas.filter(g=>g.records.some(r=>r.es_hallazgo)).length;
    return {
      records: records.length,
      aros: new Set(records.map(r=>r.sede).filter(Boolean)).size,
      areas: areas.length,
      affectedAreas,
      findings: hall.length,
      clear: areas.length - affectedAreas,
      high: hall.filter(r=>norm(r.nivel)==="alta").length,
      risk: hall.filter(r=>r.riesgo_si).length,
      review: hall.filter(r=>r.revision_si).length,
      photos: records.reduce((a,r)=>a+(Number(r.n_evidencias ?? r.n_fotos ?? (r.fotos||[]).length)||0),0)
    };
  }

  function renderKPIs() {
    const m = metrics();
    $("kpiAros").textContent = nf.format(m.aros);
    $("kpiFindings").textContent = nf.format(m.findings);
    $("kpiClear").textContent = nf.format(m.clear);
    $("kpiHigh").textContent = nf.format(m.high);
    $("kpiRisk").textContent = nf.format(m.risk);
    $("kpiReview").textContent = nf.format(m.review);
  }

  function destroyChart(name) { if (charts[name]) { charts[name].destroy(); charts[name] = null; } }

  function renderCharts() {
    const hall = FILTERED.filter(r=>r.es_hallazgo);
    const sedes = [...new Set(FILTERED.map(r=>r.sede).filter(Boolean))].sort((a,b)=>a.localeCompare(b,"es"));
    const levels = ["Leve","Moderada","Alta","Por determinar"];
    destroyChart("levels");
    const levelColors={"Leve":"#f4c542","Moderada":"#f59e0b","Alta":"#dc3545","Por determinar":"#adb5bd"};
    charts.levels = new Chart($("chartLevels"), {
      type:"bar",
      data:{labels:sedes,datasets:levels.map(level=>({label:level,backgroundColor:levelColors[level],data:sedes.map(s=>hall.filter(r=>r.sede===s && (r.nivel||"Por determinar")===level).length)}))},
      options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{position:"bottom"}},scales:{x:{stacked:true},y:{stacked:true,beginAtZero:true,ticks:{precision:0}}},onHover:(evt,els)=>{evt.native.target.style.cursor=els.length?"pointer":"default";},onClick:(evt,els)=>{
        if(!els.length)return;
        const point=els[0];
        const sede=sedes[point.index];
        const level=levels[point.datasetIndex];
        const same=$("fSede").value===sede && $("fNivel").value===level;
        $("fSede").value=same?"":sede;
        $("fNivel").value=same?"":level;
        applyFilters();
      }}
    });

    const counts = {};
    hall.forEach(r=>{ const k=r.tipo_dano||"Sin clasificar"; counts[k]=(counts[k]||0)+1; });
    const damageLabels = Object.keys(counts).sort((a,b)=>counts[b]-counts[a]);
    destroyChart("damage");
    charts.damage = new Chart($("chartDamage"), {
      type:"bar",
      data:{labels:damageLabels,datasets:[{label:"Hallazgos",data:damageLabels.map(k=>counts[k])}]},
      options:{indexAxis:"y",responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}},scales:{x:{beginAtZero:true,ticks:{precision:0}}},onHover:(evt,els)=>{evt.native.target.style.cursor=els.length?"pointer":"default";},onClick:(evt,els)=>{
        if(!els.length)return;
        const damage=damageLabels[els[0].index];
        $("fTipoDano").value=$("fTipoDano").value===damage?"":damage;
        applyFilters();
      }}
    });
  }

  function renderSummaryTable() {
    const tbody = $("tblSummary").querySelector("tbody");
    const sedes = [...new Set(FILTERED.map(r=>r.sede).filter(Boolean))].sort((a,b)=>a.localeCompare(b,"es"));
    tbody.innerHTML = sedes.map(sede=>{
      const rr = FILTERED.filter(r=>r.sede===sede); const m=metrics(rr);
      return `<tr data-sede="${esc(sede)}"><td><button class="btn btn-link btn-sm p-0 fw-bold summary-sede">${esc(sede)}</button></td><td>${m.areas}</td><td>${m.findings}</td><td>${m.clear}</td><td>${m.high}</td><td>${m.risk}</td></tr>`;
    }).join("") || `<tr><td colspan="6" class="text-muted">Sin registros para los filtros seleccionados.</td></tr>`;
    tbody.querySelectorAll(".summary-sede").forEach(btn=>btn.addEventListener("click",()=>{ $("fSede").value=btn.closest("tr").dataset.sede; applyFilters(); }));
  }

  function findingRows() {
    return FILTERED.filter(r=>r.es_hallazgo).sort((a,b)=> (b.nivel_orden-a.nivel_orden) || Number(b.riesgo_si)-Number(a.riesgo_si) || a.sede.localeCompare(b.sede,"es"));
  }

  function renderFindingsTable() {
    const table = $("tblFindings");
    if (dtFindings) { dtFindings.destroy(); dtFindings = null; }
    table.innerHTML = `<thead><tr><th>Sede</th><th>Área</th><th>Elemento normalizado</th><th>Tipo de daño</th><th>Nivel</th><th>Riesgo</th><th>Revisión</th><th>Evidencias</th><th></th></tr></thead><tbody></tbody>`;
    const tbody = table.querySelector("tbody");
    tbody.innerHTML = findingRows().map(r=>`<tr data-id="${esc(r.id)}"><td>${esc(r.sede)}</td><td>${esc(r.area)}</td><td>${esc(r.elemento_ajustado||"Por determinar")}</td><td>${esc(r.tipo_dano||"")}</td><td><span class="badge-level ${levelClass(r.nivel)}">${esc(r.nivel||"Por determinar")}</span></td><td>${esc(r.riesgo_inmediato||"")}</td><td>${esc(r.revision_tecnica||"")}</td><td>${r.n_fotos||0}</td><td><button class="btn btn-outline-primary btn-sm btn-detail">Ver área</button></td></tr>`).join("");
    tbody.querySelectorAll(".btn-detail").forEach(btn=>btn.addEventListener("click",()=>openAreaFromFinding(btn.closest("tr").dataset.id)));
    if (window.jQuery && window.jQuery.fn && window.jQuery.fn.DataTable) {
      dtFindings = window.jQuery(table).DataTable({pageLength:10,order:[[4,"desc"]],language:{url:"https://cdn.datatables.net/plug-ins/1.13.8/i18n/es-ES.json"},dom:"Bfrtip",buttons:["copy","excel","print"]});
    }
  }

  function photoCard(p, index, recordId="") {
    const candidates = [...(p.local_candidates||[])].filter(Boolean);
    const src = candidates[0] || "";
    const encoded = encodeURIComponent(JSON.stringify(candidates));
    return `<div class="photo-card"><img loading="lazy" data-record-id="${esc(recordId)}" data-photo-index="${index-1}" data-candidates="${encoded}" data-candidate-index="0" src="${esc(src)}" alt="Evidencia ${index}"><div class="photo-fallback" style="display:none">📷 Evidencia pendiente de sincronizar</div><div class="photo-card-caption">Evidencia ${index}</div></div>`;
  }

  function evidenceCandidates(evidence) {
    const items=[];
    if(evidence?.local_path) items.push(evidence.local_path);
    for(const x of (evidence?.local_candidates||[])) if(x && !items.includes(x)) items.push(x);
    return items;
  }

  function evidenceType(evidence) {
    if(evidence?.media_type) return evidence.media_type;
    const src=(evidence?.local_path || evidenceCandidates(evidence)[0] || "").toLowerCase();
    if(/\.(mp4|webm|mov|m4v)(?:$|\?)/.test(src)) return "video";
    return "imagen";
  }

  function openEvidence(evidence) {
    const src = evidenceCandidates(evidence)[0] || "";
    if(!src) return;
    const isVideo=evidenceType(evidence)==="video";
    $("evidenceModalTitle").textContent = isVideo ? "Evidencia en video" : "Evidencia fotográfica";
    const img=$("evidenceModalImage"), video=$("evidenceModalVideo");
    if(isVideo){
      img.classList.add("d-none"); img.removeAttribute("src");
      video.classList.remove("d-none"); video.src=src; video.load();
    }else{
      video.pause(); video.classList.add("d-none"); video.removeAttribute("src");
      img.classList.remove("d-none"); img.src=src;
    }
    $("evidenceModalOpen").href = src;
    $("evidenceModalOpen").textContent = isVideo ? "Abrir video" : "Abrir imagen";
    bootstrap.Modal.getOrCreateInstance($("evidenceModal")).show();
  }

  function areaLevelOrder(level) {
    const map={"leve":1,"moderada":2,"alta":3,"por determinar":0};
    return map[norm(level)] ?? 0;
  }

  function areaSummary(records) {
    const hall=records.filter(r=>r.es_hallazgo);
    const max=hall.slice().sort((a,b)=>areaLevelOrder(b.nivel)-areaLevelOrder(a.nivel))[0];
    return {
      records: records.length,
      findings: hall.length,
      maxLevel: max?.nivel || "Sin afectación",
      risk: hall.some(r=>r.riesgo_si),
      review: hall.some(r=>r.revision_si),
      photos: records.reduce((a,r)=>a+(Number(r.n_evidencias ?? r.n_fotos ?? (r.fotos||[]).length)||0),0),
      priority: hall.some(r=>r.riesgo_si || norm(r.nivel)==="alta")
    };
  }

  function hasGlobalFilters() {
    return ["fSede","fCondicion","fTipoDano","fNivel"].some(id => $(id)?.value);
  }

  function detailSourceRecords() {
    return hasGlobalFilters() ? FILTERED : DATA;
  }

  function detailRecordsForArea(sede, area) {
    return detailSourceRecords().filter(r=>r.sede===sede && r.area===area);
  }

  function areaVisual(summary) {
    if (!summary.findings) return {icon:"🟢", rank:0, label:"sin afectación observable"};
    if (summary.risk || norm(summary.maxLevel)==="alta") return {icon:"🔴", rank:50, label:"alta / riesgo inmediato"};
    if (norm(summary.maxLevel)==="moderada" || summary.review) return {icon:"🟠", rank:40, label:"moderada / revisión"};
    if (norm(summary.maxLevel)==="leve") return {icon:"🟡", rank:30, label:"leve"};
    return {icon:"⚪", rank:20, label:"por determinar"};
  }

  function areaOptionLabel(sede, area) {
    const rr=detailRecordsForArea(sede, area);
    const s=areaSummary(rr);
    const visual=areaVisual(s);
    const suffix=s.findings?`${s.findings} hallazgo${s.findings===1?"":"s"}`:"sin afectación observable";
    return `${visual.icon} ${area} · ${suffix}`;
  }

  function detailAreasForSede(sede) {
    return [...new Set(detailSourceRecords().filter(r=>r.sede===sede).map(r=>r.area).filter(Boolean))]
      .sort((a,b)=>{
        const sa=areaSummary(detailRecordsForArea(sede,a));
        const sb=areaSummary(detailRecordsForArea(sede,b));
        return areaVisual(sb).rank-areaVisual(sa).rank || a.localeCompare(b,"es");
      });
  }

  function populateDetailSede() {
    const sedes=[...new Set(detailSourceRecords().map(r=>r.sede).filter(Boolean))].sort((a,b)=>a.localeCompare(b,"es"));
    const el=$("dSede"); if(!el)return;
    const current=detailSede || el.value;
    el.innerHTML=`<option value="">Seleccione</option>`+sedes.map(s=>`<option value="${esc(s)}">${esc(s)}</option>`).join("");
    if(current && sedes.includes(current)) el.value=current;
  }

  function populateDetailArea(preferred="") {
    const sede=$("dSede")?.value || "";
    detailSede=sede;
    const el=$("dArea"); if(!el)return;
    const areas=sede?detailAreasForSede(sede):[];
    const target=preferred || detailArea || el.value;
    el.innerHTML=`<option value="">Seleccione un área</option>`+areas.map(a=>`<option value="${esc(a)}">${esc(areaOptionLabel(sede,a))}</option>`).join("");
    if(target && areas.includes(target)) el.value=target;
    else if(areas.length) {
      el.value=areas[0];
    }
    detailArea=el.value;
    updateAreaNavButtons();
  }

  function syncDetailSelectorsFromGlobal() {
    if(!$("dSede")||!$("dArea"))return;
    const previousSede=detailSede || $("dSede").value;
    const previousArea=detailArea || $("dArea").value;
    populateDetailSede();
    const globalSede=$("fSede").value;
    const availableSedes=[...$("dSede").options].map(o=>o.value).filter(Boolean);
    const targetSede=(globalSede && availableSedes.includes(globalSede)) ? globalSede : (availableSedes.includes(previousSede) ? previousSede : (availableSedes[0]||""));
    $("dSede").value=targetSede;
    detailSede=targetSede;
    populateDetailArea(previousArea);
    detailArea=$("dArea").value;
    detailFindingIndex=0;
    detailPhotoIndex=0;
    renderAreaDetail();
  }

  function bindPhotoEvents(container) {
    if(!container)return;
    container.querySelectorAll(".photo-card img").forEach(img=>{
      img.addEventListener("click",()=>{
        const r=DATA.find(x=>x.id===img.dataset.recordId);
        const p=r?.fotos?.[Number(img.dataset.photoIndex)||0];
        if(p)openEvidence(p);
      });
      img.addEventListener("error",()=>{
        let candidates=[]; try{candidates=JSON.parse(decodeURIComponent(img.dataset.candidates||"%5B%5D"));}catch(_){}
        const next=(Number(img.dataset.candidateIndex)||0)+1;
        if(next<candidates.length){img.dataset.candidateIndex=String(next);img.src=candidates[next];}
        else{img.style.display="none";const fb=img.nextElementSibling;if(fb)fb.style.display="flex";}
      });
    });
  }

  function photoCandidates(photo) { return evidenceCandidates(photo); }

  function candidateImageAttrs(photo, extra="") {
    const candidates=photoCandidates(photo);
    const src=candidates[0]||"";
    const encoded=encodeURIComponent(JSON.stringify(candidates));
    return `src="${esc(src)}" data-candidates="${encoded}" data-candidate-index="0" ${extra}`;
  }

  function renderFindingSwitcher(hall) {
    if(hall.length<=1) return `<div class="finding-record-id">Hallazgo registrado</div>`;
    return `<div class="finding-switcher"><span class="finding-switcher-label">Hallazgos del área</span>${hall.map((r,i)=>`<button type="button" class="finding-switch-btn ${i===detailFindingIndex?"active":""}" data-finding-index="${i}">Hallazgo ${i+1}</button>`).join("")}</div>`;
  }

  function renderFindingInfo(r, hall) {
    const when=r.timestamp ? df.format(new Date(r.timestamp)) : "Fecha no reportada";
    return `${renderFindingSwitcher(hall)}
      <div class="finding-badges"><span class="badge-level ${levelClass(r.nivel)}">${esc(r.nivel||"Por determinar")}</span>${r.riesgo_si?`<span class="finding-badge finding-badge-risk">⚠ Riesgo inmediato</span>`:""}${r.revision_si?`<span class="finding-badge finding-badge-review">🛠 Revisión técnica</span>`:""}</div>
      <div class="finding-form-grid">
        <div class="finding-form-field"><small>Resultado del registro</small><b>${esc(r.resultado||"Hallazgo / afectación observada")}</b></div>
        <div class="finding-form-field"><small>Clasificación técnica normalizada</small><b>${esc(r.componente_ajustado||"Por determinar")}</b></div>
        <div class="finding-form-field"><small>Elemento normalizado</small><b>${esc(r.elemento_ajustado||"No reportado")}</b></div>
        <div class="finding-form-field"><small>Tipo de daño</small><b>${esc(r.tipo_dano||"No reportado")}</b></div>
        <div class="finding-form-field"><small>Dimensiones aproximadas</small><b>${esc(r.dimensiones||"No reportadas")}</b></div>
        <div class="finding-form-field"><small>Extensión</small><b>${esc(r.extension||"No reportada")}</b></div>
        <div class="finding-form-field"><small>Riesgo inmediato</small><b>${esc(r.riesgo_inmediato||"No aplica")}</b></div>
        <div class="finding-form-field"><small>Revisión técnica</small><b>${esc(r.revision_tecnica||"No aplica")}</b></div>
        <div class="finding-form-field"><small>Fecha / hora</small><b>${esc(when)}</b></div>
      </div>
      <div class="area-text-block"><h5>Descripción de lo observado</h5><p>${esc(r.descripcion||"Sin descripción")}</p></div>
      ${r.observaciones?`<div class="area-text-block"><h5>Observaciones</h5><p>${esc(r.observaciones)}</p></div>`:""}`;
  }

  function renderClearAreaInfo(clear) {
    const r=clear[0]||{};
    const when=r.timestamp ? df.format(new Date(r.timestamp)) : "Fecha no reportada";
    const obs=[...new Set(clear.map(x=>x.observacion_area).filter(Boolean))].join(" · ") || "No se documentaron hallazgos durante el recorrido visual de esta área.";
    return `<div class="area-clear-panel"><div class="area-clear-icon">✅</div><div><h4>Área revisada sin afectaciones observables</h4><p>${esc(obs)}</p></div></div>
      <div class="finding-form-grid area-clear-meta">
        <div class="finding-form-field"><small>Resultado</small><b>${esc(r.resultado||"Sin afectación observable")}</b></div>
        <div class="finding-form-field"><small>Fecha / hora</small><b>${esc(when)}</b></div>
        <div class="finding-form-field"><small>Registros del área</small><b>${clear.length}</b></div>
      </div>`;
  }

  function renderPhotoViewer(r, contextLabel="Hallazgo seleccionado") {
    const media=r?.fotos||[];
    if(!media.length) return `<div class="area-photo-title-row"><div><h4>Evidencia multimedia</h4><span>${esc(contextLabel)}</span></div></div><div class="photo-empty"><div class="icon">📎</div><strong>Sin evidencias asociadas</strong><span>No se registraron fotografías o videos para este registro.</span></div>`;
    detailPhotoIndex=Math.max(0,Math.min(detailPhotoIndex,media.length-1));
    const e=media[detailPhotoIndex];
    const src=evidenceCandidates(e)[0]||"";
    const isVideo=evidenceType(e)==="video";
    const compatible=e?.browser_compatible!==false;
    let main="";
    if(isVideo){
      main = compatible
        ? `<video id="areaMediaMain" class="area-photo-video" controls preload="metadata" playsinline src="${esc(src)}"></video>`
        : `<div id="areaMediaMain" class="video-incompatible"><div class="icon">🎬</div><strong>Video QuickTime pendiente de conversión</strong><span>Conviértalo a MP4 mediante IMPORTAR_EVIDENCIAS.bat antes de publicar.</span></div>`;
    }else{
      const attrs=candidateImageAttrs(e,`id="areaMediaMain" class="area-photo-img" data-photo-index="${detailPhotoIndex}" alt="Evidencia ${detailPhotoIndex+1}"`);
      main=`<img ${attrs}><div class="photo-stage-fallback"><span>📷 Evidencia pendiente de sincronizar con el tablero.</span></div>`;
    }
    const thumbs=media.map((ev,i)=>{
      const active=i===detailPhotoIndex?"active":"";
      if(evidenceType(ev)==="video") return `<button type="button" class="photo-thumb video-thumb ${active}" data-photo-index="${i}" title="Video ${i+1}"><span>🎬</span><small>Video</small></button>`;
      return `<button type="button" class="photo-thumb ${active}" data-photo-index="${i}" title="Imagen ${i+1}"><img class="area-photo-img" ${candidateImageAttrs(ev,`alt="Miniatura ${i+1}"`)}><span class="photo-thumb-fallback" style="display:none">📷</span></button>`;
    }).join("");
    const nVideos=media.filter(x=>evidenceType(x)==="video").length;
    const nImages=media.length-nVideos;
    const countLabel=[nImages?`${nImages} foto${nImages===1?"":"s"}`:"",nVideos?`${nVideos} video${nVideos===1?"":"s"}`:""].filter(Boolean).join(" · ");
    return `<div class="area-photo-title-row"><div><h4>Evidencia multimedia</h4><span>${esc(contextLabel)}</span></div><span>${countLabel}</span></div>
      <div class="photo-stage">
        <button id="btnPrevPhoto" class="photo-nav-btn photo-nav-prev" type="button" ${detailPhotoIndex<=0?"disabled":""} aria-label="Evidencia anterior">‹</button>
        ${main}
        <button id="btnNextPhoto" class="photo-nav-btn photo-nav-next" type="button" ${detailPhotoIndex>=media.length-1?"disabled":""} aria-label="Evidencia siguiente">›</button>
      </div>
      <div class="photo-view-footer"><span class="photo-counter">${detailPhotoIndex+1} / ${media.length} · ${isVideo?"Video":"Fotografía"}</span>${src?`<a class="photo-open-link" href="${esc(src)}" target="_blank" rel="noopener">Abrir archivo ↗</a>`:""}</div>
      <div class="photo-thumbs">${thumbs}</div>`;
  }

  function bindCandidateImage(img) {
    if(!img)return;
    img.addEventListener("error",()=>{
      let candidates=[]; try{candidates=JSON.parse(decodeURIComponent(img.dataset.candidates||"%5B%5D"));}catch(_){}
      const next=(Number(img.dataset.candidateIndex)||0)+1;
      if(next<candidates.length){img.dataset.candidateIndex=String(next);img.src=candidates[next];return;}
      img.style.display="none";
      const fallback=img.nextElementSibling;
      if(fallback && (fallback.classList.contains("photo-stage-fallback")||fallback.classList.contains("photo-thumb-fallback"))) fallback.style.display=fallback.classList.contains("photo-stage-fallback")?"flex":"flex";
    });
  }

  function bindAreaDetailEvents(box, hall, viewerRecord=null) {
    box.querySelectorAll(".finding-switch-btn").forEach(btn=>btn.addEventListener("click",()=>{
      detailFindingIndex=Number(btn.dataset.findingIndex)||0; detailPhotoIndex=0; renderAreaDetail();
    }));
    const prev=$("btnPrevPhoto"), next=$("btnNextPhoto");
    if(prev)prev.addEventListener("click",()=>{detailPhotoIndex=Math.max(0,detailPhotoIndex-1);renderAreaDetail();});
    if(next)next.addEventListener("click",()=>{detailPhotoIndex+=1;renderAreaDetail();});
    box.querySelectorAll(".photo-thumb").forEach(btn=>btn.addEventListener("click",()=>{detailPhotoIndex=Number(btn.dataset.photoIndex)||0;renderAreaDetail();}));
    box.querySelectorAll(".area-photo-img").forEach(bindCandidateImage);
    const main=$("areaMediaMain");
    if(main && main.tagName==="IMG"){main.addEventListener("click",()=>{const r=viewerRecord || hall[detailFindingIndex];const p=r?.fotos?.[detailPhotoIndex];if(p)openEvidence(p);});}
  }

  function renderAreaDetail() {
    const box=$("areaDetail"); if(!box)return;
    detailSede=$("dSede")?.value||""; detailArea=$("dArea")?.value||"";
    if(!detailSede||!detailArea){box.innerHTML=`<div class="area-empty-state">Seleccione un Área Operativa y un área para consultar su información.</div>`;updateAreaNavButtons();return;}
    const rr=detailRecordsForArea(detailSede,detailArea).sort((a,b)=>String(a.timestamp).localeCompare(String(b.timestamp)));
    if(!rr.length){box.innerHTML=`<div class="area-empty-state">No se encontraron registros para el área seleccionada.</div>`;updateAreaNavButtons();return;}
    const s=areaSummary(rr), hall=rr.filter(r=>r.es_hallazgo), clear=rr.filter(r=>!r.es_hallazgo);
    detailFindingIndex=Math.max(0,Math.min(detailFindingIndex,Math.max(0,hall.length-1)));
    const active=hall[detailFindingIndex]||null;
    if(active) detailPhotoIndex=Math.max(0,Math.min(detailPhotoIndex,Math.max(0,(active.fotos||[]).length-1)));
    const stateClass=s.priority?"area-status-priority":s.findings?"area-status-findings":"area-status-clear";
    const stateText=s.priority?"Atención prioritaria":s.findings?"Con hallazgos":"Sin afectación observable";
    const info=active?renderFindingInfo(active,hall):renderClearAreaInfo(clear);
    const clearMedia=clear.flatMap(r=>r.fotos||[]);
    const clearViewerRecord=clear.length?{...clear[0], fotos:clearMedia}:null;
    if(!active) detailPhotoIndex=Math.max(0,Math.min(detailPhotoIndex,Math.max(0,clearMedia.length-1)));
    const viewerRecord=active || clearViewerRecord;
    const photos=active?renderPhotoViewer(active,"Hallazgo seleccionado"):(clearMedia.length?renderPhotoViewer(clearViewerRecord,"Evidencia del área revisada"):`<div class="area-photo-title-row"><div><h4>Evidencia multimedia</h4><span>Área seleccionada</span></div></div><div class="photo-empty"><div class="icon">✅</div><strong>Sin evidencia asociada</strong><span>El área fue registrada sin afectaciones observables.</span></div>`);
    const areaNotes=[...new Set(clear.map(r=>r.observacion_area).filter(Boolean))];
    const note=active&&areaNotes.length?`<div class="area-observation"><strong>Otro registro del área:</strong> ${areaNotes.map(esc).join(" · ")}</div>`:"";
    box.innerHTML=`<div class="area-detail-head"><div><div class="module-eyebrow">${esc(detailSede)}</div><h3 class="area-detail-title">${esc(detailArea)}</h3><div class="area-detail-subtitle">${s.records} registro${s.records===1?"":"s"} · ${s.findings} hallazgo${s.findings===1?"":"s"} · ${s.photos} evidencia${s.photos===1?"":"s"}</div></div><span class="area-status-badge ${stateClass}">${esc(stateText)}</span></div>
      <div class="area-focus-grid"><div class="area-info-panel">${info}${note}</div><div class="area-photo-panel">${photos}</div></div>`;
    bindAreaDetailEvents(box,hall,viewerRecord); updateAreaNavButtons();
  }

  function updateAreaNavButtons() {
    const prev=$("btnPrevArea"), next=$("btnNextArea"); if(!prev||!next)return;
    const areas=detailSede?detailAreasForSede(detailSede):[]; const idx=areas.indexOf(detailArea);
    prev.disabled=idx<=0; next.disabled=idx<0||idx>=areas.length-1;
  }

  function moveArea(delta) {
    const areas=detailSede?detailAreasForSede(detailSede):[]; const idx=areas.indexOf(detailArea); const ni=idx+delta;
    if(ni<0||ni>=areas.length)return; $("dArea").value=areas[ni]; detailArea=areas[ni]; detailFindingIndex=0; detailPhotoIndex=0; renderAreaDetail();
  }

  function openAreaFromFinding(id) {
    const r=DATA.find(x=>x.id===id); if(!r)return;
    detailSede=r.sede; detailArea=r.area; detailFindingIndex=0; detailPhotoIndex=0; populateDetailSede(); $("dSede").value=r.sede; populateDetailArea(r.area); $("dArea").value=r.area; renderAreaDetail();
    setTimeout(()=>$("areaDetail")?.scrollIntoView({behavior:"smooth",block:"start"}),120);
  }

  function reportScopeSede() {
    return $("dSede")?.value || $("fSede")?.value || "";
  }

  function reportRecords() {
    const sede=reportScopeSede();
    return sede ? DATA.filter(r=>r.sede===sede) : DATA.slice();
  }

  function filteredTitle() {
    return reportScopeSede() || "Consolidado de sedes inspeccionadas";
  }

  function priorityScore(r) {
    const level=norm(r?.nivel);
    return (r?.riesgo_si?1000:0)
      +(level==="alta"?500:0)
      +(r?.revision_si?200:0)
      +(level==="moderada"?80:0)
      +(level==="leve"?20:0)
      +((r?.n_fotos||0)>0?5:0);
  }

  function prioritize(records) {
    return records.filter(r=>r.es_hallazgo).sort((a,b)=>
      priorityScore(b)-priorityScore(a)
      || String(a.area||"").localeCompare(String(b.area||""),"es")
    );
  }

  function priorityAction(r) {
    const level=norm(r?.nivel);
    if(r?.riesgo_si && level==="alta") return "Valoración técnica prioritaria";
    if(r?.riesgo_si) return "Control preventivo y valoración";
    if(level==="alta" && r?.revision_si) return "Valoración técnica prioritaria";
    if(level==="alta") return "Valoración técnica";
    if(r?.revision_si) return "Revisión técnica";
    if(level==="moderada") return "Seguimiento técnico";
    return "Seguimiento";
  }

  function predominant(records, field) {
    const c={}; records.filter(r=>r.es_hallazgo).forEach(r=>{const k=r[field]||"Sin clasificar";c[k]=(c[k]||0)+1;});
    return Object.entries(c).sort((a,b)=>b[1]-a[1])[0]?.[0] || "Sin hallazgos";
  }

  function executiveText(records) {
    const sede=reportScopeSede() || "el área operativa seleccionada";
    const m=metrics(records); const hall=records.filter(r=>r.es_hallazgo);
    const levelCounts = {Leve:0,Moderada:0,Alta:0,"Por determinar":0};
    hall.forEach(r=>{const k=r.nivel||"Por determinar";levelCounts[k]=(levelCounts[k]||0)+1;});
    const damage=predominant(records,"tipo_dano");
    const element=predominant(records,"elemento_ajustado");

    let result=`En el recorrido de ${sede} se inspeccionaron ${m.areas} áreas. `;
    result+=`${m.affectedAreas} presentaron uno o más hallazgos y ${m.clear} no evidenciaron afectaciones observables durante la inspección visual. `;
    if(m.findings){
      result+=`Se documentaron ${m.findings} hallazgos: ${levelCounts.Alta||0} de nivel Alto, ${levelCounts.Moderada||0} Moderado y ${levelCounts.Leve||0} Leve. `;
      result+=`${m.risk} registro(s) reportan riesgo inmediato y ${m.review} requieren revisión técnica especializada.`;
    } else {
      result+="No se registraron hallazgos en las áreas recorridas.";
    }

    const predominance=m.findings
      ? `El tipo de daño observado con mayor frecuencia es ${damage.toLowerCase()} y el componente registrado con mayor frecuencia es ${String(element).toLowerCase()}.`
      : "No se identificaron afectaciones visibles que requieran clasificación de daño.";

    let conclusion;
    if(m.risk || m.high){
      conclusion="Se recomienda priorizar la valoración técnica de los puntos críticos identificados, especialmente aquellos con afectación visual Alta y/o riesgo inmediato reportado. Mantener medidas preventivas y restricciones temporales de uso cuando las condiciones observadas así lo ameriten, hasta contar con valoración especializada.";
    } else if(m.review){
      conclusion="No se identificaron afectaciones visuales de nivel Alto ni riesgo inmediato; sin embargo, se recomienda gestionar la revisión técnica de los registros señalados y mantener seguimiento de su evolución.";
    } else if(m.findings){
      conclusion="No se identificaron afectaciones visuales de nivel Alto ni situaciones de riesgo inmediato. Se recomienda mantener seguimiento de los hallazgos documentados y registrar cualquier cambio observado.";
    } else {
      conclusion="Durante el recorrido no se identificaron afectaciones observables. Se recomienda conservar la evidencia del estado inspeccionado y realizar seguimiento ante cualquier cambio posterior.";
    }
    return {result,predominance,conclusion};
  }

  function renderReportPreview() {
    if (!$("reportPreview")) return;
    const records=reportRecords(); const m=metrics(records); const text=executiveText(records); const priorities=prioritize(records).slice(0,6);
    const date = META?.procesado_en ? new Date(META.procesado_en) : new Date();
    $("reportPreview").innerHTML = `<div class="report-header"><div class="module-eyebrow">UESVALLE</div><h2>Informe ejecutivo · Inspección visual post-sismo</h2><div class="report-meta">${esc(filteredTitle())} · Corte de información: ${esc(new Intl.DateTimeFormat("es-CO",{day:"numeric",month:"long",year:"numeric"}).format(date))}</div></div>
      <div class="report-kpis">
        <div class="report-kpi"><b>${m.areas}</b><span>Áreas inspeccionadas</span></div><div class="report-kpi"><b>${m.findings}</b><span>Hallazgos</span></div><div class="report-kpi"><b>${m.clear}</b><span>Sin afectación</span></div><div class="report-kpi"><b>${m.high}</b><span>Nivel Alto</span></div><div class="report-kpi"><b>${m.risk}</b><span>Riesgo inmediato</span></div><div class="report-kpi"><b>${m.review}</b><span>Revisión técnica</span></div>
      </div>
      <h3>Resultado</h3><p>${esc(text.result)}</p><p>${esc(text.predominance)}</p>
      <h3>Hallazgos prioritarios</h3>${priorities.length?`<div class="table-responsive"><table class="table table-sm"><thead><tr><th>Área</th><th>Hallazgo</th><th>Nivel</th><th>Riesgo</th><th>Revisión</th></tr></thead><tbody>${priorities.map(r=>`<tr><td>${esc(r.area)}</td><td>${esc(r.tipo_dano||r.elemento_ajustado||"")}</td><td>${esc(r.nivel||"")}</td><td>${esc(r.riesgo_inmediato||"")}</td><td>${esc(r.revision_tecnica||"")}</td></tr>`).join("")}</tbody></table></div>`:`<p class="text-muted">No se identifican hallazgos en el universo filtrado.</p>`}
      <h3>Conclusión y recomendación</h3><p>${esc(text.conclusion)}</p>
      <div class="report-note"><strong>Alcance:</strong> los resultados corresponden a una inspección visual preliminar y no constituyen diagnóstico de estabilidad ni evaluación estructural definitiva. La clasificación técnica normalizada se utiliza para presentar de forma consistente los hallazgos observados.</div>`;
  }

  async function normalizePhotoBlobForPdf(blob) {
    // Chrome ya interpreta la orientación EXIF al mostrar las evidencias
    // del tablero. Para el PDF se rasteriza esa misma orientación una sola vez.
    if("createImageBitmap" in window){
      try{
        const bitmap=await createImageBitmap(blob,{imageOrientation:"from-image"});
        const canvas=document.createElement("canvas");
        canvas.width=Math.max(1,bitmap.width);
        canvas.height=Math.max(1,bitmap.height);
        const ctx=canvas.getContext("2d",{alpha:false});
        ctx.fillStyle="#ffffff";
        ctx.fillRect(0,0,canvas.width,canvas.height);
        ctx.drawImage(bitmap,0,0,canvas.width,canvas.height);
        bitmap.close?.();
        return {data:canvas.toDataURL("image/jpeg",0.94),width:canvas.width,height:canvas.height};
      }catch(_){ /* fallback compatible con Chrome */ }
    }

    const objectUrl=URL.createObjectURL(blob);
    try{
      const img=await new Promise((resolve,reject)=>{
        const el=new Image();
        el.decoding="async";
        el.onload=()=>resolve(el);
        el.onerror=reject;
        el.src=objectUrl;
      });
      const w=Math.max(1,img.naturalWidth||img.width);
      const h=Math.max(1,img.naturalHeight||img.height);
      const canvas=document.createElement("canvas");
      canvas.width=w;
      canvas.height=h;
      const ctx=canvas.getContext("2d",{alpha:false});
      ctx.fillStyle="#ffffff";
      ctx.fillRect(0,0,w,h);
      ctx.drawImage(img,0,0,w,h);
      return {data:canvas.toDataURL("image/jpeg",0.94),width:w,height:h};
    } finally {
      URL.revokeObjectURL(objectUrl);
    }
  }

  async function loadImageData(photo) {
    const candidates = evidenceCandidates(photo);
    for (const url of candidates) {
      try {
        const res = await fetch(url, {mode:"cors"});
        if(!res.ok) continue;
        const blob=await res.blob();
        if(!blob.type.startsWith("image/")) continue;
        return await normalizePhotoBlobForPdf(blob);
      } catch (_) {}
    }
    return null;
  }

  function addImageFit(doc,image,x,y,maxW,maxH) {
    if(!image?.data) return false;
    const iw=Math.max(1,image.width||1), ih=Math.max(1,image.height||1);
    const scale=Math.min(maxW/iw,maxH/ih);
    const w=iw*scale, h=ih*scale;
    const ix=x+(maxW-w)/2, iy=y+(maxH-h)/2;
    try{
      const type=image.data.startsWith("data:image/png")?"PNG":"JPEG";
      doc.addImage(image.data,type,ix,iy,w,h,undefined,"FAST");
      return true;
    }catch(_){ return false; }
  }

  async function loadStaticImageData(url) {
    try {
      const res=await fetch(url,{cache:"no-store"});
      if(!res.ok) return null;
      const blob=await res.blob();
      if(!blob.type.startsWith("image/")) return null;
      return await new Promise((resolve,reject)=>{const fr=new FileReader();fr.onload=()=>resolve(fr.result);fr.onerror=reject;fr.readAsDataURL(blob);});
    } catch (_) { return null; }
  }

  function criticalPhotoItems(records, limit=3) {
    const ordered=prioritize(records);
    const seenAreas=new Set();
    const items=[];
    for(const r of ordered){
      const areaKey=`${r.sede||""}::${r.area||""}`;
      if(seenAreas.has(areaKey)) continue;
      const photo=(r.fotos||[]).find(p=>evidenceType(p)==="imagen");
      if(!photo) continue;
      seenAreas.add(areaKey);
      items.push({p:photo,r});
      if(items.length>=limit) break;
    }
    return items;
  }

  function wrapText(doc,text,width){ return doc.splitTextToSize(String(text||""),width); }

  async function generatePdf() {
    if (!window.jspdf?.jsPDF) {
      alert("No fue posible cargar la librería PDF.");
      return;
    }

    const sede=reportScopeSede();
    if(!sede){
      alert("Seleccione un Área Operativa en el bloque Detalle por área antes de generar el informe.");
      $("dSede")?.focus();
      return;
    }

    const {jsPDF}=window.jspdf;
    const doc=new jsPDF({unit:"mm",format:"a4"});
    const BLUE=[11,79,138];
    const DARK=[39,52,61];
    const MUTED=[76,88,97];
    const records=reportRecords();
    const mtr=metrics(records);
    const text=executiveText(records);
    const priority=prioritize(records).slice(0,6);
    const date=META?.procesado_en ? new Date(META.procesado_en) : new Date();
    const dateText=new Intl.DateTimeFormat("es-CO",{day:"numeric",month:"long",year:"numeric"}).format(date);
    const headerLogo=await loadStaticImageData(PDF_HEADER_LOGO_URL);

    // Tipografía única del informe: Helvetica. Cambia solo tamaño/peso por jerarquía.
    const bodyFont=9.2;
    const sectionFont=12;
    const evidenceTitleFont=10.5;

    const drawInstitutionalLogo=(topY=8)=>{
      if(!headerLogo) return topY;
      try{
        const type=headerLogo.startsWith("data:image/png")?"PNG":"JPEG";
        // Franja institucional compacta: identidad sin competir con el contenido.
        const w=118, h=18.58, x=(210-w)/2;
        doc.addImage(headerLogo,type,x,topY,w,h,undefined,"FAST");
        return topY+h;
      }catch(_){ return topY; }
    };

    const drawHeader=()=>{
      let y=drawInstitutionalLogo(7);
      y+=10; // separación armónica entre logo y título
      doc.setFont("helvetica","bold");
      doc.setFontSize(17);
      doc.setTextColor(...BLUE);
      const title=`Informe Recorrido Área Operativa ${sede}`;
      const titleLines=wrapText(doc,title,182);
      doc.text(titleLines,14,y);
      y+=titleLines.length*6.4+1.5;

      doc.setFont("helvetica","normal");
      doc.setFontSize(bodyFont);
      doc.setTextColor(...MUTED);
      doc.text(`Fecha: ${dateText}`,14,y);
      y+=6;
      doc.setDrawColor(...BLUE);
      doc.setLineWidth(.7);
      doc.line(14,y,196,y);
      return y+8;
    };

    const sectionTitle=(title,y)=>{
      doc.setFont("helvetica","bold");
      doc.setFontSize(sectionFont);
      doc.setTextColor(...BLUE);
      doc.text(title,14,y);
      return y+6;
    };

    const bodyText=(value,y,width=182)=>{
      doc.setFont("helvetica","normal");
      doc.setFontSize(bodyFont);
      doc.setTextColor(...DARK);
      const lines=wrapText(doc,value,width);
      doc.text(lines,14,y);
      return y+lines.length*4.45;
    };

    let y=drawHeader();

    // Indicadores.
    y=sectionTitle("Indicadores del recorrido",y);
    doc.autoTable({
      startY:y,
      theme:"grid",
      styles:{font:"helvetica",fontSize:9,cellPadding:2.4,halign:"center",textColor:DARK},
      headStyles:{fillColor:BLUE,textColor:[255,255,255],fontStyle:"bold",fontSize:9.2},
      head:[["Áreas","Hallazgos","Sin afectación","Alta","Riesgo inmediato"]],
      body:[[mtr.areas,mtr.findings,mtr.clear,mtr.high,mtr.risk]],
      margin:{left:14,right:14}
    });
    y=doc.lastAutoTable.finalY+8;

    // Resultado.
    y=sectionTitle("Resultado del recorrido",y);
    y=bodyText(`${text.result} ${text.predominance}`,y)+7;

    // Puntos críticos.
    y=sectionTitle("Puntos críticos priorizados",y);
    if(priority.length){
      doc.autoTable({
        startY:y,
        theme:"striped",
        styles:{font:"helvetica",fontSize:8.5,cellPadding:2,valign:"middle",textColor:DARK},
        headStyles:{fillColor:BLUE,textColor:[255,255,255],fontStyle:"bold",fontSize:8.7},
        head:[["Área","Hallazgo principal","Nivel","Riesgo","Acción"]],
        body:priority.map(r=>[
          r.area||"",
          r.tipo_dano||r.elemento_ajustado||"",
          r.nivel||"",
          r.riesgo_inmediato||"",
          priorityAction(r)
        ]),
        columnStyles:{
          0:{cellWidth:38},1:{cellWidth:48},2:{cellWidth:20,halign:"center"},
          3:{cellWidth:20,halign:"center"},4:{cellWidth:56}
        },
        margin:{left:14,right:14}
      });
      y=doc.lastAutoTable.finalY+9;
    }else{
      y=bodyText("No se identificaron hallazgos que requieran priorización en el recorrido.",y)+7;
    }

    if(y>230){ doc.addPage(); y=drawHeader(); }

    // Conclusión.
    y=sectionTitle("Conclusión y recomendación",y);
    y=bodyText(text.conclusion,y)+9;

    // Alcance técnico con la misma jerarquía de títulos.
    y=sectionTitle("Alcance técnico",y);
    bodyText(
      "Los resultados corresponden a una inspección visual preliminar y no constituyen diagnóstico de estabilidad ni evaluación estructural definitiva. La clasificación técnica normalizada se utiliza para presentar de forma consistente los hallazgos observados.",
      y
    );

    // Página de evidencia crítica: una fotografía por área crítica.
    const candidates=criticalPhotoItems(records,3);
    const loaded=[];
    for(const item of candidates){
      const image=await loadImageData(item.p);
      if(image) loaded.push({...item,image});
    }

    if(loaded.length){
      doc.addPage();
      let py=drawInstitutionalLogo(7)+8;

      doc.setFont("helvetica","bold");
      doc.setFontSize(15);
      doc.setTextColor(...BLUE);
      doc.text(`Evidencia de puntos críticos - ${sede}`,14,py);
      py+=7;
      doc.setDrawColor(...BLUE);
      doc.setLineWidth(.7);
      doc.line(14,py,196,py);
      py+=8;

      for(const item of loaded){
        if(py>226){
          doc.addPage();
          py=15;
        }

        const r=item.r;
        const cardH=63;
        doc.setFillColor(246,249,251);
        doc.roundedRect(14,py,182,cardH,2,2,"F");

        // Nombre de cada punto crítico claramente diferenciado.
        doc.setFont("helvetica","bold");
        doc.setFontSize(evidenceTitleFont);
        doc.setTextColor(...BLUE);
        doc.text(r.area||"Área priorizada",18,py+7);

        doc.setFont("helvetica","bold");
        doc.setFontSize(8.8);
        doc.setTextColor(...DARK);
        doc.text(`Nivel: ${r.nivel||"Por determinar"}   |   Riesgo inmediato: ${r.riesgo_inmediato||"No"}`,18,py+13);

        // Imagen EXIF-normalizada, sin deformación y centrada en su caja.
        addImageFit(doc,item.image,18,py+17,64,40);

        doc.setFont("helvetica","bold");
        doc.setFontSize(9.6);
        doc.setTextColor(...BLUE);
        doc.text("Hallazgo observado",88,py+20);

        doc.setFont("helvetica","normal");
        doc.setFontSize(9);
        doc.setTextColor(...DARK);
        const desc=wrapText(doc,r.descripcion||r.tipo_dano||r.elemento_ajustado||"Hallazgo visual documentado.",102);
        doc.text(desc.slice(0,6),88,py+25);

        doc.setFont("helvetica","bold");
        doc.setFontSize(9.6);
        doc.setTextColor(...BLUE);
        doc.text("Acción sugerida",88,py+47);

        doc.setFont("helvetica","normal");
        doc.setFontSize(9);
        doc.setTextColor(...DARK);
        doc.text(wrapText(doc,priorityAction(r),102).slice(0,3),88,py+52);

        py+=68;
      }
    }

    const safe=sede.replace(/[^a-zA-Z0-9áéíóúÁÉÍÓÚñÑ_-]+/g,"_");
    doc.save(`Informe_Recorrido_Area_Operativa_${safe}.pdf`);
  }



  function areaPdfRecords() {
    const sede=$("dSede")?.value||"";
    const area=$("dArea")?.value||"";
    return sede && area ? DATA.filter(r=>r.sede===sede && r.area===area) : [];
  }

  function areaPdfPhotos(records, limit=3) {
    const out=[];
    const seen=new Set();
    for(const r of records){
      for(const p of (r.fotos||[])){
        if(evidenceType(p)!=="imagen") continue;
        const key=p.id_evidencia || evidenceCandidates(p)[0] || `${r.id}-${out.length}`;
        if(seen.has(key)) continue;
        seen.add(key);
        out.push({p,r});
        if(out.length>=limit) return out;
      }
    }
    return out;
  }

  async function generateAreaPdf() {
    if (!window.jspdf?.jsPDF) {
      alert("No fue posible cargar la librería PDF.");
      return;
    }

    const sede=$("dSede")?.value||"";
    const area=$("dArea")?.value||"";
    if(!sede || !area){
      alert("Seleccione primero un Área Operativa y un área inspeccionada para generar la ficha.");
      (!$("dSede")?.value ? $("dSede") : $("dArea"))?.focus();
      return;
    }

    const records=areaPdfRecords();
    if(!records.length){
      alert("No se encontraron registros para el área seleccionada.");
      return;
    }

    const {jsPDF}=window.jspdf;
    const doc=new jsPDF({unit:"mm",format:"a4"});
    const BLUE=[11,79,138];
    const DARK=[39,52,61];
    const MUTED=[76,88,97];
    const headerLogo=await loadStaticImageData(PDF_HEADER_LOGO_URL);
    const hall=records.filter(r=>r.es_hallazgo);
    const clear=records.filter(r=>!r.es_hallazgo);
    const summary=areaSummary(records);
    const active=prioritize(hall)[0] || records[0];
    const dateRaw=active?.timestamp || active?.fecha_inspeccion || META?.procesado_en || new Date().toISOString();
    const date=new Date(dateRaw);
    const dateText=Number.isNaN(date.getTime()) ? String(active?.fecha_inspeccion||"") :
      new Intl.DateTimeFormat("es-CO",{day:"numeric",month:"long",year:"numeric"}).format(date);

    const drawLogo=(topY=7)=>{
      if(!headerLogo) return topY;
      try{
        const type=headerLogo.startsWith("data:image/png")?"PNG":"JPEG";
        const w=118,h=18.58,x=(210-w)/2;
        doc.addImage(headerLogo,type,x,topY,w,h,undefined,"FAST");
        return topY+h;
      }catch(_){ return topY; }
    };

    const section=(title,y)=>{
      doc.setFont("helvetica","bold");
      doc.setFontSize(11.5);
      doc.setTextColor(...BLUE);
      doc.text(title,14,y);
      return y+6;
    };

    const paragraph=(text,y,width=182)=>{
      doc.setFont("helvetica","normal");
      doc.setFontSize(9.2);
      doc.setTextColor(...DARK);
      const lines=wrapText(doc,text||"",width);
      doc.text(lines,14,y);
      return y+lines.length*4.5;
    };

    let y=drawLogo(7)+10;
    doc.setFont("helvetica","bold");
    doc.setFontSize(16);
    doc.setTextColor(...BLUE);
    doc.text(`Ficha de inspección - ${sede}`,14,y);
    y+=7;

    doc.setFont("helvetica","bold");
    doc.setFontSize(13);
    doc.setTextColor(...DARK);
    doc.text(area,14,y);
    y+=6;

    doc.setFont("helvetica","normal");
    doc.setFontSize(9.2);
    doc.setTextColor(...MUTED);
    doc.text(`Fecha: ${dateText}`,14,y);
    y+=5;
    doc.setDrawColor(...BLUE);
    doc.setLineWidth(.7);
    doc.line(14,y,196,y);
    y+=8;

    const condition=hall.length ? "Con hallazgo" : "Sin afectación observable";
    const level=hall.length ? (active.nivel||"Por determinar") : "No aplica";
    const risk=hall.length ? (active.riesgo_inmediato||"No") : "No";
    const review=hall.length ? (active.revision_tecnica||"No") : "No";

    doc.autoTable({
      startY:y,
      theme:"grid",
      styles:{font:"helvetica",fontSize:9,cellPadding:2.3,textColor:DARK},
      headStyles:{fillColor:BLUE,textColor:[255,255,255],fontStyle:"bold"},
      head:[["Condición","Nivel","Riesgo inmediato","Revisión técnica"]],
      body:[[condition,level,risk,review]],
      margin:{left:14,right:14}
    });
    y=doc.lastAutoTable.finalY+8;

    if(hall.length){
      y=section("Hallazgo observado",y);
      const rows=[
        ["Componente",active.componente_ajustado||"Por determinar"],
        ["Elemento observado",active.elemento_ajustado||"Por determinar"],
        ["Tipo de daño",active.tipo_dano||"Por determinar"],
        ["Dimensiones",active.dimensiones||"No registradas"],
        ["Extensión",active.extension||"No registrada"]
      ];
      doc.autoTable({
        startY:y,
        theme:"plain",
        styles:{font:"helvetica",fontSize:9,cellPadding:1.3,textColor:DARK},
        columnStyles:{0:{cellWidth:42,fontStyle:"bold",textColor:BLUE},1:{cellWidth:140}},
        body:rows,
        margin:{left:14,right:14}
      });
      y=doc.lastAutoTable.finalY+5;

      if(active.descripcion){
        y=section("Descripción",y);
        y=paragraph(active.descripcion,y)+5;
      }
      if(active.observaciones){
        y=section("Observaciones",y);
        y=paragraph(active.observaciones,y)+5;
      }
      y=section("Acción sugerida",y);
      y=paragraph(priorityAction(active),y)+6;
    }else{
      y=section("Resultado de la revisión",y);
      const note=[...new Set(clear.map(r=>r.observacion_area).filter(Boolean))].join(" · ")
        || "Área revisada sin afectaciones observables durante el recorrido.";
      y=paragraph(note,y)+6;
    }

    const mediaCount=records.reduce((n,r)=>n+(r.fotos||[]).length,0);
    const videoCount=records.reduce((n,r)=>n+(r.fotos||[]).filter(p=>evidenceType(p)==="video").length,0);
    const photoItems=areaPdfPhotos(records,3);
    const loaded=[];
    for(const item of photoItems){
      const image=await loadImageData(item.p);
      if(image) loaded.push({...item,image});
    }

    if(loaded.length){
      if(y>205){ doc.addPage(); y=20; }
      y=section("Evidencia fotográfica",y);
      const gap=4;
      const boxW=(182-gap*2)/3;
      const boxH=48;
      loaded.forEach((item,i)=>{
        const x=14+i*(boxW+gap);
        doc.setFillColor(246,249,251);
        doc.roundedRect(x,y,boxW,boxH,1.5,1.5,"F");
        addImageFit(doc,item.image,x+2,y+2,boxW-4,boxH-4);
      });
      y+=boxH+6;
    }

    if(videoCount){
      doc.setFont("helvetica","italic");
      doc.setFontSize(8.5);
      doc.setTextColor(...MUTED);
      doc.text(`Evidencia adicional: ${videoCount} video${videoCount===1?"":"s"} disponible${videoCount===1?"":"s"} en el tablero.`,14,y);
      y+=6;
    }

    y=section("Alcance técnico",y);
    paragraph(
      "La ficha corresponde a una inspección visual preliminar y no constituye diagnóstico de estabilidad ni evaluación estructural definitiva.",
      y
    );

    const safeSede=sede.replace(/[^a-zA-Z0-9áéíóúÁÉÍÓÚñÑ_-]+/g,"_");
    const safeArea=area.replace(/[^a-zA-Z0-9áéíóúÁÉÍÓÚñÑ_-]+/g,"_");
    doc.save(`Ficha_Inspeccion_${safeSede}_${safeArea}.pdf`);
  }


  function publicEvidencePath(path) {
    const p=String(path||"").replace(/\\/g,"/").replace(/^\/+/,"");
    if(!p) return "";
    if(p.startsWith("../../")) return p;
    if(p.startsWith("data/")) return `../../${p}`;
    return p;
  }

  function applyComplementaryEvidence(manifest) {
    if(!manifest?.areas?.length) return 0;
    let added=0;
    for(const areaEntry of manifest.areas){
      const record=DATA.find(r=>r.sede===manifest.sede && r.area===areaEntry.area && !r.es_hallazgo);
      if(!record) continue;
      const existing=new Set((record.fotos||[]).map(e=>e.id_evidencia || e.local_path));
      for(const [idx,e] of (areaEntry.evidencias||[]).entries()){
        const local=publicEvidencePath(e.archivo_local);
        const id=`COMP-${norm(manifest.sede).replace(/[^a-z0-9]+/g,"-")}-${norm(areaEntry.area).replace(/[^a-z0-9]+/g,"-")}-${idx+1}`;
        if(existing.has(id) || existing.has(local)) continue;
        (record.fotos ||= []).push({
          orden:(record.fotos?.length||0)+1,
          id_evidencia:id,
          local_path:local,
          local_candidates:[local],
          media_type:e.tipo_evidencia==="video"?"video":"imagen",
          browser_compatible:true,
          complementaria:true,
          nombre_archivo:e.nombre_archivo||""
        });
        added++;
      }
      record.n_fotos=(record.fotos||[]).length;
      record.n_evidencias=(record.fotos||[]).length;
    }
    return added;
  }
  async function loadData() {
    try {
      showStatus("Cargando información procesada…","info");
      const [dr,mr,...complementResponses]=await Promise.all([
        fetch(DATA_URL,{cache:"no-store"}),
        fetch(META_URL,{cache:"no-store"}),
        ...COMPLEMENT_URLS.map(item=>fetch(item.url,{cache:"no-store"}).catch(()=>null))
      ]);
      if(!dr.ok) throw new Error(`No se pudo cargar inspecciones.json (${dr.status})`);
      if(!mr.ok) throw new Error(`No se pudo cargar metadata.json (${mr.status})`);
      DATA=await dr.json(); META=await mr.json();

      COMPLEMENTS=[];
      const complementCounts=[];
      for(let i=0;i<complementResponses.length;i++){
        const response=complementResponses[i];
        const cfg=COMPLEMENT_URLS[i];
        if(response?.ok){
          const manifest=await response.json();
          COMPLEMENTS.push(manifest);
          const count=applyComplementaryEvidence(manifest);
          complementCounts.push(`${cfg.label}: ${count}`);
        }
      }

      populateFilters(); setUpdateBadge(); applyFilters();
      const ev=META?.evidencias||{};
      const evText=Number(ev.pendientes||0)>0 ? ` · Evidencias base locales: ${ev.locales||0}/${ev.referenciadas||0} (${ev.pendientes} pendientes)` : ` · Evidencias base: ${ev.locales ?? ev.referenciadas ?? 0}/${ev.referenciadas ?? ev.locales ?? 0}`;
      const compText=complementCounts.length?` · Complementarias ${complementCounts.join(" · ")}`:"";
      showStatus(`Carga correcta: ${DATA.length} registros. Fuente: ${META.fuente || "sin identificar"}${evText}${compText}.`, Number(ev.pendientes||0)>0 ? "warning" : "success");
    } catch(e) {
      console.error(e); showStatus(`Error al cargar datos: ${e.message}. Abra el tablero mediante el BAT para evitar restricciones de file://.`,"danger");
    }
  }

  $("btnApply").addEventListener("click",applyFilters);
  $("btnClear").addEventListener("click",clearFilters);
  $("btnClearActiveFilters").addEventListener("click",clearFilters);
  $("btnReload").addEventListener("click",()=>location.reload());
  $("btnGeneratePdf").addEventListener("click",generatePdf);
  $("btnGenerateAreaPdf").addEventListener("click",generateAreaPdf);
  $("btnToggleStatus").addEventListener("click",()=>{const box=$("loadAlert");box.classList.toggle("d-none");$("statusHint").textContent=box.classList.contains("d-none")?"Oculto":"Visible";});
  if ($("analysisCollapse")) $("analysisCollapse").addEventListener("shown.bs.collapse",()=>{Object.values(charts).forEach(c=>{try{c.resize();}catch(_){}});});
  ["fSede","fTipoDano","fNivel"].forEach(id=>$(id).addEventListener("change",applyFilters));
  $("fCondicion").addEventListener("change",()=>{
    if($("fCondicion").value==="Sin afectación observable"){
      $("fTipoDano").value="";
      $("fNivel").value="";
    }
    applyFilters();
  });

  if ($("dSede")) $("dSede").addEventListener("change",()=>{detailSede=$("dSede").value;detailArea="";detailFindingIndex=0;detailPhotoIndex=0;populateDetailArea();renderAreaDetail();renderReportPreview();});
  if ($("dArea")) $("dArea").addEventListener("change",()=>{detailArea=$("dArea").value;detailFindingIndex=0;detailPhotoIndex=0;renderAreaDetail();});
  if ($("btnPrevArea")) $("btnPrevArea").addEventListener("click",()=>moveArea(-1));
  if ($("btnNextArea")) $("btnNextArea").addEventListener("click",()=>moveArea(1));

  document.addEventListener("DOMContentLoaded", loadData);
})();
