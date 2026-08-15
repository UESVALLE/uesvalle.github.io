(() => {
  "use strict";

  const DATA_URL = "../../data/inspeccion_sedes/current/inspecciones.json";
  const META_URL = "../../data/inspeccion_sedes/current/metadata.json";
  const nf = new Intl.NumberFormat("es-CO");
  const df = new Intl.DateTimeFormat("es-CO", {day:"numeric", month:"numeric", year:"numeric", hour:"numeric", minute:"2-digit", hour12:true});

  let DATA = [];
  let FILTERED = [];
  let META = null;
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
    populateSelect("fArea", DATA.map(r=>r.area), "Todas");
    populateSelect("fNivel", DATA.filter(r=>r.es_hallazgo).map(r=>r.nivel), "Todos");
    populateSelect("fTipoDano", DATA.filter(r=>r.es_hallazgo).map(r=>r.tipo_dano), "Todos");
    populateSelect("fRevision", DATA.filter(r=>r.es_hallazgo).map(r=>r.revision_tecnica), "Todos");
  }

  function renderActiveFilters() {
    const wrap = $("activeFilters");
    const items = [
      ["Sede", $("fSede").value], ["Área", $("fArea").value], ["Nivel", $("fNivel").value], ["Tipo de daño", $("fTipoDano").value], ["Revisión", $("fRevision").value]
    ].filter(([,v]) => v);
    wrap.innerHTML = items.length ? items.map(([k,v])=>`<span class="active-filter-chip">${esc(k)}: ${esc(v)}</span>`).join("") : `<span class="text-muted small">Sin filtros adicionales</span>`;
  }

  function applyFilters() {
    const sede = $("fSede").value;
    const area = $("fArea").value;
    const nivel = $("fNivel").value;
    const tipoDano = $("fTipoDano").value;
    const revision = $("fRevision").value;
    FILTERED = DATA.filter(r =>
      (!sede || r.sede === sede) &&
      (!area || r.area === area) &&
      (!nivel || r.nivel === nivel) &&
      (!tipoDano || r.tipo_dano === tipoDano) &&
      (!revision || r.revision_tecnica === revision)
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
    ["fSede","fArea","fNivel","fTipoDano","fRevision"].forEach(id => $(id).value = "");
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
      areas: areas.length,
      affectedAreas,
      findings: hall.length,
      clear: areas.length - affectedAreas,
      high: hall.filter(r=>norm(r.nivel)==="alta").length,
      risk: hall.filter(r=>r.riesgo_si).length,
      review: hall.filter(r=>r.revision_si).length,
      photos: hall.reduce((a,r)=>a+(Number(r.n_fotos)||0),0)
    };
  }

  function renderKPIs() {
    const m = metrics();
    $("kpiAreas").textContent = nf.format(m.areas);
    if ($("kpiAreasMini")) $("kpiAreasMini").textContent = `${nf.format(m.records)} registro(s) de recorrido`;
    $("kpiFindings").textContent = nf.format(m.findings);
    $("kpiClear").textContent = nf.format(m.clear);
    $("kpiHigh").textContent = nf.format(m.high);
    $("kpiRisk").textContent = nf.format(m.risk);
    $("kpiReview").textContent = nf.format(m.review);
    $("kpiPhotos").textContent = nf.format(m.photos);
  }

  function destroyChart(name) { if (charts[name]) { charts[name].destroy(); charts[name] = null; } }

  function renderCharts() {
    const hall = FILTERED.filter(r=>r.es_hallazgo);
    const sedes = [...new Set(FILTERED.map(r=>r.sede).filter(Boolean))].sort((a,b)=>a.localeCompare(b,"es"));
    const levels = ["Leve","Moderada","Alta","Por determinar"];
    destroyChart("levels");
    charts.levels = new Chart($("chartLevels"), {
      type:"bar",
      data:{labels:sedes,datasets:levels.map(level=>({label:level,data:sedes.map(s=>hall.filter(r=>r.sede===s && (r.nivel||"Por determinar")===level).length)}))},
      options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{position:"bottom"}},scales:{x:{stacked:true},y:{stacked:true,beginAtZero:true,ticks:{precision:0}}},onHover:(evt,els)=>{evt.native.target.style.cursor=els.length?"pointer":"default";},onClick:(evt,els)=>{
        if(!els.length)return;
        const point=els[0];
        const sede=sedes[point.index];
        const level=levels[point.datasetIndex];
        const same=$("fSede").value===sede && $("fNivel").value===level;
        $("fSede").value=same?"":sede;
        $("fNivel").value=same?"":level;
        const areas=DATA.filter(r=>!$("fSede").value||r.sede===$("fSede").value).map(r=>r.area);
        populateSelect("fArea",areas,"Todas");
        $("fArea").value="";
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
        $("fArea").value="";
        applyFilters();
      }}
    });
  }

  function renderSummaryTable() {
    const tbody = $("tblSummary").querySelector("tbody");
    const sedes = [...new Set(FILTERED.map(r=>r.sede).filter(Boolean))].sort((a,b)=>a.localeCompare(b,"es"));
    tbody.innerHTML = sedes.map(sede=>{
      const rr = FILTERED.filter(r=>r.sede===sede); const m=metrics(rr);
      return `<tr data-sede="${esc(sede)}"><td><button class="btn btn-link btn-sm p-0 fw-bold summary-sede">${esc(sede)}</button></td><td>${m.areas}</td><td>${m.records}</td><td>${m.findings}</td><td>${m.clear}</td><td>${m.high}</td><td>${m.risk}</td><td>${m.review}</td><td>${m.photos}</td></tr>`;
    }).join("") || `<tr><td colspan="9" class="text-muted">Sin registros para los filtros seleccionados.</td></tr>`;
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
      photos: hall.reduce((a,r)=>a+(Number(r.n_fotos)||0),0),
      priority: hall.some(r=>r.riesgo_si || norm(r.nivel)==="alta")
    };
  }

  function hasGlobalFilters() {
    return ["fSede","fArea","fNivel","fTipoDano","fRevision"].some(id => $(id)?.value);
  }

  function detailSourceRecords() {
    return hasGlobalFilters() ? FILTERED : DATA;
  }

  function detailRecordsForArea(sede, area) {
    return detailSourceRecords().filter(r=>r.sede===sede && r.area===area);
  }

  function areaOptionLabel(sede, area) {
    const rr=detailRecordsForArea(sede, area);
    const s=areaSummary(rr);
    const icon=s.priority?"🔴":s.findings?((areaLevelOrder(s.maxLevel)>=2||s.review)?"🟠":"🟡"):"🟢";
    const suffix=s.findings?`${s.findings} hallazgo${s.findings===1?"":"s"}`:"sin hallazgos";
    return `${icon} ${area} · ${suffix}`;
  }

  function detailAreasForSede(sede) {
    return [...new Set(detailSourceRecords().filter(r=>r.sede===sede).map(r=>r.area).filter(Boolean))]
      .sort((a,b)=>a.localeCompare(b,"es"));
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
      // Prioriza automáticamente el área con mayor nivel/riesgo cuando no existe selección.
      const ranked=areas.slice().sort((a,b)=>{
        const sa=areaSummary(detailRecordsForArea(sede,a));
        const sb=areaSummary(detailRecordsForArea(sede,b));
        const score=x=>(x.risk?100:0)+(x.review?30:0)+(areaLevelOrder(x.maxLevel)*10)+x.findings;
        return score(sb)-score(sa) || a.localeCompare(b,"es");
      });
      el.value=ranked[0];
    }
    detailArea=el.value;
    updateAreaNavButtons();
  }

  function syncDetailSelectorsFromGlobal() {
    if(!$("dSede")||!$("dArea"))return;
    populateDetailSede();
    const globalSede=$("fSede").value;
    const globalArea=$("fArea").value;
    if(globalSede && $("dSede").value!==globalSede){$("dSede").value=globalSede;detailSede=globalSede;populateDetailArea(globalArea);}
    else if(!$("dSede").value){
      const sedes=[...new Set(detailSourceRecords().map(r=>r.sede).filter(Boolean))].sort((a,b)=>a.localeCompare(b,"es"));
      if(sedes.length){$("dSede").value=globalSede||sedes[0];detailSede=$("dSede").value;populateDetailArea(globalArea);}
    } else if(globalArea && detailAreasForSede($("dSede").value).includes(globalArea)) {$("dArea").value=globalArea;detailArea=globalArea;}
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

  function renderPhotoViewer(r) {
    const media=r?.fotos||[];
    if(!media.length) return `<div class="area-photo-title-row"><div><h4>Evidencia multimedia</h4><span>Área / hallazgo seleccionado</span></div></div><div class="photo-empty"><div class="icon">📎</div><strong>Sin evidencias asociadas</strong><span>No se registraron fotografías o videos para este registro.</span></div>`;
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
    return `<div class="area-photo-title-row"><div><h4>Evidencia multimedia</h4><span>Hallazgo seleccionado</span></div><span>${countLabel}</span></div>
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

  function bindAreaDetailEvents(box, hall) {
    box.querySelectorAll(".finding-switch-btn").forEach(btn=>btn.addEventListener("click",()=>{
      detailFindingIndex=Number(btn.dataset.findingIndex)||0; detailPhotoIndex=0; renderAreaDetail();
    }));
    const prev=$("btnPrevPhoto"), next=$("btnNextPhoto");
    if(prev)prev.addEventListener("click",()=>{detailPhotoIndex=Math.max(0,detailPhotoIndex-1);renderAreaDetail();});
    if(next)next.addEventListener("click",()=>{detailPhotoIndex+=1;renderAreaDetail();});
    box.querySelectorAll(".photo-thumb").forEach(btn=>btn.addEventListener("click",()=>{detailPhotoIndex=Number(btn.dataset.photoIndex)||0;renderAreaDetail();}));
    box.querySelectorAll(".area-photo-img").forEach(bindCandidateImage);
    const main=$("areaMediaMain");
    if(main && hall.length && main.tagName==="IMG"){main.addEventListener("click",()=>{const r=hall[detailFindingIndex];const p=r?.fotos?.[detailPhotoIndex];if(p)openEvidence(p);});}
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
    if(active) detailPhotoIndex=Math.max(0,Math.min(detailPhotoIndex,Math.max(0,(active.fotos||[]).length-1))); else detailPhotoIndex=0;
    const stateClass=s.priority?"area-status-priority":s.findings?"area-status-findings":"area-status-clear";
    const stateText=s.priority?"Atención prioritaria":s.findings?"Con hallazgos":"Sin afectación observable";
    const info=active?renderFindingInfo(active,hall):renderClearAreaInfo(clear);
    const photos=active?renderPhotoViewer(active):`<div class="area-photo-title-row"><div><h4>Evidencia multimedia</h4><span>Área seleccionada</span></div></div><div class="photo-empty"><div class="icon">✅</div><strong>Sin evidencia asociada</strong><span>El área fue registrada sin afectaciones observables.</span></div>`;
    const areaNotes=[...new Set(clear.map(r=>r.observacion_area).filter(Boolean))];
    const note=active&&areaNotes.length?`<div class="area-observation"><strong>Otro registro del área:</strong> ${areaNotes.map(esc).join(" · ")}</div>`:"";
    box.innerHTML=`<div class="area-detail-head"><div><div class="module-eyebrow">${esc(detailSede)}</div><h3 class="area-detail-title">${esc(detailArea)}</h3><div class="area-detail-subtitle">${s.records} registro${s.records===1?"":"s"} · ${s.findings} hallazgo${s.findings===1?"":"s"} · ${s.photos} evidencia${s.photos===1?"":"s"}</div></div><span class="area-status-badge ${stateClass}">${esc(stateText)}</span></div>
      <div class="area-kpi-grid"><div class="area-kpi"><small>Registros del área</small><b>${s.records}</b></div><div class="area-kpi"><small>Hallazgos</small><b>${s.findings}</b></div><div class="area-kpi"><small>Nivel máximo observado</small><b>${esc(s.maxLevel)}</b></div><div class="area-kpi"><small>Riesgo inmediato</small><b>${s.risk?"Sí":"No"}</b></div><div class="area-kpi"><small>Revisión técnica</small><b>${s.review?"Sí":"No"}</b></div><div class="area-kpi"><small>Evidencias</small><b>${s.photos}</b></div></div>
      <div class="area-focus-grid"><div class="area-info-panel">${info}${note}</div><div class="area-photo-panel">${photos}</div></div>`;
    bindAreaDetailEvents(box,hall); updateAreaNavButtons();
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
    const tabBtn=document.querySelector('[data-bs-target="#findings-pane"]'); if(tabBtn)bootstrap.Tab.getOrCreateInstance(tabBtn).show();
    setTimeout(()=>$("areaDetail")?.scrollIntoView({behavior:"smooth",block:"start"}),120);
  }

  function reportScopeSede() {
    return $("fSede").value || "";
  }

  function reportRecords() {
    const sede=reportScopeSede();
    return sede ? DATA.filter(r=>r.sede===sede) : DATA.slice();
  }

  function filteredTitle() {
    return reportScopeSede() || "Consolidado de sedes inspeccionadas";
  }

  function prioritize(records) {
    return records.filter(r=>r.es_hallazgo).sort((a,b)=>{
      const score = r => (r.riesgo_si?100:0)+(r.revision_si?40:0)+(r.nivel_orden*10)+(r.n_fotos||0);
      return score(b)-score(a);
    });
  }

  function predominant(records, field) {
    const c={}; records.filter(r=>r.es_hallazgo).forEach(r=>{const k=r[field]||"Sin clasificar";c[k]=(c[k]||0)+1;});
    return Object.entries(c).sort((a,b)=>b[1]-a[1])[0]?.[0] || "Sin hallazgos";
  }

  function executiveText(records) {
    const m=metrics(records); const hall=records.filter(r=>r.es_hallazgo);
    const levelCounts = {Leve:0,Moderada:0,Alta:0,"Por determinar":0}; hall.forEach(r=>{const k=r.nivel||"Por determinar";levelCounts[k]=(levelCounts[k]||0)+1;});
    const damage=predominant(records,"tipo_dano"); const element=predominant(records,"elemento_ajustado");
    let result = `Se consolidaron ${m.records} registros correspondientes a ${m.areas} áreas inspeccionadas. ${m.affectedAreas} área(s) presentan uno o más hallazgos y ${m.clear} no evidencian afectaciones observables durante el recorrido. `;
    if(m.findings) result += `En total se documentaron ${m.findings} hallazgos: ${levelCounts.Alta||0} de nivel Alto, ${levelCounts.Moderada||0} Moderado y ${levelCounts.Leve||0} Leve. `;
    result += `${m.risk} registro(s) reportan riesgo inmediato y ${m.review} requieren revisión técnica especializada.`;
    const predominance = m.findings ? `El tipo de daño predominante es ${damage.toLowerCase()} y el elemento observado con mayor frecuencia es ${String(element).toLowerCase()}.` : "No se registraron hallazgos en el universo filtrado.";
    const conclusion = m.risk || m.high ? "Se recomienda priorizar la valoración técnica de los hallazgos con afectación visual Alta y/o riesgo inmediato reportado, manteniendo medidas preventivas cuando corresponda." : m.review ? "Se recomienda gestionar la valoración técnica de los registros que fueron marcados para revisión especializada." : "Con la información visual disponible no se identifican casos que requieran priorización inmediata; se recomienda conservar el registro y realizar seguimiento si aparecen cambios.";
    return {result,predominance,conclusion};
  }

  function renderReportPreview() {
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

  async function loadImageData(photo) {
    const candidates = evidenceCandidates(photo);
    for (const url of candidates) {
      try {
        const res = await fetch(url, {mode:"cors"});
        if(!res.ok) continue;
        const blob=await res.blob();
        if(!blob.type.startsWith("image/")) continue;
        return await new Promise((resolve,reject)=>{const fr=new FileReader();fr.onload=()=>resolve(fr.result);fr.onerror=reject;fr.readAsDataURL(blob);});
      } catch (_) {}
    }
    return null;
  }

  function wrapText(doc,text,width){ return doc.splitTextToSize(String(text||""),width); }

  async function generatePdf() {
    if (!window.jspdf?.jsPDF) { alert("No fue posible cargar la librería PDF."); return; }
    const {jsPDF}=window.jspdf; const doc=new jsPDF({unit:"mm",format:"a4"});
    const records=reportRecords(); const m=metrics(records); const text=executiveText(records); const priority=prioritize(records).slice(0,6);
    const title=filteredTitle();
    let y=15;
    doc.setFont("helvetica","bold"); doc.setFontSize(9); doc.setTextColor(11,79,138); doc.text("UESVALLE",14,y); y+=6;
    doc.setTextColor(30,50,65); doc.setFontSize(15); doc.text("Informe ejecutivo · Inspección visual post-sismo",14,y); y+=6;
    doc.setFont("helvetica","normal");doc.setFontSize(9);doc.setTextColor(95,110,120);doc.text(title,14,y); y+=4;
    const date = META?.procesado_en ? new Date(META.procesado_en) : new Date();
    doc.text(`Corte: ${new Intl.DateTimeFormat("es-CO",{day:"numeric",month:"long",year:"numeric"}).format(date)}`,14,y); y+=7;
    doc.setDrawColor(11,79,138);doc.setLineWidth(.6);doc.line(14,y,196,y);y+=7;

    doc.setFont("helvetica","bold");doc.setFontSize(10);doc.setTextColor(30,50,65);doc.text("Indicadores",14,y);y+=4;
    doc.autoTable({startY:y,theme:"grid",styles:{fontSize:8,cellPadding:2},headStyles:{fillColor:[11,79,138]},head:[["Áreas","Hallazgos","Sin afectación","Alta","Riesgo inmediato","Revisión técnica","Evidencias"]],body:[[m.areas,m.findings,m.clear,m.high,m.risk,m.review,m.photos]],margin:{left:14,right:14}}); y=doc.lastAutoTable.finalY+6;

    doc.setFont("helvetica","bold");doc.setFontSize(10);doc.text("Resultado",14,y);y+=5;
    doc.setFont("helvetica","normal");doc.setFontSize(8.5);doc.setTextColor(55,70,80);
    let lines=wrapText(doc,`${text.result} ${text.predominance}`,182);doc.text(lines,14,y);y+=lines.length*4.1+4;

    if(priority.length){
      doc.setFont("helvetica","bold");doc.setFontSize(10);doc.setTextColor(30,50,65);doc.text("Hallazgos prioritarios",14,y);y+=3;
      doc.autoTable({startY:y,theme:"striped",styles:{fontSize:7.3,cellPadding:1.8},headStyles:{fillColor:[11,79,138]},head:[["Área","Hallazgo","Nivel","Riesgo","Revisión"]],body:priority.map(r=>[r.area||"",r.tipo_dano||r.elemento_ajustado||"",r.nivel||"",r.riesgo_inmediato||"",r.revision_tecnica||""]),columnStyles:{0:{cellWidth:48},1:{cellWidth:58},2:{cellWidth:22},3:{cellWidth:24},4:{cellWidth:26}},margin:{left:14,right:14}}); y=doc.lastAutoTable.finalY+6;
    }

    doc.setFont("helvetica","bold");doc.setFontSize(10);doc.setTextColor(30,50,65);doc.text("Conclusión y recomendación",14,y);y+=5;
    doc.setFont("helvetica","normal");doc.setFontSize(8.5);doc.setTextColor(55,70,80);lines=wrapText(doc,text.conclusion,182);doc.text(lines,14,y);y+=lines.length*4.1+5;
    doc.setFontSize(7.4);doc.setTextColor(90,100,110);lines=wrapText(doc,"Alcance: los resultados corresponden a una inspección visual preliminar y no constituyen diagnóstico de estabilidad ni evaluación estructural definitiva. La clasificación técnica normalizada se utiliza para presentar de forma consistente los hallazgos observados.",182);doc.text(lines,14,y);y+=lines.length*3.6+4;

    // Evidencia representativa: imágenes locales publicadas junto con el tablero.
    const photos=[]; for(const r of priority){for(const p of (r.fotos||[])){if(evidenceType(p)!=="imagen") continue;photos.push({p,r});if(photos.length>=3)break;}if(photos.length>=3)break;}
    const loaded=[]; for(const item of photos){const data=await loadImageData(item.p); if(data)loaded.push({...item,data});}
    if(loaded.length){
      doc.addPage(); y=15; doc.setFont("helvetica","bold");doc.setFontSize(12);doc.setTextColor(30,50,65);doc.text("Evidencia multimedia representativa",14,y);y+=8;
      for(const item of loaded){
        try{
          doc.setFont("helvetica","bold");doc.setFontSize(8);doc.text(`${item.r.sede} · ${item.r.area}`,14,y);y+=4;
          const type=item.data.startsWith("data:image/png")?"PNG":"JPEG"; doc.addImage(item.data,type,14,y,58,42,undefined,"FAST");
          doc.setFont("helvetica","normal");doc.setFontSize(7);doc.setTextColor(80,90,100);const d=wrapText(doc,item.r.descripcion||item.r.tipo_dano||"",118);doc.text(d,77,y+5);y+=47;
          if(y>250) {doc.addPage();y=15;}
        }catch(_){ }
      }
    }
    const safe=title.replace(/[^a-zA-Z0-9áéíóúÁÉÍÓÚñÑ_-]+/g,"_");
    doc.save(`Informe_Ejecutivo_Inspeccion_Sedes_${safe}.pdf`);
  }

  async function loadData() {
    try {
      showStatus("Cargando información procesada…","info");
      const [dr,mr]=await Promise.all([fetch(DATA_URL,{cache:"no-store"}),fetch(META_URL,{cache:"no-store"})]);
      if(!dr.ok) throw new Error(`No se pudo cargar inspecciones.json (${dr.status})`);
      if(!mr.ok) throw new Error(`No se pudo cargar metadata.json (${mr.status})`);
      DATA=await dr.json(); META=await mr.json();
      populateFilters(); setUpdateBadge(); applyFilters();
      const ev=META?.evidencias||{};
      const evText=Number(ev.pendientes||0)>0 ? ` · Evidencias locales: ${ev.locales||0}/${ev.referenciadas||0} (${ev.pendientes} pendientes) · Videos: ${ev.videos||0}` : ` · Evidencias: ${ev.locales ?? ev.referenciadas ?? 0}/${ev.referenciadas ?? ev.locales ?? 0} · Fotos: ${ev.imagenes||0} · Videos: ${ev.videos||0}`;
      showStatus(`Carga correcta: ${DATA.length} registros. Fuente: ${META.fuente || "sin identificar"}${evText}.`, Number(ev.pendientes||0)>0 ? "warning" : "success");
    } catch(e) {
      console.error(e); showStatus(`Error al cargar datos: ${e.message}. Abra el tablero mediante el BAT para evitar restricciones de file://.`,"danger");
    }
  }

  $("btnApply").addEventListener("click",applyFilters);
  $("btnClear").addEventListener("click",clearFilters);
  $("btnClearActiveFilters").addEventListener("click",clearFilters);
  $("btnReload").addEventListener("click",()=>location.reload());
  $("btnGeneratePdf").addEventListener("click",generatePdf);
  $("btnToggleStatus").addEventListener("click",()=>{const box=$("loadAlert");box.classList.toggle("d-none");$("statusHint").textContent=box.classList.contains("d-none")?"Oculto":"Visible";});
  ["fSede","fArea","fNivel","fTipoDano","fRevision"].forEach(id=>$(id).addEventListener("change",()=>{if(id==="fSede"){const sede=$("fSede").value;const areas=DATA.filter(r=>!sede||r.sede===sede).map(r=>r.area);populateSelect("fArea",areas,"Todas");}applyFilters();}));

  if ($("dSede")) $("dSede").addEventListener("change",()=>{detailSede=$("dSede").value;detailArea="";detailFindingIndex=0;detailPhotoIndex=0;populateDetailArea();renderAreaDetail();renderReportPreview();});
  if ($("dArea")) $("dArea").addEventListener("change",()=>{detailArea=$("dArea").value;detailFindingIndex=0;detailPhotoIndex=0;renderAreaDetail();});
  if ($("btnPrevArea")) $("btnPrevArea").addEventListener("click",()=>moveArea(-1));
  if ($("btnNextArea")) $("btnNextArea").addEventListener("click",()=>moveArea(1));
  document.querySelectorAll('[data-bs-target="#findings-pane"]').forEach(btn=>btn.addEventListener("shown.bs.tab",()=>{syncDetailSelectorsFromGlobal();}));

  document.addEventListener("DOMContentLoaded", loadData);
})();
