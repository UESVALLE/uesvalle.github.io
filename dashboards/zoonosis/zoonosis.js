(() => {
  "use strict";

  const ACCESS_KEY = "accesoTableroUESVALLE";
  const DATA_ROOT = "../../data/zoonosis";
  const URLS = {
    metadata: `${DATA_ROOT}/current/metadata_zoonosis.json`,
    vaccination: `${DATA_ROOT}/current/vacunacion_resumen.csv`,
    vaccinationPoints: `${DATA_ROOT}/current/vacunacion_puntos.csv`,
    aggressions: `${DATA_ROOT}/current/agresiones_resumen.csv`,
    observation: `${DATA_ROOT}/current/observacion_resumen.csv`,
    visits: `${DATA_ROOT}/current/visitas_resumen.csv`,
    municipalities: `${DATA_ROOT}/current/resumen_municipios.csv`,
    quality: `${DATA_ROOT}/current/calidad_datos_publica.csv`,
    population: `${DATA_ROOT}/reference/poblacion_canina_felina_minsalud_2025.csv`,
    demoVaccination: `${DATA_ROOT}/demo/vacunacion_municipios_demo_2026.csv`,
    demoVaccinationPoints: `${DATA_ROOT}/demo/vacunacion_puntos_demo_2026.csv`
  };
  const LAYER_URLS = {
    municipios: "https://services5.arcgis.com/l23kE3b7uPnZIuaB/arcgis/rest/services/CARTOGRAFIA_BASE/FeatureServer/2",
    veredas: "https://services5.arcgis.com/l23kE3b7uPnZIuaB/arcgis/rest/services/CARTOGRAFIA_BASE/FeatureServer/4",
    centrosPoblados: "https://services5.arcgis.com/l23kE3b7uPnZIuaB/arcgis/rest/services/CARTOGRAFIA_BASE/FeatureServer/1",
    vias: "https://services5.arcgis.com/l23kE3b7uPnZIuaB/arcgis/rest/services/Sedes_Educativas_WFL1/FeatureServer/3",
    rios: "https://services5.arcgis.com/l23kE3b7uPnZIuaB/arcgis/rest/services/Sedes_Educativas_WFL1/FeatureServer/4",
    valleContorno: "https://services5.arcgis.com/l23kE3b7uPnZIuaB/arcgis/rest/services/Sedes_Educativas_WFL1/FeatureServer/8",
    municipiosUES: "https://services5.arcgis.com/l23kE3b7uPnZIuaB/arcgis/rest/services/Municipio_UES/FeatureServer/0"
  };
  const VALLE_CENTER = [3.85, -76.45];
  const VALLE_ZOOM = 9;
  const MONTHS = ["Enero","Febrero","Marzo","Abril","Mayo","Junio","Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"];
  const PALETTE = ["#2e64d2", "#16a34a", "#f59e0b", "#7c3aed", "#0891b2", "#dc2626", "#64748b", "#db2777"];
  const MAP_COLORS = ["#eff6ff", "#bfdbfe", "#93c5fd", "#60a5fa", "#2563eb", "#1e3a8a"];

  const DATA = {
    metadata: null,
    vaccination: [],
    vaccinationPoints: [],
    aggressions: [],
    observation: [],
    visits: [],
    municipalities: [],
    quality: [],
    population: [],
    demoVaccination: [],
    demoVaccinationPoints: []
  };
  const charts = {};
  const tables = {};
  let started = false;
  let MAP = null;
  let MUNICIPAL_LAYER = null;
  let MUNICIPAL_LABELS = null;
  let REAL_POINT_LAYER = null;
  let DEMO_POINT_LAYER = null;
  let TERRITORIAL_LAYERS = {};
  let TERRITORIAL_LABELS = {};
  let BASEMAPS = {};
  let CURRENT_BASEMAP = null;
  let LAST_REAL_POINT_BOUNDS = null;
  let LAST_DEMO_POINT_BOUNDS = null;
  let VALLE_BOUNDS = null;
  let CURRENT_FILTERED_VACCINATION = [];
  let MAP_STATS = new Map();
  let MAP_MAX = 0;
  let MUNICIPAL_FEATURE_COUNT = 0;
  let MUNICIPAL_LAYER_LOADED = false;
  let MUNICIPAL_LAYER_ERROR = "";
  let selectedMunicipalityBounds = null;
  let MAP_SELECTED_MUNICIPALITY = "";
  let pendingMunicipalityFocus = null;
  let initialValleFitDone = false;

  function norm(value) {
    return String(value ?? "")
      .trim()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .replace(/\s+/g, " ")
      .toUpperCase();
  }

  function escapeHTML(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  function toNumber(value) {
    if (value === null || value === undefined || value === "") return 0;
    const number = Number(String(value).replace(",", "."));
    return Number.isFinite(number) ? number : 0;
  }

  function formatInt(value) {
    return Math.round(toNumber(value)).toLocaleString("es-CO");
  }

  function formatDecimal(value, decimals = 1) {
    return toNumber(value).toLocaleString("es-CO", { minimumFractionDigits: decimals, maximumFractionDigits: decimals });
  }

  function formatPercent(value, decimals = 1) {
    return `${formatDecimal(value, decimals)} %`;
  }

  function sum(rows, field) {
    return rows.reduce((total, row) => total + toNumber(row[field]), 0);
  }

  function groupSum(rows, keyField, valueField) {
    const grouped = new Map();
    rows.forEach(row => {
      const key = String(row[keyField] || "SIN DATO");
      grouped.set(key, (grouped.get(key) || 0) + toNumber(row[valueField]));
    });
    return grouped;
  }

  function sortedEntries(map, descending = true) {
    return [...map.entries()].sort((a, b) => descending ? b[1] - a[1] : a[1] - b[1]);
  }

  function papaCSV(url) {
    return new Promise((resolve, reject) => {
      Papa.parse(`${url}?_=${Date.now()}`, {
        download: true,
        header: true,
        skipEmptyLines: true,
        complete: result => resolve(result.data || []),
        error: reject
      });
    });
  }

  async function fetchJSON(url) {
    const response = await fetch(`${url}?_=${Date.now()}`, { cache: "no-store" });
    if (!response.ok) throw new Error(`No fue posible cargar ${url}`);
    return response.json();
  }

  function parseDataTypes() {
    DATA.vaccination = DATA.vaccination.map(row => ({
      ...row,
      anio: toNumber(row.anio), mes: toNumber(row.mes), vacunaciones: toNumber(row.vacunaciones)
    }));
    DATA.vaccinationPoints = DATA.vaccinationPoints.map(row => ({
      ...row,
      anio: toNumber(row.anio), mes: toNumber(row.mes),
      latitud: toNumber(row.latitud), longitud: toNumber(row.longitud),
      vacunaciones: toNumber(row.vacunaciones)
    })).filter(row => row.latitud !== 0 && row.longitud !== 0);
    DATA.aggressions = DATA.aggressions.map(row => ({
      ...row,
      anio: toNumber(row.anio), mes: toNumber(row.mes), eventos: toNumber(row.eventos)
    }));
    DATA.observation = DATA.observation.map(row => ({
      ...row,
      anio: toNumber(row.anio), mes: toNumber(row.mes), eventos: toNumber(row.eventos)
    }));
    DATA.visits = DATA.visits.map(row => ({
      ...row,
      anio: toNumber(row.anio), mes: toNumber(row.mes), numero_visita: toNumber(row.numero_visita), visitas: toNumber(row.visitas)
    }));
    DATA.municipalities = DATA.municipalities.map(row => {
      const numeric = { ...row };
      [
        "poblacion_perros_2025","poblacion_gatos_2025","poblacion_total_animales_2025","meta_80_total_animales",
        "vacunados_caninos_archivo","vacunados_felinos_archivo","vacunados_total_archivo","avance_canino_pct",
        "avance_felino_pct","avance_total_pct","brecha_meta_80","agresiones_2026","agresiones_total_archivo",
        "agresiones_por_1000_animales","agresiones_canino","agresiones_felino","eventos_con_3_visitas",
        "eventos_cumple_3_visitas_10_dias","cumplimiento_seguimiento_pct","cobertura_oficial_2025_pct"
      ].forEach(key => numeric[key] = toNumber(row[key]));
      return numeric;
    });
    DATA.population = DATA.population.map(row => {
      const numeric = { ...row };
      [
        "poblacion_humana_dane_2025","poblacion_perros_2025","poblacion_gatos_2025","poblacion_total_animales_2025",
        "perros_vacunados_2025","gatos_vacunados_2025","total_vacunados_2025","cobertura_perros_2025_pct",
        "cobertura_gatos_2025_pct","cobertura_total_2025_pct","meta_80_total_animales","vigencia_referencia"
      ].forEach(key => numeric[key] = toNumber(row[key]));
      return numeric;
    });
    DATA.quality = DATA.quality.map(row => ({ ...row, cantidad: toNumber(row.cantidad) }));
    DATA.demoVaccination = DATA.demoVaccination.map(row => ({
      ...row,
      anio_operativo: toNumber(row.anio_operativo),
      vacunaciones_demo: toNumber(row.vacunaciones_demo),
      caninos_demo: toNumber(row.caninos_demo),
      felinos_demo: toNumber(row.felinos_demo),
      avance_demo_pct: toNumber(row.avance_demo_pct)
    }));
    DATA.demoVaccinationPoints = DATA.demoVaccinationPoints.map(row => ({
      ...row,
      anio: toNumber(row.anio), mes: toNumber(row.mes),
      latitud: toNumber(row.latitud), longitud: toNumber(row.longitud),
      vacunaciones: toNumber(row.vacunaciones)
    })).filter(row => row.latitud !== 0 && row.longitud !== 0);
  }

  function showDashboard() {
    document.getElementById("accessGate")?.classList.add("d-none");
    document.getElementById("dashboardContent")?.classList.remove("d-none");
    setTimeout(() => {
      window.dispatchEvent(new Event("resize"));
      if (MAP) MAP.invalidateSize();
    }, 250);
    startDashboard();
  }

  function initAccess() {
    const local = ["localhost", "127.0.0.1", "0.0.0.0"].includes(location.hostname);

    // En revisión local el tablero se abre directamente. La seguridad del portal
    // sigue aplicando únicamente cuando el módulo se publica en GitHub Pages.
    if (local) {
      showDashboard();
      return;
    }

    if (localStorage.getItem(ACCESS_KEY) === "ok") showDashboard();
  }

  async function loadData() {
    setLoadStatus("Cargando archivos agregados de Zoonosis…", "info", true);
    const [metadata, vaccination, vaccinationPoints, aggressions, observation, visits, municipalities, quality, population, demoVaccination, demoVaccinationPoints] = await Promise.all([
      fetchJSON(URLS.metadata),
      papaCSV(URLS.vaccination),
      papaCSV(URLS.vaccinationPoints),
      papaCSV(URLS.aggressions),
      papaCSV(URLS.observation),
      papaCSV(URLS.visits),
      papaCSV(URLS.municipalities),
      papaCSV(URLS.quality),
      papaCSV(URLS.population),
      papaCSV(URLS.demoVaccination),
      papaCSV(URLS.demoVaccinationPoints)
    ]);
    Object.assign(DATA, { metadata, vaccination, vaccinationPoints, aggressions, observation, visits, municipalities, quality, population, demoVaccination, demoVaccinationPoints });
    parseDataTypes();
    fillFilters();
    updateSourceLinks();
    updateMetadataStatus();
    initMap();
    applyFilters();
  }

  function setLoadStatus(message, type = "info", visible = false) {
    const box = document.getElementById("loadAlert");
    if (!box) return;
    box.innerHTML = `<div class="alert alert-${type} mb-0">${message}</div>`;
    box.classList.toggle("d-none", !visible);
  }

  function updateMetadataStatus() {
    const metadata = DATA.metadata || {};
    const date = metadata.generado_en ? new Date(metadata.generado_en) : new Date();
    const badge = document.getElementById("lastUpdate");
    if (badge) {
      badge.textContent = `Actualizado: ${date.toLocaleString("es-CO")}`;
      badge.className = "badge text-bg-success last-update-badge";
    }
    const privacy = metadata.privacidad || {};
    const message = `
      <b>Datos cargados correctamente.</b><br>
      Vacunaciones válidas en fuente: <b>${formatInt(metadata.vacunaciones_validas)}</b> ·
      Agresiones procesadas: <b>${formatInt(metadata.agresiones)}</b> ·
      Municipios con referencia poblacional: <b>${formatInt(DATA.population.length)}</b>.<br>
      Vigencia operativa: <b>2026</b> · Nivel de publicación: <b>${escapeHTML(privacy.nivel_publicacion || "Agregado y anonimizado")}</b>.
      Los archivos públicos no contienen nombres, documentos, teléfonos, direcciones, funcionarios, actas ni coordenadas domiciliarias.
    `;
    setLoadStatus(message, "success", false);
  }

  function updateSourceLinks() {
    const source = (DATA.metadata?.fuentes || []).find(item => norm(item.entidad).includes("MINISTERIO"));
    const link = document.getElementById("sourceMinHealth");
    if (link && source?.url) link.href = source.url;
  }

  function fillSelect(id, values, allLabel) {
    const select = document.getElementById(id);
    if (!select) return;
    const current = select.value;
    select.innerHTML = `<option value="">${allLabel}</option>` + values.map(value => `<option value="${escapeHTML(value)}">${escapeHTML(value)}</option>`).join("");
    if (values.includes(current)) select.value = current;
  }

  function fillFilters() {
    const years = [2026];
    const yearSelect = document.getElementById("fYear");
    yearSelect.innerHTML = years.map(year => `<option value="${year}">${year}</option>`).join("");
    yearSelect.value = "2026";

    const municipalities = [...new Set(DATA.municipalities.map(row => row.municipio).filter(Boolean))].sort((a,b) => a.localeCompare(b, "es"));
    const aros = [...new Set(DATA.municipalities.map(row => row.area_operativa).filter(value => value && norm(value) !== "SIN DATO"))].sort((a,b) => a.localeCompare(b, "es"));
    const species = [...new Set([...DATA.vaccination, ...DATA.aggressions].map(row => row.especie).filter(Boolean))].sort((a,b) => a.localeCompare(b, "es"));
    fillSelect("fMunicipality", municipalities, "Todos");
    fillSelect("fAro", aros, "Todas");
    fillSelect("fSpecies", species, "Todas");
  }

  function currentFilters() {
    return {
      year: toNumber(document.getElementById("fYear")?.value),
      month: toNumber(document.getElementById("fMonth")?.value),
      municipality: document.getElementById("fMunicipality")?.value || "",
      aro: document.getElementById("fAro")?.value || "",
      species: document.getElementById("fSpecies")?.value || ""
    };
  }

  function matches(row, filters, options = {}) {
    const rowYear = toNumber(row.anio_operativo || row.anio);
    if (!options.ignoreYear && filters.year && rowYear !== filters.year) return false;
    if (!options.ignoreMonth && filters.month && toNumber(row.mes) !== filters.month) return false;
    if (filters.municipality && norm(row.municipio) !== norm(filters.municipality)) return false;
    if (filters.aro && norm(row.area_operativa) !== norm(filters.aro)) return false;
    if (!options.ignoreSpecies && filters.species && norm(row.especie) !== norm(filters.species)) return false;
    return true;
  }

  function filteredMunicipalities(filters) {
    return DATA.municipalities.filter(row => {
      if (filters.municipality && norm(row.municipio) !== norm(filters.municipality)) return false;
      if (filters.aro && norm(row.area_operativa) !== norm(filters.aro)) return false;
      return true;
    });
  }

  function denominatorField(species) {
    const normalized = norm(species);
    if (normalized === "CANINO") return "poblacion_perros_2025";
    if (normalized === "FELINO") return "poblacion_gatos_2025";
    return "poblacion_total_animales_2025";
  }

  function applyFilters() {
    const filters = currentFilters();
    const vaccination = DATA.vaccination.filter(row => matches(row, filters));
    const vaccinationPoints = DATA.vaccinationPoints.filter(row => matches(row, filters));
    const aggressions = DATA.aggressions.filter(row => matches(row, filters));
    const observation = DATA.observation.filter(row => matches(row, filters));
    const visits = DATA.visits.filter(row => matches(row, filters, { ignoreSpecies: true }));
    const municipalities = filteredMunicipalities(filters);
    const populationField = denominatorField(filters.species);
    const population = sum(municipalities, populationField);
    const target = Math.ceil(population * 0.8);
    const vaccinationCount = sum(vaccination, "vacunaciones");
    const aggressionCount = sum(aggressions, "eventos");
    const followupComplete = aggressions.filter(row => norm(row.seguimiento_3_visitas) === "CUMPLE").reduce((acc,row) => acc + row.eventos, 0);
    const coverage = population ? vaccinationCount / population * 100 : 0;
    const gap = Math.max(0, target - vaccinationCount);
    const rate = population ? aggressionCount / population * 1000 : 0;

    document.getElementById("kpiVaccinations").textContent = formatInt(vaccinationCount);
    document.getElementById("kpiAggressions").textContent = formatInt(aggressionCount);
    document.getElementById("kpiPopulation").textContent = formatInt(population);
    document.getElementById("kpiCoverage").textContent = formatPercent(coverage);
    document.getElementById("kpiGap").textContent = formatInt(gap);
    document.getElementById("kpiFollowup").textContent = formatInt(followupComplete);
    document.getElementById("kpiRate").textContent = formatDecimal(rate, 2);

    renderActiveFilters(filters);
    renderSummaryCharts(vaccination, aggressions);
    renderVaccination(vaccination);
    renderAggressions(aggressions);
    renderObservation(observation);
    renderPopulation(municipalities, filters);
    renderQuality();
    renderMap(vaccination, vaccinationPoints, aggressions, municipalities, filters);
    updateTables(vaccination, aggressions, observation, municipalities);
  }

  function renderActiveFilters(filters) {
    const wrap = document.getElementById("activeFilters");
    if (!wrap) return;
    const chips = [];
    if (filters.year) chips.push({ field:"year", label:"Año", value:filters.year, removable:false });
    if (filters.month) chips.push({ field:"month", label:"Mes", value:MONTHS[filters.month - 1], removable:true });
    if (filters.municipality) chips.push({ field:"municipality", label:"Municipio", value:filters.municipality, removable:true });
    if (filters.aro) chips.push({ field:"aro", label:"ARO", value:filters.aro, removable:true });
    if (filters.species) chips.push({ field:"species", label:"Especie", value:filters.species, removable:true });
    wrap.innerHTML = chips.length
      ? chips.map(item => `<span class="active-filter-chip"><span class="label">${escapeHTML(item.label)}:</span>${escapeHTML(item.value)}${item.removable ? `<button type="button" class="active-filter-remove" data-clear-filter="${item.field}" aria-label="Quitar ${escapeHTML(item.label)}">×</button>` : ""}</span>`).join("")
      : `<span class="text-muted small">Sin filtros adicionales</span>`;
  }

  function clearSingleFilter(field) {
    const controlMap = { month:"fMonth", municipality:"fMunicipality", aro:"fAro", species:"fSpecies" };
    const id = controlMap[field];
    if (!id) return;
    const control = document.getElementById(id);
    if (!control) return;
    control.value = "";
    if (field === "month") V6_STATE.monthFromChart = false;
    if (field === "municipality") {
      MAP_SELECTED_MUNICIPALITY = "";
      selectedMunicipalityBounds = null;
      pendingMunicipalityFocus = null;
      V6_STATE.municipalityFromChart = false;
    }
    applyFilters();
  }

  function destroyChart(id) {
    if (charts[id]) {
      charts[id].destroy();
      delete charts[id];
    }
  }

  function createChart(id, config) {
    const canvas = document.getElementById(id);
    if (!canvas) return;
    destroyChart(id);
    charts[id] = new Chart(canvas, config);
  }

  function doughnutConfig(labels, values, title = "Registros") {
    return {
      type: "doughnut",
      data: { labels, datasets: [{ data: values, backgroundColor: labels.map((_,i) => PALETTE[i % PALETTE.length]), borderWidth: 1 }] },
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: {
          legend: { position: "bottom", labels: { boxWidth: 12, font: { size: 11 } } },
          tooltip: { callbacks: { label: ctx => ` ${ctx.label}: ${formatInt(ctx.raw)} ${title}` } }
        }
      }
    };
  }

  function renderSummaryCharts(vaccination, aggressions) {
    const vaccByMonth = Array(12).fill(0);
    const aggByMonth = Array(12).fill(0);
    vaccination.forEach(row => { if (row.mes >= 1 && row.mes <= 12) vaccByMonth[row.mes - 1] += row.vacunaciones; });
    aggressions.forEach(row => { if (row.mes >= 1 && row.mes <= 12) aggByMonth[row.mes - 1] += row.eventos; });
    createChart("chartTrend", {
      type: "line",
      data: { labels: MONTHS, datasets: [
        { label: "Vacunaciones", data: vaccByMonth, borderColor: "#16a34a", backgroundColor: "rgba(22,163,74,.12)", tension: .25, fill: true },
        { label: "Agresiones", data: aggByMonth, borderColor: "#dc2626", backgroundColor: "rgba(220,38,38,.08)", tension: .25, fill: true }
      ] },
      options: { responsive:true, maintainAspectRatio:false, interaction:{mode:"index",intersect:false}, plugins:{legend:{position:"top"}}, scales:{y:{beginAtZero:true}} }
    });

    const vaccSpecies = groupSum(vaccination, "especie", "vacunaciones");
    const aggSpecies = groupSum(aggressions, "especie", "eventos");
    const species = [...new Set([...vaccSpecies.keys(), ...aggSpecies.keys()])].sort();
    createChart("chartSpecies", {
      type: "bar",
      data: { labels: species, datasets: [
        { label:"Vacunaciones", data:species.map(key => vaccSpecies.get(key) || 0), backgroundColor:"rgba(22,163,74,.55)", borderColor:"#16a34a", borderWidth:1, borderRadius:6 },
        { label:"Agresiones", data:species.map(key => aggSpecies.get(key) || 0), backgroundColor:"rgba(220,38,38,.45)", borderColor:"#dc2626", borderWidth:1, borderRadius:6 }
      ] },
      options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{position:"top"}},scales:{y:{beginAtZero:true}}}
    });

    const municipal = sortedEntries(groupSum(aggressions, "municipio", "eventos")).slice(0,15);
    createChart("chartMunicipal", {
      type:"bar",
      data:{labels:municipal.map(item=>item[0]),datasets:[{label:"Agresiones",data:municipal.map(item=>item[1]),backgroundColor:"rgba(46,100,210,.5)",borderColor:"#2e64d2",borderWidth:1,borderRadius:6}]},
      options:{responsive:true,maintainAspectRatio:false,indexAxis:"y",plugins:{legend:{display:false}},scales:{x:{beginAtZero:true}}}
    });
  }

  function renderVaccination(rows) {
    const bySpecies = groupSum(rows, "especie", "vacunaciones");
    const byCondition = groupSum(rows, "condicion", "vacunaciones");
    const byAge = sortedEntries(groupSum(rows, "grupo_edad", "vacunaciones"), false);
    const bySterilization = groupSum(rows, "esterilizado", "vacunaciones");
    document.getElementById("vaccDogs").textContent = formatInt(bySpecies.get("CANINO") || 0);
    document.getElementById("vaccCats").textContent = formatInt(bySpecies.get("FELINO") || 0);
    document.getElementById("vaccFirst").textContent = formatInt(byCondition.get("PRIMERA VEZ") || 0);
    document.getElementById("vaccRe").textContent = formatInt(byCondition.get("REVACUNADO") || 0);
    createChart("chartVaccCondition", doughnutConfig([...byCondition.keys()], [...byCondition.values()]));
    createChart("chartVaccAge", {
      type:"bar", data:{labels:byAge.map(item=>item[0]),datasets:[{data:byAge.map(item=>item[1]),backgroundColor:"rgba(46,100,210,.55)",borderColor:"#2e64d2",borderWidth:1,borderRadius:5}]},
      options:{responsive:true,maintainAspectRatio:false,indexAxis:"y",plugins:{legend:{display:false}},scales:{x:{beginAtZero:true}}}
    });
    createChart("chartSterilization", doughnutConfig([...bySterilization.keys()], [...bySterilization.values()]));
  }

  function renderAggressions(rows) {
    const bySpecies = groupSum(rows, "especie", "eventos");
    const byVaccine = groupSum(rows, "condicion_vacunacion", "eventos");
    const bySector = groupSum(rows, "sector", "eventos");
    const byProvoked = groupSum(rows, "provocado", "eventos");
    document.getElementById("aggDogs").textContent = formatInt(bySpecies.get("CANINO") || 0);
    document.getElementById("aggCats").textContent = formatInt(bySpecies.get("FELINO") || 0);
    document.getElementById("aggUnknownVacc").textContent = formatInt(byVaccine.get("DESCONOCIDO") || 0);
    document.getElementById("aggRural").textContent = formatInt(bySector.get("RURAL") || 0);
    createChart("chartSector", doughnutConfig([...bySector.keys()], [...bySector.values()]));
    createChart("chartProvoked", doughnutConfig([...byProvoked.keys()], [...byProvoked.values()]));
    createChart("chartAnimalVaccination", doughnutConfig([...byVaccine.keys()], [...byVaccine.values()]));
  }

  function renderObservation(rows) {
    const byBand = groupSum(rows, "categoria_visitas", "eventos");
    const byFollowup = groupSum(rows, "seguimiento_3_visitas", "eventos");
    const byState = sortedEntries(groupSum(rows, "estado_animal", "eventos")).slice(0,8);
    document.getElementById("obsOne").textContent = formatInt(byBand.get("1 VISITA") || 0);
    document.getElementById("obsTwo").textContent = formatInt(byBand.get("2 VISITAS") || 0);
    document.getElementById("obsThree").textContent = formatInt(byBand.get("3 O MÁS VISITAS") || 0);
    document.getElementById("obsComplete").textContent = formatInt(byFollowup.get("CUMPLE") || 0);
    createChart("chartVisitBand", doughnutConfig([...byBand.keys()], [...byBand.values()]));
    createChart("chartFollowup", doughnutConfig([...byFollowup.keys()], [...byFollowup.values()]));
    createChart("chartAnimalState", {
      type:"bar",data:{labels:byState.map(item=>item[0]),datasets:[{data:byState.map(item=>item[1]),backgroundColor:"rgba(25,135,84,.5)",borderColor:"#198754",borderWidth:1,borderRadius:5}]},
      options:{responsive:true,maintainAspectRatio:false,indexAxis:"y",plugins:{legend:{display:false}},scales:{x:{beginAtZero:true}}}
    });
  }

  function renderPopulation(rows, filters) {
    const field = denominatorField(filters.species);
    const dogs = sum(rows, "poblacion_perros_2025");
    const cats = sum(rows, "poblacion_gatos_2025");
    const total = sum(rows, field);
    document.getElementById("popDogs").textContent = formatInt(dogs);
    document.getElementById("popCats").textContent = formatInt(cats);
    document.getElementById("popTotal").textContent = formatInt(total);
    document.getElementById("popTarget").textContent = formatInt(Math.ceil(total * .8));
    const top = [...rows].sort((a,b) => b[field] - a[field]).slice(0,15);
    createChart("chartPopulation", {
      type:"bar",data:{labels:top.map(row=>row.municipio),datasets:[{data:top.map(row=>row[field]),backgroundColor:"rgba(124,58,237,.42)",borderColor:"#7c3aed",borderWidth:1,borderRadius:5}]},
      options:{responsive:true,maintainAspectRatio:false,indexAxis:"y",plugins:{legend:{display:false}},scales:{x:{beginAtZero:true}}}
    });
  }

  function renderQuality() {
    document.getElementById("qualityTypes").textContent = formatInt(DATA.quality.length);
    document.getElementById("qualityRecords").textContent = formatInt(sum(DATA.quality, "cantidad"));
    document.getElementById("qualityHigh").textContent = formatInt(DATA.quality.filter(row => norm(row.nivel) === "ALTO").length);
  }

  const DATA_TABLE_LANGUAGE = {
    decimal:",", thousands:".", search:"Buscar:", lengthMenu:"Mostrar _MENU_ registros", info:"Mostrando _START_ a _END_ de _TOTAL_ registros",
    infoEmpty:"Sin registros", zeroRecords:"No se encontraron resultados", paginate:{first:"Primero",last:"Último",next:"Siguiente",previous:"Anterior"}
  };

  function renderTable(id, rows, columns, title, order = [[columns.length - 1, "desc"]]) {
    if (tables[id]) {
      tables[id].destroy();
      delete tables[id];
    }
    const table = document.getElementById(id);
    if (!table) return;
    table.innerHTML = "";
    tables[id] = $(table).DataTable({
      data: rows,
      columns,
      pageLength: 10,
      order,
      responsive: false,
      language: DATA_TABLE_LANGUAGE,
      dom: "Bfrtip",
      buttons: [
        { extend:"excelHtml5", title, text:"Excel", className:"btn btn-success btn-sm" },
        { extend:"csvHtml5", title, text:"CSV", className:"btn btn-secondary btn-sm" },
        { extend:"print", text:"Imprimir", className:"btn btn-outline-primary btn-sm" }
      ]
    });
  }

  function aggregateVaccinationTable(rows, fields) {
    const grouped = new Map();
    rows.forEach(row => {
      const values = fields.map(field => String(row[field] ?? ""));
      const key = JSON.stringify(values);
      if (!grouped.has(key)) grouped.set(key, { values, vaccinations:0 });
      grouped.get(key).vaccinations += toNumber(row.vacunaciones);
    });
    return [...grouped.values()].sort((a,b)=>b.vaccinations-a.vaccinations);
  }

  function renderVaccinationTable(vaccination) {
    CURRENT_FILTERED_VACCINATION = vaccination;
    const mode = document.getElementById("vaccinationTableMode")?.value || "territorio";
    const configurations = {
      perfil: {
        fields:["anio","mes","municipio","area_operativa","especie","sexo","condicion","grupo_edad","esterilizado","vacuna","lote"],
        titles:["AÑO","MES","MUNICIPIO","ARO","ESPECIE","SEXO","CONDICIÓN","GRUPO EDAD","ESTERILIZADO","VACUNA","LOTE"],
        explanation:'En “Perfil completo”, una fila reúne vacunaciones con el mismo año, mes, municipio, ARO, especie, sexo, condición, grupo de edad, esterilización, vacuna y lote.'
      },
      lote: {
        fields:["anio","mes","municipio","area_operativa","vacuna","lote","especie","condicion"],
        titles:["AÑO","MES","MUNICIPIO","ARO","VACUNA","LOTE","ESPECIE","CONDICIÓN"],
        explanation:'En “Vacuna y lote”, una fila reúne todos los registros que comparten periodo, territorio, biológico, lote, especie y condición.'
      },
      territorio: {
        fields:["anio","mes","municipio","area_operativa","especie","condicion"],
        titles:["AÑO","MES","MUNICIPIO","ARO","ESPECIE","CONDICIÓN"],
        explanation:'En “Territorio, especie y condición”, una fila resume el volumen de vacunación por periodo y territorio, sin separar sexo, edad, esterilización, vacuna o lote.'
      }
    };
    const config = configurations[mode] || configurations.perfil;
    const grouped = aggregateVaccinationTable(vaccination, config.fields);
    const rows = grouped.map(item => item.values.map((value,index) => config.fields[index] === "mes" ? (MONTHS[toNumber(value)-1] || "Sin fecha") : value).concat(formatInt(item.vaccinations)));
    const columns = config.titles.map(title => ({title})).concat({title:"VACUNACIONES"});
    renderTable("tblVaccination", rows, columns, "ZOONOSIS_VACUNACION", [[columns.length-1,"desc"]]);
    const total = sum(vaccination, "vacunaciones");
    document.getElementById("vaccinationTableSummary").innerHTML = `<strong>${formatInt(grouped.length)}</strong> filas agregadas · <strong>${formatInt(total)}</strong> vacunaciones representadas`;
    document.getElementById("vaccinationTableExplanation").innerHTML = `<strong>Cómo leer:</strong> ${config.explanation} La columna “Vacunaciones” es la suma de registros incluidos en esa combinación.`;
  }

  function updateTables(vaccination, aggressions, observation, municipalities) {
    renderVaccinationTable(vaccination);

    renderTable("tblAggressions", aggressions.map(row => [
      row.anio || "Sin fecha", MONTHS[row.mes-1] || "Sin fecha", row.municipio, row.area_operativa, row.especie,
      row.sector, row.provocado, row.condicion_vacunacion, row.seguimiento_3_visitas, formatInt(row.eventos)
    ]), [
      {title:"AÑO"},{title:"MES"},{title:"MUNICIPIO"},{title:"ARO"},{title:"ESPECIE"},{title:"SECTOR"},
      {title:"PROVOCADO"},{title:"VACUNACIÓN ANIMAL"},{title:"SEGUIMIENTO"},{title:"EVENTOS"}
    ], "ZOONOSIS_AGRESIONES", [[9,"desc"]]);

    renderTable("tblObservation", observation.map(row => [
      row.anio || "Sin fecha", MONTHS[row.mes-1] || "Sin fecha", row.municipio, row.area_operativa, row.especie,
      row.categoria_visitas, row.seguimiento_3_visitas, row.estado_animal, formatInt(row.eventos)
    ]), [
      {title:"AÑO"},{title:"MES"},{title:"MUNICIPIO"},{title:"ARO"},{title:"ESPECIE"},{title:"VISITAS"},
      {title:"RESULTADO"},{title:"ESTADO ANIMAL"},{title:"EVENTOS"}
    ], "ZOONOSIS_OBSERVACION", [[8,"desc"]]);

    renderTable("tblPopulation", municipalities.map(row => [
      row.codigo_dane, row.municipio, row.area_operativa, formatInt(row.poblacion_perros_2025), formatInt(row.poblacion_gatos_2025),
      formatInt(row.poblacion_total_animales_2025), formatInt(row.meta_80_total_animales), formatPercent(row.cobertura_oficial_2025_pct)
    ]), [
      {title:"CÓDIGO DANE"},{title:"MUNICIPIO"},{title:"ARO"},{title:"PERROS 2025"},{title:"GATOS 2025"},
      {title:"TOTAL ANIMALES"},{title:"META 80 %"},{title:"COBERTURA OFICIAL 2025"}
    ], "ZOONOSIS_POBLACION_REFERENCIA", [[5,"desc"]]);

    renderTable("tblQuality", DATA.quality.map(row => [row.fuente_datos, row.tipo_inconsistencia, formatInt(row.cantidad), row.nivel]), [
      {title:"FUENTE"},{title:"TIPO DE INCONSISTENCIA"},{title:"CANTIDAD"},{title:"NIVEL"}
    ], "ZOONOSIS_CALIDAD_DATOS", [[2,"desc"]]);
  }

  function getFeatureMunicipality(properties) {
    const p = properties || {};
    return p.MPIO_CNMBRE || p.MPIO_CNMBR || p.MUNICIPIO || p.NOM_MUN || p.NOMBRE || p.MPIO || p.NAME || "";
  }

  function arcgisGeoJSONQuery(layerUrl) {
    const params = new URLSearchParams({
      where: "1=1",
      outFields: "*",
      returnGeometry: "true",
      outSR: "4326",
      f: "geojson"
    });
    return `${layerUrl}/query?${params.toString()}`;
  }

  async function fetchLayerGeoJSON(layerUrl) {
    const response = await fetch(arcgisGeoJSONQuery(layerUrl), { cache:"no-store" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    if (!data || data.type !== "FeatureCollection" || !Array.isArray(data.features)) {
      throw new Error("La respuesta no contiene una colección GeoJSON válida.");
    }
    return data;
  }

  function createMapPanes() {
    const panes = {
      territorialPane: 410,
      municipalPane: 430,
      contourPane: 450,
      labelPane: 610,
      demoPointsPane: 640,
      realPointsPane: 650
    };
    const passThroughPanes = new Set(["territorialPane", "contourPane", "labelPane"]);
    Object.entries(panes).forEach(([name,z]) => {
      const pane = MAP.getPane(name) || MAP.createPane(name);
      pane.style.zIndex = String(z);
      // Las capas territoriales son solo referencia visual y no deben bloquear
      // el clic sobre los polígonos municipales ubicados debajo.
      pane.style.pointerEvents = passThroughPanes.has(name) ? "none" : "auto";
    });
  }

  function initMap() {
    if (MAP || !document.getElementById("map")) return;
    MAP = L.map("map", { zoomControl:true, preferCanvas:true }).setView(VALLE_CENTER, VALLE_ZOOM);
    createMapPanes();

    BASEMAPS = {
      cartoLight: L.tileLayer("https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png", { maxZoom:20, attribution:"© OpenStreetMap © CARTO" }),
      esriTopo: L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}", { maxZoom:19, attribution:"Esri" }),
      esriImagery: L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}", { maxZoom:19, attribution:"Esri" }),
      osm: L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", { maxZoom:19, attribution:"© OpenStreetMap" })
    };
    CURRENT_BASEMAP = BASEMAPS.cartoLight;
    CURRENT_BASEMAP.addTo(MAP);

    MUNICIPAL_LABELS = L.layerGroup([], { pane:"labelPane" }).addTo(MAP);
    REAL_POINT_LAYER = L.layerGroup([], { pane:"realPointsPane" }).addTo(MAP);
    DEMO_POINT_LAYER = L.layerGroup([], { pane:"demoPointsPane" });
    initTerritorialLayers();
    loadMunicipalPolygons();

    MAP.on("zoomend", updateScaleSensitiveLayers);
  }

  async function loadMunicipalPolygons() {
    MUNICIPAL_LAYER_LOADED = false;
    MUNICIPAL_LAYER_ERROR = "";
    updateMapCounters({ real:0, demo:0 });
    try {
      const geojson = await fetchLayerGeoJSON(LAYER_URLS.municipios);
      MUNICIPAL_LAYER = L.geoJSON(geojson, {
        pane:"municipalPane",
        style: municipalityStyle,
        onEachFeature: (feature, layer) => bindMunicipalityFeature(layer, feature)
      }).addTo(MAP);
      MUNICIPAL_FEATURE_COUNT = MUNICIPAL_LAYER.getLayers().length;
      MUNICIPAL_LAYER_LOADED = MUNICIPAL_FEATURE_COUNT > 0;
      if (!MUNICIPAL_LAYER_LOADED) throw new Error("La consulta municipal no devolvió geometrías.");
      VALLE_BOUNDS = MUNICIPAL_LAYER.getBounds();
      refreshMunicipalityFeatures();
      renderMunicipalityLabels();
      syncMapLayers();
      if (!initialValleFitDone && VALLE_BOUNDS?.isValid()) {
        initialValleFitDone = true;
        MAP.fitBounds(VALLE_BOUNDS, { padding:[12,12] });
      }
      applyFilters();
    } catch (error) {
      console.warn("Falló la consulta GeoJSON municipal; se intenta la carga Esri utilizada por IRCAS.", error);
      if (L.esri?.featureLayer) {
        MUNICIPAL_LAYER = L.esri.featureLayer({
          url:LAYER_URLS.municipios,
          pane:"municipalPane",
          simplifyFactor:.25,
          precision:5,
          style:feature => municipalityStyle(feature)
        }).addTo(MAP);
        MUNICIPAL_LAYER.on("createfeature", event => bindMunicipalityFeature(event.layer, event.feature));
        MUNICIPAL_LAYER.on("load", () => {
          MUNICIPAL_FEATURE_COUNT = 0;
          MUNICIPAL_LAYER.eachFeature(() => { MUNICIPAL_FEATURE_COUNT += 1; });
          MUNICIPAL_LAYER_LOADED = MUNICIPAL_FEATURE_COUNT > 0;
          MUNICIPAL_LAYER_ERROR = MUNICIPAL_LAYER_LOADED ? "" : "La capa Esri no devolvió geometrías.";
          try { VALLE_BOUNDS = MUNICIPAL_LAYER.getBounds?.() || VALLE_BOUNDS; } catch (_) {}
          refreshMunicipalityFeatures();
          renderMunicipalityLabels();
          syncMapLayers();
          if (!initialValleFitDone && VALLE_BOUNDS?.isValid()) {
            initialValleFitDone = true;
            MAP.fitBounds(VALLE_BOUNDS, { padding:[12,12] });
          }
          applyFilters();
        });
        MUNICIPAL_LAYER.on("requesterror", requestError => {
          MUNICIPAL_LAYER_ERROR = requestError?.message || error?.message || "No fue posible consultar la capa municipal.";
          MUNICIPAL_LAYER_LOADED = false;
          updateMapCounters({ real:0, demo:0 });
          document.getElementById("mapSummary").innerHTML = `<span class="text-danger"><b>No fue posible dibujar los polígonos municipales:</b> ${escapeHTML(MUNICIPAL_LAYER_ERROR)}.</span> Los puntos de vacunación continúan disponibles.`;
        });
      } else {
        MUNICIPAL_LAYER_ERROR = error?.message || String(error);
        MUNICIPAL_LAYER_LOADED = false;
        updateMapCounters({ real:0, demo:0 });
        document.getElementById("mapSummary").innerHTML = `<span class="text-danger"><b>No fue posible dibujar los polígonos municipales:</b> ${escapeHTML(MUNICIPAL_LAYER_ERROR)}.</span> Los puntos de vacunación continúan disponibles.`;
      }
    }
  }

  function eachMunicipalFeature(callback) {
    if (!MUNICIPAL_LAYER || typeof callback !== "function") return;
    if (typeof MUNICIPAL_LAYER.eachFeature === "function") MUNICIPAL_LAYER.eachFeature(callback);
    else if (typeof MUNICIPAL_LAYER.eachLayer === "function") MUNICIPAL_LAYER.eachLayer(callback);
  }

  function initTerritorialLayers() {
    if (!L.esri?.featureLayer) return;
    TERRITORIAL_LABELS = {
      veredas: L.layerGroup([], { pane:"labelPane" }),
      rios: L.layerGroup([], { pane:"labelPane" })
    };

    TERRITORIAL_LAYERS = {
      veredas: L.esri.featureLayer({
        url:LAYER_URLS.veredas, pane:"territorialPane", interactive:false,
        style:{ color:"#c9ced6", weight:.75, fillColor:"#f5f6f7", fillOpacity:.015, interactive:false }
      }),
      centrosPoblados: L.esri.featureLayer({
        url:LAYER_URLS.centrosPoblados, pane:"territorialPane", interactive:false,
        style:{ color:"#b45309",weight:1,fillColor:"#f59e0b",fillOpacity:.22,interactive:false },
        pointToLayer:(geojson,latlng)=>L.circleMarker(latlng,{ pane:"territorialPane", interactive:false, radius:3.5,color:"#b45309",fillColor:"#f59e0b",fillOpacity:.85,weight:1 })
      }),
      vias: L.esri.featureLayer({ url:LAYER_URLS.vias, pane:"territorialPane", interactive:false, style:{ color:"#475569",weight:1.6,interactive:false } }),
      rios: L.esri.featureLayer({ url:LAYER_URLS.rios, pane:"territorialPane", interactive:false, style:{ color:"#0ea5e9",weight:1.5,interactive:false } }),
      valleContorno: L.esri.featureLayer({ url:LAYER_URLS.valleContorno, pane:"contourPane", interactive:false, style:{ color:"#111827",weight:2.6,fillOpacity:0,interactive:false } }),
      municipiosUES: L.esri.featureLayer({ url:LAYER_URLS.municipiosUES, pane:"contourPane", interactive:false, style:{ color:"#0f766e",weight:2,fillColor:"#2dd4bf",fillOpacity:.035,interactive:false } })
    };

    TERRITORIAL_LAYERS.veredas.on("load", () => renderEsriLabels(TERRITORIAL_LAYERS.veredas, TERRITORIAL_LABELS.veredas, p => p.NOMBRE_VER || p.NOMBRE || "", "vereda-label"));
    TERRITORIAL_LAYERS.rios.on("load", () => renderEsriLabels(TERRITORIAL_LAYERS.rios, TERRITORIAL_LABELS.rios, p => p.NOM1_DRENAJE || p.NOMBRE || p.RIO || "", "rio-label"));
    TERRITORIAL_LAYERS.valleContorno.on("load", () => {
      try {
        const b = TERRITORIAL_LAYERS.valleContorno.getBounds?.();
        if (b?.isValid()) VALLE_BOUNDS = b;
      } catch (_) {}
    });
    syncMapLayers();
  }

  function renderEsriLabels(sourceLayer, targetGroup, nameFn, className) {
    if (!sourceLayer || !targetGroup) return;
    targetGroup.clearLayers();
    sourceLayer.eachFeature(layer => {
      const name = nameFn(layer.feature?.properties || {});
      if (!name) return;
      const latlng = layer.getLatLng?.() || layer.getBounds?.().getCenter?.();
      if (!latlng) return;
      L.marker(latlng, { interactive:false, pane:"labelPane", icon:L.divIcon({ className, html:`<div>${escapeHTML(name)}</div>` }) }).addTo(targetGroup);
    });
    updateScaleSensitiveLayers();
  }

  function updateScaleSensitiveLayers() {
    if (!MAP) return;
    const zoom = MAP.getZoom();
    const veredaLabelsChecked = document.getElementById("showVeredasValle")?.checked === true;
    const rioLabelsChecked = document.getElementById("showRiosLabels")?.checked === true;
    toggleLayer(TERRITORIAL_LABELS.veredas, veredaLabelsChecked && zoom >= 12);
    toggleLayer(TERRITORIAL_LABELS.rios, rioLabelsChecked && zoom >= 11);
  }

  function getMapMetric() {
    return document.querySelector('input[name="mapMetric"]:checked')?.value || "agresiones";
  }

  function getMapDataMode() {
    return document.querySelector('input[name="mapDataMode"]:checked')?.value || "real";
  }

  function demoVaccinationByMunicipality() {
    const result = new Map();
    DATA.demoVaccination.forEach(row => result.set(norm(row.municipio), row));
    return result;
  }

  function updateMapCounters(pointStats = { real:0, demo:0 }) {
    const polygons = document.getElementById("mapMunicipalityCount");
    const dataCount = document.getElementById("mapMunicipalityDataCount");
    const realPoints = document.getElementById("mapRealPointCount");
    const demoPoints = document.getElementById("mapDemoPointCount");
    if (polygons) polygons.textContent = MUNICIPAL_LAYER_LOADED ? formatInt(MUNICIPAL_FEATURE_COUNT) : "0";
    if (dataCount) dataCount.textContent = formatInt([...MAP_STATS.values()].filter(s => metricValue(s) > 0).length);
    if (realPoints) realPoints.textContent = formatInt(pointStats.real || 0);
    if (demoPoints) demoPoints.textContent = formatInt(pointStats.demo || 0);
  }

  function setBasemap(name) {
    const next = BASEMAPS[name];
    if (!MAP || !next || next === CURRENT_BASEMAP) return;
    if (CURRENT_BASEMAP && MAP.hasLayer(CURRENT_BASEMAP)) MAP.removeLayer(CURRENT_BASEMAP);
    CURRENT_BASEMAP = next;
    CURRENT_BASEMAP.addTo(MAP);
    CURRENT_BASEMAP.bringToBack?.();
  }

  function toggleLayer(layer, visible) {
    if (!MAP || !layer) return;
    if (visible && !MAP.hasLayer(layer)) layer.addTo(MAP);
    if (!visible && MAP.hasLayer(layer)) MAP.removeLayer(layer);
  }

  function syncMapLayers() {
    if (!MAP) return;
    toggleLayer(MUNICIPAL_LAYER, document.getElementById("showMunicipalPolygons")?.checked !== false);
    toggleLayer(MUNICIPAL_LABELS, document.getElementById("showMunicipalityLabels")?.checked !== false);
    toggleLayer(TERRITORIAL_LAYERS.veredas, document.getElementById("showVeredasValle")?.checked === true);
    toggleLayer(TERRITORIAL_LAYERS.centrosPoblados, document.getElementById("showCentrosPoblados")?.checked === true);
    toggleLayer(TERRITORIAL_LAYERS.vias, document.getElementById("showViasPrincipales")?.checked === true);
    toggleLayer(TERRITORIAL_LAYERS.rios, document.getElementById("showRios")?.checked === true);
    toggleLayer(TERRITORIAL_LAYERS.valleContorno, document.getElementById("showValleContorno")?.checked === true);
    toggleLayer(TERRITORIAL_LAYERS.municipiosUES, document.getElementById("showMunicipiosUES")?.checked === true);
    updateScaleSensitiveLayers();
  }

  function metricValue(stats) {
    const metric = getMapMetric();
    if (!stats) return 0;
    if (metric === "tasa") return stats.rate;
    if (metric === "vacunacion") return stats.vaccinations;
    if (metric === "avance") return stats.coverage;
    if (metric === "poblacion") return stats.population;
    return stats.aggressions;
  }

  function metricLabel() {
    const metric = getMapMetric();
    return ({agresiones:"Agresiones reportadas",tasa:"Agresiones por 1.000 animales",vacunacion:"Vacunaciones registradas",avance:"Avance frente a población estimada",poblacion:"Población animal estimada"})[metric] || "Agresiones reportadas";
  }

  const METRIC_SCALES = {
    agresiones: { thresholds:[0,25,50,100,150], colors:["#fff7ed","#fed7aa","#fdba74","#f97316","#dc2626"], decimals:0, unit:"" },
    tasa: { thresholds:[0,5,10,15,20], colors:["#f0fdf4","#bbf7d0","#86efac","#22c55e","#15803d"], decimals:1, unit:"" },
    vacunacion: { thresholds:[0,250,500,750,1000], colors:["#eff6ff","#bfdbfe","#93c5fd","#3b82f6","#1d4ed8"], decimals:0, unit:"" },
    avance: { thresholds:[0,20,40,60,80], colors:["#fef2f2","#fecaca","#fde68a","#bbf7d0","#16a34a"], decimals:1, unit:" %" },
    poblacion: { thresholds:[0,5000,10000,20000,30000], colors:["#f5f3ff","#ddd6fe","#c4b5fd","#8b5cf6","#6d28d9"], decimals:0, unit:"" }
  };

  function scaleForMetric() { return METRIC_SCALES[getMapMetric()] || METRIC_SCALES.agresiones; }

  function colorForValue(value) {
    if (!Number.isFinite(value) || value <= 0) return "#f1f5f9";
    const scale = scaleForMetric();
    const t = scale.thresholds;
    if (value <= t[1]) return scale.colors[0];
    if (value <= t[2]) return scale.colors[1];
    if (value <= t[3]) return scale.colors[2];
    if (value <= t[4]) return scale.colors[3];
    return scale.colors[4];
  }

  function municipalityStyle(feature) {
    const name = getFeatureMunicipality(feature?.properties);
    const stats = MAP_STATS.get(norm(name));
    const selected = MAP_SELECTED_MUNICIPALITY || document.getElementById("fMunicipality")?.value || "";
    const active = selected && norm(selected) === norm(name);
    const value = metricValue(stats);
    return {
      pane:"municipalPane",
      color: active ? "#0f172a" : "#334155",
      weight: active ? 4.2 : 1.35,
      fillColor: stats ? colorForValue(value) : "#f8fafc",
      fillOpacity: active ? .88 : (stats ? .76 : .12)
    };
  }

  function popupHTML(name) {
    const stats = MAP_STATS.get(norm(name));
    if (!stats) return `<div class="popup-zoonosis"><h4>${escapeHTML(name)}</h4><p>Sin información en el universo filtrado.</p></div>`;
    const demoBadge = stats.vaccinationType === "SIMULADO" ? '<div class="popup-demo-note">La vacunación municipal mostrada es simulada para validar el tablero.</div>' : '';
    return `<div class="popup-zoonosis">
      <h4>${escapeHTML(stats.name)}</h4>
      <div class="popup-grid">
        <div class="popup-metric"><small>Vacunaciones</small><b>${formatInt(stats.vaccinations)}</b></div>
        <div class="popup-metric"><small>Agresiones</small><b>${formatInt(stats.aggressions)}</b></div>
        <div class="popup-metric"><small>Población estimada</small><b>${formatInt(stats.population)}</b></div>
        <div class="popup-metric"><small>Avance</small><b>${formatPercent(stats.coverage)}</b></div>
        <div class="popup-metric"><small>Tasa por 1.000</small><b>${formatDecimal(stats.rate,2)}</b></div>
        <div class="popup-metric"><small>Seguimientos completos</small><b>${formatInt(stats.complete)}</b></div>
      </div>${demoBadge}
    </div>`;
  }

  function findMunicipalityLayer(name) {
    let match = null;
    eachMunicipalFeature(layer => {
      if (match) return;
      const layerName = getFeatureMunicipality(layer.feature?.properties);
      if (norm(layerName) === norm(name)) match = layer;
    });
    return match;
  }

  function focusMunicipalityOnMap(name, options = {}) {
    if (!MAP || !name) return;
    const layer = options.layer || findMunicipalityLayer(name);
    const bounds = options.bounds || layer?.getBounds?.() || selectedMunicipalityBounds;
    if (!bounds?.isValid?.()) return;

    selectedMunicipalityBounds = bounds;
    const openSelectedPopup = () => {
      const currentLayer = layer || findMunicipalityLayer(name);
      if (!currentLayer) return;
      currentLayer.setPopupContent?.(popupHTML(name));
      currentLayer.bringToFront?.();
      if (options.openPopup !== false) currentLayer.openPopup?.();
    };

    if (typeof MAP.flyToBounds === "function") {
      MAP.once("moveend", openSelectedPopup);
      MAP.flyToBounds(bounds, { padding:[30,30], maxZoom:11, duration:.7 });
      window.setTimeout(openSelectedPopup, 900);
    } else {
      MAP.fitBounds(bounds, { padding:[30,30], maxZoom:11 });
      openSelectedPopup();
    }
  }

  function selectMunicipality(name, options = {}) {
    if (!name) return;
    const source = options.source || "map";
    const select = document.getElementById("fMunicipality");
    const option = select ? [...select.options].find(item => norm(item.value) === norm(name)) : null;
    const layer = options.layer || findMunicipalityLayer(name);
    const bounds = options.bounds || layer?.getBounds?.() || null;

    MAP_SELECTED_MUNICIPALITY = name;
    selectedMunicipalityBounds = bounds;
    pendingMunicipalityFocus = { name, layer, bounds, openPopup: options.openPopup !== false };

    if (option && select) {
      select.value = option.value;
      V6_STATE.municipalityFromChart = source === "chart";
      applyFilters();
    } else {
      V6_STATE.municipalityFromChart = false;
      refreshMunicipalityFeatures();
    }

    window.requestAnimationFrame(() => {
      const pending = pendingMunicipalityFocus;
      pendingMunicipalityFocus = null;
      focusMunicipalityOnMap(name, pending || { layer, bounds, openPopup: options.openPopup !== false });
    });
  }

  function clearMunicipalitySelection(options = {}) {
    MAP_SELECTED_MUNICIPALITY = "";
    selectedMunicipalityBounds = null;
    pendingMunicipalityFocus = null;
    V6_STATE.municipalityFromChart = false;
    const select = document.getElementById("fMunicipality");
    if (select) select.value = "";
    if (options.apply !== false) applyFilters();
    else refreshMunicipalityFeatures();
    if (options.fitValle) {
      if (VALLE_BOUNDS?.isValid()) MAP?.fitBounds(VALLE_BOUNDS, { padding:[12,12] });
      else MAP?.setView(VALLE_CENTER, VALLE_ZOOM);
    }
  }

  function bindMunicipalityFeature(layer, feature) {
    const name = getFeatureMunicipality(feature?.properties);
    layer.bindPopup(popupHTML(name));
    layer.on("click", event => {
      if (event?.originalEvent) L.DomEvent.stopPropagation(event.originalEvent);
      layer.setPopupContent(popupHTML(name));
      selectMunicipality(name, {
        source:"map",
        layer,
        bounds:layer.getBounds?.() || null,
        openPopup:true
      });
    });
  }

  function refreshMunicipalityFeatures() {
    if (!MUNICIPAL_LAYER) return;
    const selected = MAP_SELECTED_MUNICIPALITY || document.getElementById("fMunicipality")?.value || "";
    selectedMunicipalityBounds = null;
    eachMunicipalFeature(layer => {
      const name = getFeatureMunicipality(layer.feature?.properties);
      layer.setStyle?.(municipalityStyle(layer.feature));
      layer.setPopupContent?.(popupHTML(name));
      if (selected && norm(selected) === norm(name) && layer.getBounds) {
        selectedMunicipalityBounds = layer.getBounds();
        layer.bringToFront?.();
      }
    });
  }

  function renderMunicipalityLabels() {
    if (!MUNICIPAL_LABELS || !MUNICIPAL_LAYER) return;
    MUNICIPAL_LABELS.clearLayers();
    eachMunicipalFeature(layer => {
      const bounds = layer.getBounds?.();
      if (!bounds?.isValid()) return;
      const name = getFeatureMunicipality(layer.feature?.properties);
      if (!name) return;
      L.marker(bounds.getCenter(), {
        interactive:false, pane:"labelPane",
        icon:L.divIcon({className:"municipio-label",html:`<div>${escapeHTML(name)}</div>`})
      }).addTo(MUNICIPAL_LABELS);
    });
  }

  function aggregateVaccinationPoints(rows) {
    const grouped = new Map();
    rows.forEach(row => {
      const lat = toNumber(row.latitud);
      const lon = toNumber(row.longitud);
      if (!lat || !lon) return;
      const key = `${lat.toFixed(6)}|${lon.toFixed(6)}`;
      if (!grouped.has(key)) {
        grouped.set(key, {
          latitud:lat,longitud:lon,municipio:row.municipio,total:0,caninos:0,felinos:0,otros:0,primera:0,revacunados:0,
          anios:new Set(),meses:new Set(),fechas:new Set(),lotes:new Map()
        });
      }
      const item = grouped.get(key);
      const count = toNumber(row.vacunaciones);
      item.total += count;
      const species = norm(row.especie);
      if (species === "CANINO") item.caninos += count;
      else if (species === "FELINO") item.felinos += count;
      else item.otros += count;
      const condition = norm(row.condicion);
      if (condition === "PRIMERA VEZ") item.primera += count;
      if (condition === "REVACUNADO") item.revacunados += count;
      if (row.anio) item.anios.add(row.anio);
      if (row.mes) item.meses.add(row.mes);
      if (row.fecha) item.fechas.add(row.fecha);
      const vaccine = row.vacuna || "SIN DATO";
      const lot = row.lote || "SIN DATO";
      const lotKey = `${vaccine}|||${lot}`;
      item.lotes.set(lotKey, (item.lotes.get(lotKey) || 0) + count);
    });
    return [...grouped.values()];
  }

  function formatDateISO(value) {
    const parts = String(value || "").split("-");
    return parts.length === 3 ? `${parts[2]}/${parts[1]}/${parts[0]}` : String(value || "");
  }

  function vaccinationPointPopup(point, simulated = false) {
    const years = [...point.anios].sort().join(", ") || "Sin dato";
    const months = [...point.meses].sort((a,b)=>a-b).map(month => MONTHS[month-1]).join(", ") || "Sin dato";
    const dates = [...point.fechas].sort();
    const period = dates.length === 0 ? "Sin dato" : dates.length === 1 ? formatDateISO(dates[0]) : `${formatDateISO(dates[0])} a ${formatDateISO(dates[dates.length-1])}`;
    const lotRows = [...point.lotes.entries()].sort((a,b)=>b[1]-a[1]).map(([key,count]) => {
      const [vaccine,lot] = key.split("|||");
      return `<div class="popup-lot-row"><span>${escapeHTML(vaccine)} · lote ${escapeHTML(lot)}</span><b>${formatInt(count)} dosis</b></div>`;
    }).join("");
    const title = simulated ? "Punto simulado de vacunación" : "Punto real de vacunación";
    const note = simulated
      ? '<div class="popup-demo-note">Información creada exclusivamente para probar la visualización. No corresponde a resultados oficiales.</div>'
      : '<div class="popup-point-note">No se muestran datos del propietario, documentos, teléfonos, direcciones, auxiliares ni nombres de mascotas.</div>';
    return `<div class="popup-zoonosis"><h4>${title}</h4><div class="popup-grid">
      <div class="popup-metric"><small>Municipio</small><b>${escapeHTML(point.municipio || "SIN DATO")}</b></div>
      <div class="popup-metric"><small>Vacunaciones</small><b>${formatInt(point.total)}</b></div>
      <div class="popup-metric"><small>Caninos</small><b>${formatInt(point.caninos)}</b></div>
      <div class="popup-metric"><small>Felinos</small><b>${formatInt(point.felinos)}</b></div>
      <div class="popup-metric"><small>Primera vez</small><b>${formatInt(point.primera)}</b></div>
      <div class="popup-metric"><small>Revacunados</small><b>${formatInt(point.revacunados)}</b></div>
      <div class="popup-metric"><small>Periodo</small><b>${escapeHTML(period)}</b></div>
      <div class="popup-metric"><small>Año / mes</small><b>${escapeHTML(years)} · ${escapeHTML(months)}</b></div>
    </div><div class="popup-lot-list"><div class="popup-lot-title">Vacuna y lote</div>${lotRows || '<div class="popup-lot-row"><span>Sin información</span><b>–</b></div>'}</div>${note}</div>`;
  }

  function renderPointLayer(rows, layer, simulated = false) {
    if (!layer) return { locations:0, vaccinations:0, bounds:null };
    layer.clearLayers();
    const points = aggregateVaccinationPoints(rows);
    const bounds=[];
    let vaccinations=0;
    points.forEach(point => {
      vaccinations += point.total;
      bounds.push([point.latitud,point.longitud]);
      const multi=point.total>1;
      const icon=L.divIcon({
        className:"vaccination-point-icon",
        html:`<span class="vaccination-point-dot${simulated ? " demo" : ""}${multi ? " multi" : ""}">${multi ? formatInt(point.total) : ""}</span>`,
        iconSize:multi ? [26,26] : [18,18], iconAnchor:multi ? [13,13] : [9,9]
      });
      L.marker([point.latitud,point.longitud],{ pane:simulated ? "demoPointsPane" : "realPointsPane",icon,keyboard:true,title:`${point.total} vacunación(es)${simulated ? " simuladas" : ""}` })
        .bindPopup(vaccinationPointPopup(point,simulated),{maxWidth:390}).addTo(layer);
    });
    return { locations:points.length,vaccinations,bounds:bounds.length ? L.latLngBounds(bounds) : null };
  }

  function filterDemoPoints(filters) {
    return DATA.demoVaccinationPoints.filter(row => matches(row, filters));
  }

  function renderMap(vaccination, vaccinationPoints, aggressions, municipalities, filters) {
    const populationField = denominatorField(filters.species);
    const vaccByMuni = groupSum(vaccination,"municipio","vacunaciones");
    const aggByMuni = groupSum(aggressions,"municipio","eventos");
    const demoByMuni = demoVaccinationByMunicipality();
    const demoMode = getMapDataMode() === "demo";
    document.getElementById("mapDemoBanner")?.classList.toggle("d-none",!demoMode);
    const demoPointsCheckbox=document.getElementById("showDemoVaccinationPoints");
    if (demoPointsCheckbox) {
      demoPointsCheckbox.disabled=!demoMode;
      if (!demoMode) demoPointsCheckbox.checked=false;
      if (demoMode && !demoPointsCheckbox.dataset.userChanged) demoPointsCheckbox.checked=true;
    }

    const completeByMuni=new Map();
    aggressions.forEach(row=>{ if(norm(row.seguimiento_3_visitas)!=="CUMPLE")return; completeByMuni.set(norm(row.municipio),(completeByMuni.get(norm(row.municipio))||0)+row.eventos); });
    MAP_STATS=new Map();
    municipalities.forEach(row=>{
      const key=norm(row.municipio);
      const population=toNumber(row[populationField]);
      const realVaccinations=vaccByMuni.get(row.municipio)||0;
      const demoRow=demoByMuni.get(key);
      let vaccinations=realVaccinations;
      let vaccinationType="REAL";
      if(demoMode && demoRow){vaccinations=toNumber(demoRow.vacunaciones_demo);vaccinationType=norm(demoRow.tipo_dato)||"SIMULADO";}
      const aggressionCount=aggByMuni.get(row.municipio)||0;
      MAP_STATS.set(key,{name:row.municipio,aro:row.area_operativa,population,vaccinations,realVaccinations,vaccinationType,aggressions:aggressionCount,coverage:population?vaccinations/population*100:0,rate:population?aggressionCount/population*1000:0,complete:completeByMuni.get(key)||0});
    });
    MAP_MAX=Math.max(0,...[...MAP_STATS.values()].map(metricValue));
    syncMapLayers();
    refreshMunicipalityFeatures();
    renderMunicipalityLabels();

    const showReal=document.getElementById("showRealVaccinationPoints")?.checked!==false;
    const showDemo=demoMode && document.getElementById("showDemoVaccinationPoints")?.checked===true;
    toggleLayer(REAL_POINT_LAYER,showReal);
    toggleLayer(DEMO_POINT_LAYER,showDemo);
    const realStats=showReal ? renderPointLayer(vaccinationPoints,REAL_POINT_LAYER,false) : (REAL_POINT_LAYER.clearLayers(),{locations:0,vaccinations:0,bounds:null});
    const demoRows=showDemo ? filterDemoPoints(filters) : [];
    const demoStats=showDemo ? renderPointLayer(demoRows,DEMO_POINT_LAYER,true) : (DEMO_POINT_LAYER.clearLayers(),{locations:0,vaccinations:0,bounds:null});
    LAST_REAL_POINT_BOUNDS=realStats.bounds;
    LAST_DEMO_POINT_BOUNDS=demoStats.bounds;
    updateMapCounters({real:realStats.locations,demo:demoStats.locations});
    renderMapLegend();

    const metric=getMapMetric();
    const values=[...MAP_STATS.values()];
    const totalPopulation=values.reduce((a,i)=>a+i.population,0);
    const totalVaccinations=values.reduce((a,i)=>a+i.vaccinations,0);
    const totalAggressions=values.reduce((a,i)=>a+i.aggressions,0);
    let summaryValue=values.reduce((a,i)=>a+metricValue(i),0);
    if(metric==="tasa")summaryValue=totalPopulation?totalAggressions/totalPopulation*1000:0;
    if(metric==="avance")summaryValue=totalPopulation?totalVaccinations/totalPopulation*100:0;
    const decimals=["tasa","avance"].includes(metric)?1:0;
    const municipalitiesAggression=values.filter(i=>i.aggressions>0).length;
    const municipalitiesVaccination=values.filter(i=>i.vaccinations>0).length;
    const polygonStatus=MUNICIPAL_LAYER_LOADED?`Polígonos dibujados: <strong>${formatInt(MUNICIPAL_FEATURE_COUNT)}</strong>.`:`<span class="text-danger">Polígonos no dibujados: ${escapeHTML(MUNICIPAL_LAYER_ERROR||"verifique conexión")}</span>`;
    const demoText=demoMode?` Puntos simulados visibles: <strong>${formatInt(demoStats.locations)}</strong>.`:"";
    document.getElementById("mapSummary").innerHTML=`<strong>Color municipal · ${escapeHTML(metricLabel())}:</strong> ${formatDecimal(summaryValue,decimals)} · Municipios con agresiones: <strong>${formatInt(municipalitiesAggression)}</strong> · Municipios con vacunación: <strong>${formatInt(municipalitiesVaccination)}</strong>. ${polygonStatus} Puntos reales: <strong>${formatInt(realStats.locations)}</strong>.${demoText}`;
  }

  function renderMapLegend() {
    const legend=document.getElementById("mapLegend");
    if(!legend)return;
    const scale=scaleForMetric();const t=scale.thresholds;
    const labels=[`1–${formatDecimal(t[1],scale.decimals)}${scale.unit}`,`${formatDecimal(t[1]+(scale.decimals?.1:1),scale.decimals)}–${formatDecimal(t[2],scale.decimals)}${scale.unit}`,`${formatDecimal(t[2]+(scale.decimals?.1:1),scale.decimals)}–${formatDecimal(t[3],scale.decimals)}${scale.unit}`,`${formatDecimal(t[3]+(scale.decimals?.1:1),scale.decimals)}–${formatDecimal(t[4],scale.decimals)}${scale.unit}`,`Más de ${formatDecimal(t[4],scale.decimals)}${scale.unit}`];
    const municipalItems=scale.colors.map((c,i)=>`<span class="map-legend-item"><span class="map-legend-swatch" style="background:${c}"></span>${labels[i]}</span>`).join("");
    const demoMode=getMapDataMode()==="demo";
    legend.innerHTML=`<div class="map-legend-section"><span class="map-legend-heading">Color municipal · ${escapeHTML(metricLabel())}</span><div class="map-legend-list"><span class="map-legend-item"><span class="map-legend-swatch zero"></span>0 / Sin registros</span>${municipalItems}</div>${demoMode&&["vacunacion","avance"].includes(getMapMetric())?'<div class="legend-demo-note">La vacunación municipal es simulada, excepto Dagua.</div>':''}</div><div class="map-legend-section"><span class="map-legend-heading">Puntos de vacunación</span><div class="map-legend-list"><span class="map-legend-item"><span class="map-legend-point"></span>Punto real</span><span class="map-legend-item"><span class="map-legend-point multi"></span>Varias vacunaciones reales</span>${demoMode?'<span class="map-legend-item"><span class="map-legend-point demo"></span>Punto simulado</span><span class="map-legend-item"><span class="map-legend-point demo multi"></span>Varias vacunaciones simuladas</span>':''}</div></div>`;
  }

  function clearFilters() {
    document.getElementById("fYear").value = "2026";
    document.getElementById("fMonth").value = "";
    document.getElementById("fMunicipality").value = "";
    document.getElementById("fAro").value = "";
    document.getElementById("fSpecies").value = "";
    applyFilters();
    if (MAP) MAP.setView(VALLE_CENTER, VALLE_ZOOM);
  }

  function bindDashboardEvents() {
    document.getElementById("btnApply")?.addEventListener("click", applyFilters);
    document.getElementById("btnClear")?.addEventListener("click", clearFilters);
    document.getElementById("btnClearActiveFilters")?.addEventListener("click", clearFilters);
    document.getElementById("btnReload")?.addEventListener("click", loadData);
    document.querySelectorAll('input[name="mapMetric"]').forEach(input => input.addEventListener("change", applyFilters));
    document.querySelectorAll('input[name="mapDataMode"]').forEach(input => input.addEventListener("change", applyFilters));
    document.querySelectorAll('input[name="zoonosisBasemap"]').forEach(input => input.addEventListener("change", () => setBasemap(input.value)));
    ["showRealVaccinationPoints","showDemoVaccinationPoints","showMunicipalPolygons","showMunicipalityLabels","showVeredasValle","showCentrosPoblados","showViasPrincipales","showRios","showRiosLabels","showValleContorno","showMunicipiosUES"].forEach(id => {
      document.getElementById(id)?.addEventListener("change", event => {
        if (id === "showDemoVaccinationPoints") event.target.dataset.userChanged = "1";
        syncMapLayers(); applyFilters();
      });
    });
    document.getElementById("btnMapReset")?.addEventListener("click", () => {
      clearMunicipalitySelection({ apply:true, fitValle:true });
    });
    document.getElementById("btnMapFitRealPoints")?.addEventListener("click", () => {
      if (LAST_REAL_POINT_BOUNDS?.isValid()) MAP?.fitBounds(LAST_REAL_POINT_BOUNDS, { padding:[25,25], maxZoom:15 });
    });
    document.getElementById("btnMapFitDemoPoints")?.addEventListener("click", () => {
      if (LAST_DEMO_POINT_BOUNDS?.isValid()) MAP?.fitBounds(LAST_DEMO_POINT_BOUNDS, { padding:[25,25], maxZoom:12 });
    });
    document.getElementById("vaccinationTableMode")?.addEventListener("change", () => renderVaccinationTable(CURRENT_FILTERED_VACCINATION));
    document.getElementById("btnToggleStatus")?.addEventListener("click", () => {
      const box = document.getElementById("loadAlert");
      const hidden = box.classList.toggle("d-none");
      document.getElementById("btnToggleStatus").textContent = hidden ? "Ver detalle" : "Ocultar detalle";
      document.getElementById("statusHint").textContent = hidden ? "Oculto" : "Visible";
    });
    document.getElementById("btnCloseSession")?.addEventListener("click", () => {
      localStorage.removeItem(ACCESS_KEY);
      location.href = "../../index.html";
    });
    document.querySelectorAll("[data-trend-mode]").forEach(button => {
      button.addEventListener("click", () => setTrendMode(button.dataset.trendMode));
    });
    document.querySelectorAll("[data-municipal-topic]").forEach(button => {
      button.addEventListener("click", () => setMunicipalTopic(button.dataset.municipalTopic));
    });
    document.getElementById("municipalMetric")?.addEventListener("change", event => {
      V6_STATE.municipalMetric = event.target.value;
      applyFilters();
    });
    document.getElementById("aggressionTableMode")?.addEventListener("change", renderAggressionTable);
    document.getElementById("observationTableMode")?.addEventListener("change", renderObservationTable);
    document.getElementById("btnClearVaccinationFilters")?.addEventListener("click", clearVaccinationFilters);
    document.getElementById("btnClearAggressionFilters")?.addEventListener("click", clearAggressionFilters);
    document.getElementById("btnClearObservationFilters")?.addEventListener("click", clearObservationFilters);
    document.getElementById("activeFilters")?.addEventListener("click", event => {
      const button = event.target.closest("[data-clear-filter]");
      if (button) clearSingleFilter(button.dataset.clearFilter);
    });
    ["fYear","fAro","fSpecies"].forEach(id => document.getElementById(id)?.addEventListener("change", applyFilters));
    document.getElementById("fMonth")?.addEventListener("change", () => {
      V6_STATE.monthFromChart = false;
      applyFilters();
    });
    document.getElementById("fMunicipality")?.addEventListener("change", event => {
      const municipality = event.target.value || "";
      if (municipality) selectMunicipality(municipality, { source:"filter", openPopup:true });
      else clearMunicipalitySelection({ apply:true, fitValle:false });
    });
    document.querySelectorAll('#dashboardTabs button[data-bs-toggle="tab"]').forEach(button => {
      button.addEventListener("shown.bs.tab", () => {
        setTimeout(() => {
          Object.values(charts).forEach(chart => chart.resize?.());
          Object.values(tables).forEach(table => table.columns?.adjust());
          MAP?.invalidateSize();
        }, 160);
      });
    });
    document.querySelectorAll(".collapsible-block .collapse").forEach(block => {
      block.addEventListener("shown.bs.collapse", () => setTimeout(() => MAP?.invalidateSize(), 120));
    });
  }


  /* ============================================================
     ZOONOSIS V6.2 · interacción correctiva, módulos cruzados y detalle diario
     ============================================================ */
  Object.assign(URLS, {
    vaccinationDaily: `${DATA_ROOT}/current/vacunacion_diaria.csv`,
    aggressionDaily: `${DATA_ROOT}/current/agresiones_diarias.csv`,
    observationDaily: `${DATA_ROOT}/current/observacion_diaria.csv`,
    visitsDaily: `${DATA_ROOT}/current/visitas_diarias.csv`
  });
  Object.assign(DATA, {
    vaccinationDaily: [],
    aggressionDaily: [],
    observationDaily: [],
    visitsDaily: []
  });

  const V6_STATE = {
    trendMode: "events",
    municipalTopic: "aggression",
    municipalMetric: "aggressions",
    vaccinationFilters: { condition:"", age:"", sterilized:"" },
    aggressionFilters: { sector:"", provoked:"", vaccination:"" },
    observationFilters: { visitBand:"", followup:"", state:"" },
    monthFromChart: false,
    municipalityFromChart: false
  };
  let V6_CURRENT = {
    filters:{}, vaccination:[], vaccinationDaily:[], aggressions:[], aggressionDaily:[],
    observation:[], observationDaily:[], visits:[], visitsDaily:[], municipalities:[]
  };

  const MUNICIPAL_METRICS = {
    vaccination: [
      ["vaccinations","Vacunaciones registradas"],
      ["coverage","Avance frente a población estimada"],
      ["dogs","Caninos vacunados"],
      ["cats","Felinos vacunados"],
      ["first","Primera vez"],
      ["revaccinated","Revacunados"]
    ],
    aggression: [
      ["aggressions","Agresiones reportadas"],
      ["rate","Agresiones por 1.000 animales"],
      ["dogs","Agresiones por perros"],
      ["cats","Agresiones por gatos"]
    ],
    observation: [
      ["cases","Casos en observación"],
      ["one","Casos con una visita"],
      ["two","Casos con dos visitas"],
      ["three","Casos con tres o más visitas"],
      ["complete","Seguimientos completos"],
      ["pending","Seguimientos pendientes"],
      ["compliance","Cumplimiento del seguimiento"]
    ]
  };

  function parseV6DataTypes() {
    DATA.vaccinationDaily = DATA.vaccinationDaily.map(row => ({...row, anio:toNumber(row.anio), mes:toNumber(row.mes), vacunaciones:toNumber(row.vacunaciones)}));
    DATA.aggressionDaily = DATA.aggressionDaily.map(row => ({...row, anio:toNumber(row.anio), mes:toNumber(row.mes), eventos:toNumber(row.eventos)}));
    DATA.observationDaily = DATA.observationDaily.map(row => ({...row, anio:toNumber(row.anio), mes:toNumber(row.mes), eventos:toNumber(row.eventos)}));
    DATA.visitsDaily = DATA.visitsDaily.map(row => ({...row, anio:toNumber(row.anio), mes:toNumber(row.mes), numero_visita:toNumber(row.numero_visita), visitas:toNumber(row.visitas)}));
  }

  async function loadData() {
    setLoadStatus("Cargando archivos agregados y detalle diario de Zoonosis…", "info", true);
    const [metadata, vaccination, vaccinationDaily, vaccinationPoints, aggressions, aggressionDaily, observation, observationDaily, visits, visitsDaily, municipalities, quality, population, demoVaccination, demoVaccinationPoints] = await Promise.all([
      fetchJSON(URLS.metadata), papaCSV(URLS.vaccination), papaCSV(URLS.vaccinationDaily), papaCSV(URLS.vaccinationPoints),
      papaCSV(URLS.aggressions), papaCSV(URLS.aggressionDaily), papaCSV(URLS.observation), papaCSV(URLS.observationDaily),
      papaCSV(URLS.visits), papaCSV(URLS.visitsDaily), papaCSV(URLS.municipalities), papaCSV(URLS.quality), papaCSV(URLS.population),
      papaCSV(URLS.demoVaccination), papaCSV(URLS.demoVaccinationPoints)
    ]);
    Object.assign(DATA, { metadata, vaccination, vaccinationDaily, vaccinationPoints, aggressions, aggressionDaily, observation, observationDaily, visits, visitsDaily, municipalities, quality, population, demoVaccination, demoVaccinationPoints });
    parseDataTypes();
    parseV6DataTypes();
    fillFilters();
    updateSourceLinks();
    updateMetadataStatus();
    initMap();
    initializeMunicipalMetricSelect();
    applyFilters();
  }

  function formatDateDisplay(value) {
    const text = String(value || "").trim();
    if (!/^\d{4}-\d{2}-\d{2}$/.test(text)) return "Sin fecha verificable";
    const [year,month,day] = text.split("-");
    return `${day}/${month}/${year}`;
  }

  function updateInteractionContext(filters) {
    // V6.1: la consulta global se comunica únicamente en Filtros activos.
  }

  function applyFilters() {
    const filters = currentFilters();
    const vaccination = DATA.vaccination.filter(row => matches(row, filters));
    const vaccinationDaily = DATA.vaccinationDaily.filter(row => matches(row, filters));
    const vaccinationPoints = DATA.vaccinationPoints.filter(row => matches(row, filters));
    const aggressions = DATA.aggressions.filter(row => matches(row, filters));
    const aggressionDaily = DATA.aggressionDaily.filter(row => matches(row, filters));
    const observation = DATA.observation.filter(row => matches(row, filters));
    const observationDaily = DATA.observationDaily.filter(row => matches(row, filters));
    const visits = DATA.visits.filter(row => matches(row, filters, { ignoreSpecies: true }));
    const visitsDaily = DATA.visitsDaily.filter(row => matches(row, filters));
    const municipalities = filteredMunicipalities(filters);
    V6_CURRENT = { filters, vaccination, vaccinationDaily, aggressions, aggressionDaily, observation, observationDaily, visits, visitsDaily, municipalities };

    const populationField = denominatorField(filters.species);
    const population = sum(municipalities, populationField);
    const target = Math.ceil(population * 0.8);
    const vaccinationCount = sum(vaccination, "vacunaciones");
    const aggressionCount = sum(aggressions, "eventos");
    const followupComplete = aggressions.filter(row => norm(row.seguimiento_3_visitas) === "CUMPLE").reduce((acc,row) => acc + row.eventos, 0);
    const coverage = population ? vaccinationCount / population * 100 : 0;
    const gap = Math.max(0, target - vaccinationCount);
    const rate = population ? aggressionCount / population * 1000 : 0;

    document.getElementById("kpiVaccinations").textContent = formatInt(vaccinationCount);
    document.getElementById("kpiAggressions").textContent = formatInt(aggressionCount);
    document.getElementById("kpiPopulation").textContent = formatInt(population);
    document.getElementById("kpiCoverage").textContent = formatPercent(coverage);
    document.getElementById("kpiGap").textContent = formatInt(gap);
    document.getElementById("kpiFollowup").textContent = formatInt(followupComplete);
    document.getElementById("kpiRate").textContent = formatDecimal(rate, 2);

    renderActiveFilters(filters);
    updateInteractionContext(filters);
    const trendFilters = {...filters, month:0};
    const trendData = {
      vaccination: DATA.vaccination.filter(row => matches(row, trendFilters)),
      aggressions: DATA.aggressions.filter(row => matches(row, trendFilters)),
      observationDaily: DATA.observationDaily.filter(row => matches(row, trendFilters)),
      visitsDaily: DATA.visitsDaily.filter(row => matches(row, trendFilters))
    };
    renderSummaryCharts(vaccination, aggressions, trendData, filters);
    renderVaccination(vaccination);
    renderAggressions(aggressions);
    renderObservation(observation, observationDaily, visitsDaily);
    renderPopulation(municipalities, filters);
    renderQuality();
    renderMap(vaccination, vaccinationPoints, aggressions, municipalities, filters);
    updateTables(vaccination, vaccinationDaily, aggressions, aggressionDaily, observation, observationDaily, visitsDaily, municipalities);
  }

  function setSegmentActive(selector, dataKey, value) {
    document.querySelectorAll(selector).forEach(button => {
      button.classList.toggle("active", button.dataset[dataKey] === value);
      button.setAttribute("aria-pressed", button.dataset[dataKey] === value ? "true" : "false");
    });
  }

  function setMapMetricValue(value) {
    const input = document.querySelector(`input[name="mapMetric"][value="${value}"]`);
    if (input) input.checked = true;
  }

  function setTrendMode(mode) {
    if (!["events","followup"].includes(mode)) return;
    V6_STATE.trendMode = mode;
    setSegmentActive("[data-trend-mode]", "trendMode", mode);
    applyFilters();
  }

  function setMunicipalTopic(topic) {
    if (!MUNICIPAL_METRICS[topic]) return;
    V6_STATE.municipalTopic = topic;
    V6_STATE.municipalMetric = MUNICIPAL_METRICS[topic][0][0];
    setSegmentActive("[data-municipal-topic]", "municipalTopic", topic);
    initializeMunicipalMetricSelect();
    if (topic === "vaccination") setMapMetricValue("vacunacion");
    if (topic === "aggression") setMapMetricValue("agresiones");
    applyFilters();
  }

  function initializeMunicipalMetricSelect() {
    const select = document.getElementById("municipalMetric");
    if (!select) return;
    const options = MUNICIPAL_METRICS[V6_STATE.municipalTopic] || [];
    if (!options.some(([value]) => value === V6_STATE.municipalMetric)) V6_STATE.municipalMetric = options[0]?.[0] || "aggressions";
    select.innerHTML = options.map(([value,label]) => `<option value="${value}">${label}</option>`).join("");
    select.value = V6_STATE.municipalMetric;
  }

  function monthlyArray(rows, valueField) {
    const values = Array(12).fill(0);
    rows.forEach(row => { const month=toNumber(row.mes); if(month>=1&&month<=12) values[month-1]+=toNumber(row[valueField]); });
    return values;
  }

  function setMonthFromTrend(monthIndex) {
    const month = monthIndex + 1;
    const select = document.getElementById("fMonth");
    if (!select) return;
    if (toNumber(select.value) === month) {
      select.value = "";
      V6_STATE.monthFromChart = false;
    } else {
      select.value = String(month);
      V6_STATE.monthFromChart = true;
    }
    applyFilters();
  }

  function renderSummaryCharts(vaccination, aggressions, trendData, filters) {
    const trendTitle = document.getElementById("trendChartTitle");
    const trendSubtitle = document.getElementById("trendChartSubtitle");
    let datasets = [];
    if (V6_STATE.trendMode === "followup") {
      if (trendTitle) trendTitle.textContent = "Tendencia mensual del seguimiento de animales agresores";
      if (trendSubtitle) trendSubtitle.textContent = "Casos abiertos, visitas realizadas y seguimientos completados por mes.";
      const cases = monthlyArray(trendData.observationDaily, "eventos");
      const visit1 = monthlyArray(trendData.visitsDaily.filter(r=>r.numero_visita===1), "visitas");
      const visit2 = monthlyArray(trendData.visitsDaily.filter(r=>r.numero_visita===2), "visitas");
      const visit3 = monthlyArray(trendData.visitsDaily.filter(r=>r.numero_visita===3), "visitas");
      const complete = monthlyArray(trendData.visitsDaily.filter(r=>r.numero_visita===3 && norm(r.seguimiento_3_visitas)==="CUMPLE"), "visitas");
      datasets = [
        {label:"Casos en observación",data:cases,borderColor:"#2e64d2",backgroundColor:"rgba(46,100,210,.08)",tension:.25},
        {label:"Visita 1",data:visit1,borderColor:"#0891b2",backgroundColor:"transparent",tension:.25},
        {label:"Visita 2",data:visit2,borderColor:"#f59e0b",backgroundColor:"transparent",tension:.25},
        {label:"Visita 3",data:visit3,borderColor:"#7c3aed",backgroundColor:"transparent",tension:.25},
        {label:"Seguimientos completos",data:complete,borderColor:"#16a34a",backgroundColor:"rgba(22,163,74,.08)",tension:.25,fill:true}
      ];
    } else {
      if (trendTitle) trendTitle.textContent = "Tendencia mensual de la vigilancia de zoonosis";
      if (trendSubtitle) trendSubtitle.textContent = "Vacunaciones, agresiones y casos que ingresan a observación.";
      datasets = [
        {label:"Vacunaciones",data:monthlyArray(trendData.vaccination,"vacunaciones"),borderColor:"#16a34a",backgroundColor:"rgba(22,163,74,.10)",tension:.25,fill:true},
        {label:"Agresiones",data:monthlyArray(trendData.aggressions,"eventos"),borderColor:"#dc2626",backgroundColor:"rgba(220,38,38,.06)",tension:.25,fill:true},
        {label:"Casos en observación",data:monthlyArray(trendData.observationDaily,"eventos"),borderColor:"#2e64d2",backgroundColor:"transparent",tension:.25}
      ];
    }
    createChart("chartTrend", {
      type:"line", data:{labels:MONTHS,datasets},
      options:{responsive:true,maintainAspectRatio:false,interaction:{mode:"index",intersect:false},plugins:{legend:{position:"top"}},elements:{point:{radius:ctx=>toNumber(filters.month)===ctx.dataIndex+1?6:3,hoverRadius:7,borderWidth:ctx=>toNumber(filters.month)===ctx.dataIndex+1?3:1}},scales:{y:{beginAtZero:true}},onClick:(event,elements)=>{if(elements.length)setMonthFromTrend(elements[0].index);}}
    });

    const vaccSpecies = groupSum(vaccination, "especie", "vacunaciones");
    const aggSpecies = groupSum(aggressions, "especie", "eventos");
    const species = [...new Set([...vaccSpecies.keys(), ...aggSpecies.keys()])].sort();
    createChart("chartSpecies", {type:"bar",data:{labels:species,datasets:[
      {label:"Vacunaciones",data:species.map(k=>vaccSpecies.get(k)||0),backgroundColor:"rgba(22,163,74,.55)",borderColor:"#16a34a",borderWidth:1,borderRadius:6},
      {label:"Agresiones",data:species.map(k=>aggSpecies.get(k)||0),backgroundColor:"rgba(220,38,38,.45)",borderColor:"#dc2626",borderWidth:1,borderRadius:6}
    ]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{position:"top"}},scales:{y:{beginAtZero:true}}}});
    renderMunicipalChart(filters);
  }

  function municipalMetricRows(filters) {
    const comparisonFilters = {...filters, municipality:""};
    const municipalities = DATA.municipalities.filter(row => !comparisonFilters.aro || norm(row.area_operativa)===norm(comparisonFilters.aro));
    const vaccination = DATA.vaccination.filter(row => matches(row, comparisonFilters));
    const aggressions = DATA.aggressions.filter(row => matches(row, comparisonFilters));
    const observation = DATA.observation.filter(row => matches(row, comparisonFilters));
    const demo = getMapDataMode()==="demo" ? demoVaccinationByMunicipality() : new Map();
    return municipalities.map(m => {
      const name=m.municipio;
      const vRows=vaccination.filter(r=>norm(r.municipio)===norm(name));
      const aRows=aggressions.filter(r=>norm(r.municipio)===norm(name));
      const oRows=observation.filter(r=>norm(r.municipio)===norm(name));
      let vacc=sum(vRows,"vacunaciones"), dogsV=sum(vRows.filter(r=>norm(r.especie)==="CANINO"),"vacunaciones"), catsV=sum(vRows.filter(r=>norm(r.especie)==="FELINO"),"vacunaciones");
      let first=sum(vRows.filter(r=>norm(r.condicion)==="PRIMERA VEZ"),"vacunaciones"), revaccinated=sum(vRows.filter(r=>norm(r.condicion)==="REVACUNADO"),"vacunaciones");
      if (demo.has(norm(name))) { const d=demo.get(norm(name)); vacc=toNumber(d.vacunaciones_demo); dogsV=toNumber(d.caninos_demo); catsV=toNumber(d.felinos_demo); first=Math.round(vacc*.42); revaccinated=vacc-first; }
      const pop=toNumber(m[denominatorField(filters.species)]), agg=sum(aRows,"eventos");
      const complete=sum(oRows.filter(r=>norm(r.seguimiento_3_visitas)==="CUMPLE"),"eventos");
      const cases=sum(oRows,"eventos");
      return {name,vaccinations:vacc,coverage:pop?vacc/pop*100:0,dogsVacc:dogsV,catsVacc:catsV,first,revaccinated,
        aggressions:agg,rate:pop?agg/pop*1000:0,dogsAgg:sum(aRows.filter(r=>norm(r.especie)==="CANINO"),"eventos"),catsAgg:sum(aRows.filter(r=>norm(r.especie)==="FELINO"),"eventos"),
        cases,one:sum(oRows.filter(r=>norm(r.categoria_visitas)==="1 VISITA"),"eventos"),two:sum(oRows.filter(r=>norm(r.categoria_visitas)==="2 VISITAS"),"eventos"),three:sum(oRows.filter(r=>norm(r.categoria_visitas)==="3 O MÁS VISITAS"),"eventos"),complete,pending:Math.max(0,cases-complete),compliance:cases?complete/cases*100:0};
    });
  }

  function renderMunicipalChart(filters) {
    initializeMunicipalMetricSelect();
    const metric=V6_STATE.municipalMetric, topic=V6_STATE.municipalTopic;
    const map={vaccination:{vaccinations:"vaccinations",coverage:"coverage",dogs:"dogsVacc",cats:"catsVacc",first:"first",revaccinated:"revaccinated"},aggression:{aggressions:"aggressions",rate:"rate",dogs:"dogsAgg",cats:"catsAgg"},observation:{cases:"cases",one:"one",two:"two",three:"three",complete:"complete",pending:"pending",compliance:"compliance"}};
    const field=map[topic]?.[metric] || "aggressions";
    const label=(MUNICIPAL_METRICS[topic]||[]).find(([v])=>v===metric)?.[1] || "Indicador";
    const allRows=municipalMetricRows(filters).sort((a,b)=>b[field]-a[field]);
    let rows=allRows.slice(0,15);
    const selectedName=filters.municipality || "";
    if(selectedName && !rows.some(r=>norm(r.name)===norm(selectedName))){
      const selectedRow=allRows.find(r=>norm(r.name)===norm(selectedName));
      if(selectedRow) rows=[...rows.slice(0,14),selectedRow];
    }
    const percentage=["coverage","compliance"].includes(metric);
    const selectedColor=topic==="vaccination"?"#15803d":topic==="observation"?"#6d28d9":"#b91c1c";
    const normalColor=topic==="vaccination"?"rgba(22,163,74,.52)":topic==="observation"?"rgba(124,58,237,.45)":"rgba(220,38,38,.45)";
    const borderColor=topic==="vaccination"?"#16a34a":topic==="observation"?"#7c3aed":"#dc2626";
    document.getElementById("municipalChartTitle").textContent=`${label} por municipio`;
    document.getElementById("municipalChartSubtitle").textContent=`${getMapDataMode()==="demo"&&topic==="vaccination"?"Modo demostración · ":""}Haz clic en una barra para filtrar; repite el clic para quitar el municipio.`;
    createChart("chartMunicipal", {type:"bar",data:{labels:rows.map(r=>r.name),datasets:[{label,data:rows.map(r=>r[field]),backgroundColor:rows.map(r=>selectedName&&norm(r.name)===norm(selectedName)?selectedColor:normalColor),borderColor:rows.map(r=>selectedName&&norm(r.name)===norm(selectedName)?"#0f172a":borderColor),borderWidth:rows.map(r=>selectedName&&norm(r.name)===norm(selectedName)?2:1),borderRadius:6}]},options:{responsive:true,maintainAspectRatio:false,indexAxis:"y",plugins:{legend:{display:false},tooltip:{callbacks:{label:ctx=>percentage?` ${formatPercent(ctx.raw)}`:` ${formatInt(ctx.raw)}`}}},scales:{x:{beginAtZero:true,ticks:{callback:v=>percentage?`${v}%`:v}}},onClick:(event,elements)=>{if(!elements.length)return;const municipality=rows[elements[0].index]?.name;selectMunicipalityFromChart(municipality);}}});
  }

  function selectMunicipalityFromChart(municipality) {
    selectMunicipality(municipality, { source:"chart", openPopup:true });
  }

  function vaccinationRowsWithFilters(rows, exclude="") {
    const f = V6_STATE.vaccinationFilters;
    return rows.filter(row => {
      if (exclude !== "condition" && f.condition && norm(row.condicion) !== norm(f.condition)) return false;
      if (exclude !== "age" && f.age && norm(row.grupo_edad) !== norm(f.age)) return false;
      if (exclude !== "sterilized" && f.sterilized && norm(row.esterilizado) !== norm(f.sterilized)) return false;
      return true;
    });
  }

  function aggressionRowsWithFilters(rows, exclude="") {
    const f = V6_STATE.aggressionFilters;
    return rows.filter(row => {
      if (exclude !== "sector" && f.sector && norm(row.sector) !== norm(f.sector)) return false;
      if (exclude !== "provoked" && f.provoked && norm(row.provocado) !== norm(f.provoked)) return false;
      if (exclude !== "vaccination" && f.vaccination && norm(row.condicion_vacunacion) !== norm(f.vaccination)) return false;
      return true;
    });
  }

  function updateLocalFilterStrip(type, filters, labels) {
    const parts = Object.entries(filters).filter(([,value]) => value).map(([key,value]) => `${labels[key]}: ${value}`);
    const strip = document.getElementById(`${type}InteractionStrip`);
    const text = document.getElementById(`${type}ChartFilters`);
    if (text) text.textContent = parts.join(" · ");
    strip?.classList.toggle("d-none", parts.length === 0);
  }

  function toggleVaccinationFilter(key, value) {
    V6_STATE.vaccinationFilters[key] = norm(V6_STATE.vaccinationFilters[key]) === norm(value) ? "" : value;
    renderVaccination(V6_CURRENT.vaccination);
    renderVaccinationTable();
  }

  function toggleAggressionFilter(key, value) {
    V6_STATE.aggressionFilters[key] = norm(V6_STATE.aggressionFilters[key]) === norm(value) ? "" : value;
    renderAggressions(V6_CURRENT.aggressions);
    renderAggressionTable();
  }

  function clearVaccinationFilters() {
    V6_STATE.vaccinationFilters = { condition:"", age:"", sterilized:"" };
    renderVaccination(V6_CURRENT.vaccination);
    renderVaccinationTable();
  }

  function clearAggressionFilters() {
    V6_STATE.aggressionFilters = { sector:"", provoked:"", vaccination:"" };
    renderAggressions(V6_CURRENT.aggressions);
    renderAggressionTable();
  }

  function clearObservationFilters() {
    V6_STATE.observationFilters = { visitBand:"", followup:"", state:"" };
    renderObservation(V6_CURRENT.observation, V6_CURRENT.observationDaily, V6_CURRENT.visitsDaily);
    renderObservationTable();
  }

  function interactiveDoughnutWithToggle(id, labels, values, toggleCallback) {
    const config = doughnutConfig(labels, values);
    config.options.onClick = (event, elements) => {
      if (!elements.length) return;
      toggleCallback(labels[elements[0].index]);
    };
    createChart(id, config);
  }

  function renderVaccination(rows) {
    const selected = vaccinationRowsWithFilters(rows);
    const bySpecies = groupSum(selected, "especie", "vacunaciones");
    const byCondition = groupSum(vaccinationRowsWithFilters(rows, "condition"), "condicion", "vacunaciones");
    const byAge = sortedEntries(groupSum(vaccinationRowsWithFilters(rows, "age"), "grupo_edad", "vacunaciones"), false);
    const bySterilization = groupSum(vaccinationRowsWithFilters(rows, "sterilized"), "esterilizado", "vacunaciones");
    document.getElementById("vaccDogs").textContent = formatInt(bySpecies.get("CANINO") || 0);
    document.getElementById("vaccCats").textContent = formatInt(bySpecies.get("FELINO") || 0);
    document.getElementById("vaccFirst").textContent = formatInt(groupSum(selected, "condicion", "vacunaciones").get("PRIMERA VEZ") || 0);
    document.getElementById("vaccRe").textContent = formatInt(groupSum(selected, "condicion", "vacunaciones").get("REVACUNADO") || 0);
    interactiveDoughnutWithToggle("chartVaccCondition", [...byCondition.keys()], [...byCondition.values()], value => toggleVaccinationFilter("condition", value));
    createChart("chartVaccAge", {
      type:"bar",
      data:{labels:byAge.map(item=>item[0]),datasets:[{data:byAge.map(item=>item[1]),backgroundColor:"rgba(46,100,210,.55)",borderColor:"#2e64d2",borderWidth:1,borderRadius:5}]},
      options:{responsive:true,maintainAspectRatio:false,indexAxis:"y",plugins:{legend:{display:false}},scales:{x:{beginAtZero:true}},onClick:(event,elements)=>{if(elements.length)toggleVaccinationFilter("age",byAge[elements[0].index][0]);}}
    });
    interactiveDoughnutWithToggle("chartSterilization", [...bySterilization.keys()], [...bySterilization.values()], value => toggleVaccinationFilter("sterilized", value));
    const f = V6_STATE.vaccinationFilters;
    updateLocalFilterStrip("vaccination", f, {condition:"Condición",age:"Edad",sterilized:"Esterilización"});
    document.getElementById("chartVaccCondition")?.closest(".chart-card")?.classList.toggle("selected-filter", Boolean(f.condition));
    document.getElementById("chartVaccAge")?.closest(".chart-card")?.classList.toggle("selected-filter", Boolean(f.age));
    document.getElementById("chartSterilization")?.closest(".chart-card")?.classList.toggle("selected-filter", Boolean(f.sterilized));
  }

  function renderAggressions(rows) {
    const selected = aggressionRowsWithFilters(rows);
    const bySpecies = groupSum(selected, "especie", "eventos");
    const bySector = groupSum(aggressionRowsWithFilters(rows, "sector"), "sector", "eventos");
    const byProvoked = groupSum(aggressionRowsWithFilters(rows, "provoked"), "provocado", "eventos");
    const byVaccine = groupSum(aggressionRowsWithFilters(rows, "vaccination"), "condicion_vacunacion", "eventos");
    document.getElementById("aggDogs").textContent = formatInt(bySpecies.get("CANINO") || 0);
    document.getElementById("aggCats").textContent = formatInt(bySpecies.get("FELINO") || 0);
    document.getElementById("aggUnknownVacc").textContent = formatInt(groupSum(selected, "condicion_vacunacion", "eventos").get("DESCONOCIDO") || 0);
    document.getElementById("aggRural").textContent = formatInt(groupSum(selected, "sector", "eventos").get("RURAL") || 0);
    interactiveDoughnutWithToggle("chartSector", [...bySector.keys()], [...bySector.values()], value => toggleAggressionFilter("sector", value));
    interactiveDoughnutWithToggle("chartProvoked", [...byProvoked.keys()], [...byProvoked.values()], value => toggleAggressionFilter("provoked", value));
    interactiveDoughnutWithToggle("chartAnimalVaccination", [...byVaccine.keys()], [...byVaccine.values()], value => toggleAggressionFilter("vaccination", value));
    const f = V6_STATE.aggressionFilters;
    updateLocalFilterStrip("aggression", f, {sector:"Sector",provoked:"Provocada",vaccination:"Vacunación animal"});
    document.getElementById("chartSector")?.closest(".chart-card")?.classList.toggle("selected-filter", Boolean(f.sector));
    document.getElementById("chartProvoked")?.closest(".chart-card")?.classList.toggle("selected-filter", Boolean(f.provoked));
    document.getElementById("chartAnimalVaccination")?.closest(".chart-card")?.classList.toggle("selected-filter", Boolean(f.vaccination));
  }

  function observationRowsWithFilters(rows, exclude="") {
    const f=V6_STATE.observationFilters;
    return rows.filter(row => {
      if(exclude!=="visitBand" && f.visitBand && norm(row.categoria_visitas)!==norm(f.visitBand)) return false;
      if(exclude!=="followup" && f.followup && norm(row.seguimiento_3_visitas)!==norm(f.followup)) return false;
      if(exclude!=="state" && f.state && norm(row.estado_animal)!==norm(f.state)) return false;
      return true;
    });
  }

  function toggleObservationFilter(key,value) {
    V6_STATE.observationFilters[key] = norm(V6_STATE.observationFilters[key])===norm(value) ? "" : value;
    renderObservation(V6_CURRENT.observation,V6_CURRENT.observationDaily,V6_CURRENT.visitsDaily);
    renderObservationTable();
    updateInteractionContext(V6_CURRENT.filters);
  }

  function interactiveDoughnut(id, labels, values, filterKey) {
    const config=doughnutConfig(labels,values);
    config.options.onClick=(event,elements)=>{if(elements.length)toggleObservationFilter(filterKey,labels[elements[0].index]);};
    createChart(id,config);
  }

  function renderObservation(rows, dailyRows, visitRows) {
    const selected=observationRowsWithFilters(rows);
    const byBand=groupSum(observationRowsWithFilters(rows,"visitBand"),"categoria_visitas","eventos");
    const byFollowup=groupSum(observationRowsWithFilters(rows,"followup"),"seguimiento_3_visitas","eventos");
    const byState=sortedEntries(groupSum(observationRowsWithFilters(rows,"state"),"estado_animal","eventos")).slice(0,8);
    const selectedBand=groupSum(selected,"categoria_visitas","eventos"), selectedFollow=groupSum(selected,"seguimiento_3_visitas","eventos");
    document.getElementById("obsOne").textContent=formatInt(selectedBand.get("1 VISITA")||0);
    document.getElementById("obsTwo").textContent=formatInt(selectedBand.get("2 VISITAS")||0);
    document.getElementById("obsThree").textContent=formatInt(selectedBand.get("3 O MÁS VISITAS")||0);
    document.getElementById("obsComplete").textContent=formatInt(selectedFollow.get("CUMPLE")||0);
    interactiveDoughnut("chartVisitBand",[...byBand.keys()],[...byBand.values()],"visitBand");
    interactiveDoughnut("chartFollowup",[...byFollowup.keys()],[...byFollowup.values()],"followup");
    createChart("chartAnimalState",{type:"bar",data:{labels:byState.map(i=>i[0]),datasets:[{data:byState.map(i=>i[1]),backgroundColor:"rgba(25,135,84,.5)",borderColor:"#198754",borderWidth:1,borderRadius:5}]},options:{responsive:true,maintainAspectRatio:false,indexAxis:"y",plugins:{legend:{display:false}},scales:{x:{beginAtZero:true}},onClick:(event,elements)=>{if(elements.length)toggleObservationFilter("state",byState[elements[0].index][0]);}}});
    const f=V6_STATE.observationFilters; const parts=[];
    if(f.visitBand)parts.push(f.visitBand);if(f.followup)parts.push(f.followup);if(f.state)parts.push(f.state);
    const strip=document.getElementById("observationInteractionStrip");
    const text=document.getElementById("observationChartFilters");
    if(text) text.textContent=parts.join(" · ");
    strip?.classList.toggle("d-none",parts.length===0);
    document.getElementById("chartVisitBand")?.closest(".chart-card")?.classList.toggle("selected-filter",Boolean(f.visitBand));
    document.getElementById("chartFollowup")?.closest(".chart-card")?.classList.toggle("selected-filter",Boolean(f.followup));
    document.getElementById("chartAnimalState")?.closest(".chart-card")?.classList.toggle("selected-filter",Boolean(f.state));
  }

  function aggregateByFields(rows, fields, valueField) {
    const grouped=new Map();
    rows.forEach(row=>{const values=fields.map(f=>String(row[f]??""));const key=JSON.stringify(values);if(!grouped.has(key))grouped.set(key,{values,total:0});grouped.get(key).total+=toNumber(row[valueField]);});
    return [...grouped.values()].sort((a,b)=>b.total-a.total);
  }

  function formatTableValue(field,value) {
    if(field.startsWith("fecha"))return formatDateDisplay(value);
    if(field==="mes")return MONTHS[toNumber(value)-1]||"Sin fecha verificable";
    return value||"Sin dato";
  }

  function renderVaccinationTable(vaccination=V6_CURRENT.vaccination) {
    CURRENT_FILTERED_VACCINATION=vaccination;
    const mode=document.getElementById("vaccinationTableMode")?.value||"territorio";
    const daily=vaccinationRowsWithFilters(V6_CURRENT.vaccinationDaily);
    const monthly=vaccinationRowsWithFilters(vaccination);
    const configs={
      territorio:{source:monthly,fields:["anio","mes","municipio","area_operativa","especie","condicion"],titles:["AÑO","MES","MUNICIPIO","ARO","ESPECIE","CONDICIÓN"],text:"La vista mensual resume el volumen por territorio, especie y condición."},
      diario:{source:daily,fields:["fecha","municipio","area_operativa","especie","condicion"],titles:["FECHA","MUNICIPIO","ARO","ESPECIE","CONDICIÓN"],text:"La actividad diaria permite identificar jornadas y productividad por fecha."},
      lote:{source:daily,fields:["fecha","municipio","vacuna","lote","especie","condicion"],titles:["FECHA","MUNICIPIO","VACUNA","LOTE","ESPECIE","CONDICIÓN"],text:"La trazabilidad diaria relaciona fecha, biológico y lote sin exponer datos del propietario."},
      perfil:{source:daily,fields:["fecha","municipio","area_operativa","especie","sexo","condicion","grupo_edad","esterilizado","vacuna","lote"],titles:["FECHA","MUNICIPIO","ARO","ESPECIE","SEXO","CONDICIÓN","GRUPO EDAD","ESTERILIZADO","VACUNA","LOTE"],text:"El perfil analítico diario agrega registros con las mismas características visibles."}
    };
    const c=configs[mode]||configs.territorio;const grouped=aggregateByFields(c.source,c.fields,"vacunaciones");
    const rows=grouped.map(g=>g.values.map((v,i)=>formatTableValue(c.fields[i],v)).concat(formatInt(g.total)));
    const columns=c.titles.map(title=>({title})).concat({title:"VACUNACIONES"});
    renderTable("tblVaccination",rows,columns,"ZOONOSIS_VACUNACION",[[columns.length-1,"desc"]]);
    document.getElementById("vaccinationTableSummary").innerHTML=`<strong>${formatInt(grouped.length)}</strong> filas agregadas · <strong>${formatInt(sum(c.source,"vacunaciones"))}</strong> vacunaciones`;
    document.getElementById("vaccinationTableExplanation").innerHTML=`<strong>Cómo leer:</strong> ${c.text} La última columna suma los registros de cada combinación.`;
  }

  function renderAggressionTable() {
    const mode=document.getElementById("aggressionTableMode")?.value||"monthly";
    const source=mode==="daily"?aggressionRowsWithFilters(V6_CURRENT.aggressionDaily):aggressionRowsWithFilters(V6_CURRENT.aggressions);
    let rows,columns;
    if(mode==="daily"){
      rows=source.map(r=>[formatDateDisplay(r.fecha_agresion),formatDateDisplay(r.fecha_primera_visita),r.municipio,r.area_operativa,r.especie,r.sector,r.provocado,r.condicion_vacunacion,r.seguimiento_3_visitas,r.estado_animal,formatInt(r.eventos)]);
      columns=["FECHA AGRESIÓN","PRIMERA VISITA","MUNICIPIO","ARO","ESPECIE","SECTOR","PROVOCADO","VACUNACIÓN ANIMAL","SEGUIMIENTO","ESTADO ANIMAL","EVENTOS"].map(title=>({title}));
    }else{
      rows=source.map(r=>[r.anio||"Sin fecha",MONTHS[r.mes-1]||"Sin fecha verificable",r.municipio,r.area_operativa,r.especie,r.sector,r.provocado,r.condicion_vacunacion,r.seguimiento_3_visitas,formatInt(r.eventos)]);
      columns=["AÑO","MES","MUNICIPIO","ARO","ESPECIE","SECTOR","PROVOCADO","VACUNACIÓN ANIMAL","SEGUIMIENTO","EVENTOS"].map(title=>({title}));
    }
    renderTable("tblAggressions",rows,columns,"ZOONOSIS_AGRESIONES",[[columns.length-1,"desc"]]);
    document.getElementById("aggressionTableSummary").innerHTML=`<strong>${formatInt(rows.length)}</strong> filas · <strong>${formatInt(sum(source,"eventos"))}</strong> eventos`;
  }

  function renderObservationTable() {
    const mode=document.getElementById("observationTableMode")?.value||"monthly";
    let source,rows,columns,valueField;
    if(mode==="visits"){
      source=observationRowsWithFilters(V6_CURRENT.visitsDaily);valueField="visitas";
      rows=source.map(r=>[formatDateDisplay(r.fecha_visita),r.municipio,r.area_operativa,r.especie,r.numero_visita,r.dentro_10_dias,r.categoria_visitas,r.seguimiento_3_visitas,r.estado_animal,formatInt(r.visitas)]);
      columns=["FECHA VISITA","MUNICIPIO","ARO","ESPECIE","NÚMERO VISITA","DENTRO 10 DÍAS","TOTAL VISITAS DEL CASO","RESULTADO","ESTADO ANIMAL","VISITAS"].map(title=>({title}));
    }else if(mode==="daily"){
      source=observationRowsWithFilters(V6_CURRENT.observationDaily);valueField="eventos";
      rows=source.map(r=>[formatDateDisplay(r.fecha_apertura),formatDateDisplay(r.fecha_agresion),r.municipio,r.area_operativa,r.especie,r.categoria_visitas,r.seguimiento_3_visitas,r.estado_animal,formatInt(r.eventos)]);
      columns=["FECHA APERTURA","FECHA AGRESIÓN","MUNICIPIO","ARO","ESPECIE","VISITAS","RESULTADO","ESTADO ANIMAL","CASOS"].map(title=>({title}));
    }else{
      source=observationRowsWithFilters(V6_CURRENT.observation);valueField="eventos";
      rows=source.map(r=>[r.anio||"Sin fecha",MONTHS[r.mes-1]||"Sin fecha verificable",r.municipio,r.area_operativa,r.especie,r.categoria_visitas,r.seguimiento_3_visitas,r.estado_animal,formatInt(r.eventos)]);
      columns=["AÑO","MES","MUNICIPIO","ARO","ESPECIE","VISITAS","RESULTADO","ESTADO ANIMAL","CASOS"].map(title=>({title}));
    }
    renderTable("tblObservation",rows,columns,"ZOONOSIS_OBSERVACION",[[columns.length-1,"desc"]]);
    document.getElementById("observationTableSummary").innerHTML=`<strong>${formatInt(rows.length)}</strong> filas · <strong>${formatInt(sum(source,valueField))}</strong> ${mode==="visits"?"visitas":"casos"}`;
  }

  function updateTables(vaccination, vaccinationDaily, aggressions, aggressionDaily, observation, observationDaily, visitsDaily, municipalities) {
    renderVaccinationTable(vaccination);renderAggressionTable();renderObservationTable();
    renderTable("tblPopulation",municipalities.map(r=>[r.codigo_dane,r.municipio,r.area_operativa,formatInt(r.poblacion_perros_2025),formatInt(r.poblacion_gatos_2025),formatInt(r.poblacion_total_animales_2025),formatInt(r.meta_80_total_animales),formatPercent(r.cobertura_oficial_2025_pct)]),["CÓDIGO DANE","MUNICIPIO","ARO","PERROS 2025","GATOS 2025","TOTAL ANIMALES","META 80 %","COBERTURA OFICIAL 2025"].map(title=>({title})),"ZOONOSIS_POBLACION_REFERENCIA",[[5,"desc"]]);
    renderTable("tblQuality",DATA.quality.map(r=>[r.fuente_datos,r.tipo_inconsistencia,formatInt(r.cantidad),r.nivel]),["FUENTE","TIPO DE INCONSISTENCIA","CANTIDAD","NIVEL"].map(title=>({title})),"ZOONOSIS_CALIDAD_DATOS",[[2,"desc"]]);
  }

  function showDashboardTab(buttonId) {
    const button=document.getElementById(buttonId);if(!button)return;
    bootstrap.Tab.getOrCreateInstance(button).show();
  }

  function clearChartSelections() {
    V6_STATE.vaccinationFilters={condition:"",age:"",sterilized:""};
    V6_STATE.aggressionFilters={sector:"",provoked:"",vaccination:""};
    V6_STATE.observationFilters={visitBand:"",followup:"",state:""};
    if(V6_STATE.monthFromChart)document.getElementById("fMonth").value="";
    if(V6_STATE.municipalityFromChart){
      document.getElementById("fMunicipality").value="";
      MAP_SELECTED_MUNICIPALITY="";
      selectedMunicipalityBounds=null;
      pendingMunicipalityFocus=null;
    }
    V6_STATE.monthFromChart=false;V6_STATE.municipalityFromChart=false;applyFilters();
  }

  function clearFilters() {
    document.getElementById("fYear").value="2026";document.getElementById("fMonth").value="";document.getElementById("fMunicipality").value="";document.getElementById("fAro").value="";document.getElementById("fSpecies").value="";
    MAP_SELECTED_MUNICIPALITY="";selectedMunicipalityBounds=null;pendingMunicipalityFocus=null;
    V6_STATE.vaccinationFilters={condition:"",age:"",sterilized:""};V6_STATE.aggressionFilters={sector:"",provoked:"",vaccination:""};V6_STATE.observationFilters={visitBand:"",followup:"",state:""};V6_STATE.monthFromChart=false;V6_STATE.municipalityFromChart=false;applyFilters();
    if(VALLE_BOUNDS?.isValid())MAP?.fitBounds(VALLE_BOUNDS,{padding:[12,12]});else MAP?.setView(VALLE_CENTER,VALLE_ZOOM);
  }


  const INTERFACE_VERSION = "6.4.0";

  function startDashboard() {
    if (started) return;
    started = true;
    bindDashboardEvents();
    loadData().catch(error => {
      console.error(error);
      const badge = document.getElementById("lastUpdate");
      badge.textContent = "Error cargando datos";
      badge.className = "badge text-bg-danger last-update-badge";
      setLoadStatus(`<b>No fue posible cargar los archivos del tablero.</b><br>${escapeHTML(error.message || error)}.<br>Abra el proyecto mediante un servidor local o GitHub Pages; no use directamente el protocolo file://.`, "danger", true);
    });
  }

  document.addEventListener("DOMContentLoaded", initAccess);
})();
