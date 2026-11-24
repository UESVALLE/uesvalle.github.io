'use strict';

const root = '../../';
const display = new Intl.NumberFormat('es-CO', {minimumGroupingDigits: 1});
const $ = id => document.getElementById(id);
const sections = [...document.querySelectorAll('main .chapter')];
const select = $('municipio');
let data;
let schoolOffset = 0;
let currentSlide = 0;
let presenting = false;
let ownFullscreen = false;

function format(value) {
  return display.format(Number(value) || 0);
}

function pct(ratio) {
  return (ratio * 100).toFixed(1).replace('.', ',') + ' %';
}

const LEVELS = [
  ['SIN RIESGO', 'Sin riesgo', '#2E9E6B'], ['BAJO', 'Bajo', '#9ED3B4'], ['MEDIO', 'Medio', '#F0B429'],
  ['ALTO', 'Alto', '#E8710A'], ['INVIABLE SANITARIAMENTE', 'Inviable sanitariamente', '#8F2D0A'], ['SIN DATO', 'Sin dato', '#B9C2CE']
];

function riskSummary(schools) {
  const levels = Object.fromEntries(LEVELS.map(([key]) => [key, {students: 0, schools: 0}]));
  const towns = {};
  let total = 0;
  for (const school of schools) {
    const students = Number(school.ESTUDIANTES_ACTUAL) || 0;
    const level = levels[school.NIVEL_RIESGO_IRCA] || levels['SIN DATO'];
    level.students += students;
    level.schools += 1;
    total += students;
    const town = towns[school.MUNICIPIO_NORM] ||= {none: 0, all: 0};
    town.all += students;
    if (school.NIVEL_RIESGO_IRCA === 'SIN RIESGO') town.none += students;
  }
  const porMunicipio = {};
  for (const [town, value] of Object.entries(towns)) if (value.all > 0) porMunicipio[town] = value.none / value.all;
  return {levels, total, porMunicipio, totalRatio: total ? levels['SIN RIESGO'].students / total : 0};
}

function showRisk() {
  const summary = data.sinRiesgo;
  $('pct-sin-riesgo').textContent = pct(summary.totalRatio);
  $('est-sin-riesgo').textContent = format(summary.levels['SIN RIESGO'].students);
  $('est-total').textContent = format(summary.total);
  $('sedes-sin-riesgo').textContent = format(summary.levels['SIN RIESGO'].schools);
  const high = summary.levels['ALTO'].students + summary.levels['INVIABLE SANITARIAMENTE'].students;
  $('pct-alto').textContent = pct(summary.total ? high / summary.total : 0);
  const bar = $('barra-riesgo');
  const legend = $('leyenda-riesgo');
  for (const [key, label, color] of LEVELS) {
    const level = summary.levels[key];
    const share = summary.total ? level.students / summary.total : 0;
    const segment = document.createElement('i');
    segment.style.cssText = 'width:' + (share * 100).toFixed(2) + '%;background:' + color;
    segment.title = label + ' · ' + pct(share);
    bar.append(segment);
    const item = document.createElement('li');
    const swatch = document.createElement('span');
    swatch.style.background = color;
    const strong = element('strong', pct(share));
    item.append(swatch, strong, element('em', label), element('small', format(level.students) + ' estudiantes · ' + format(level.schools) + ' sedes'));
    if (key === 'SIN RIESGO') item.className = 'main';
    legend.append(item);
  }
}

function setMapView(view) {
  const byRisk = view === 'sinriesgo';
  $('mapa').dataset.vista = byRisk ? 'riesgo' : 'entregas';
  $('vista-entregas').setAttribute('aria-pressed', String(!byRisk));
  $('vista-sinriesgo').setAttribute('aria-pressed', String(byRisk));
  $('leyenda-entregas').hidden = byRisk;
  $('leyenda-sinriesgo').hidden = !byRisk;
  $('leyenda-titulo').textContent = byRisk ? 'Estudiantes en sedes sin riesgo' : 'Filtros escolares entregados';
  document.querySelectorAll('#mapa path').forEach(path => {
    const title = path.querySelector('title');
    if (title) title.textContent = byRisk ? path.dataset.tituloRiesgo : path.dataset.tituloEntregas;
  });
}

function municipalityKey(name) {
  const key = name.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toUpperCase().replace(/[^A-Z0-9]+/g, ' ').trim();
  return ['CALIMA EL DARIEN', 'CALIMA DARIEN', 'EL DARIEN'].includes(key) ? 'CALIMA' : key;
}

function friendlyName(name) {
  return ({CALIMA: 'Calima – El Darién', ALCALA: 'Alcalá', BOLIVAR: 'Bolívar', GUACARI: 'Guacarí', TULUA: 'Tuluá',
    ANDALUCIA: 'Andalucía', EL_AGUILA: 'El Águila', LA_UNION: 'La Unión', RIOFRIO: 'Riofrío',
    ULLOA: 'Ulloa', VERSALLES: 'Versalles', YOTOCO: 'Yotoco'})[name.replaceAll(' ', '_')] ||
    name.toLowerCase().replace(/(^| )\p{L}/gu, initial => initial.toUpperCase());
}

function element(tag, text) {
  const node = document.createElement(tag);
  node.textContent = text;
  return node;
}

async function getJSON(url) {
  const response = await fetch(url);
  if (!response.ok) throw new Error(String(response.status));
  return response.json();
}

function setTerritory() {
  const town = select.value;
  $('territorio-nombre').textContent = town ? friendlyName(town) : 'Valle del Cauca';
  $('territorio-filtros').textContent = format(town ? data.escolaresPorMunicipio[town] : data.totales.escolares);
  $('territorio-f13').textContent = format(town ? data.actividadesPorMunicipio[town] : data.totales.f13);
  $('territorio-sinriesgo').textContent = town ? (data.sinRiesgo.porMunicipio[town] === undefined ? 'Fuera de la línea base' : pct(data.sinRiesgo.porMunicipio[town])) : pct(data.sinRiesgo.totalRatio);
  document.querySelectorAll('#mapa [data-choice]').forEach(path => path.toggleAttribute('data-selected', path.dataset.choice === town));
  $('fichas').replaceChildren();
  schoolOffset = 0;
  showSchools();
}

function showSchools() {
  const town = select.value;
  const schoolList = town ? data.sedes.filter(school => school.MUNICIPIO_NORM === town) : [];
  $('fichas-aviso').textContent = !town ? 'Para consultar fichas de sedes, selecciona un municipio en el mapa o en el detalle territorial.'
    : schoolList.length ? friendlyName(town) + ' · ' + format(schoolList.length) + ' sedes en la línea base IRCA.'
    : 'El municipio seleccionado queda fuera del conjunto de sedes de la línea base IRCA.';
  for (const school of schoolList.slice(schoolOffset, schoolOffset + 12)) {
    const article = document.createElement('article');
    const risk = school.NIVEL_RIESGO_IRCA.toLowerCase();
    const enrollment = school.ESTUDIANTES_ACTUAL === '' ? 'Matrícula sin dato' : format(school.ESTUDIANTES_ACTUAL) + ' estudiantes';
    article.append(element('h3', school.NOMBRE_SEDE_IRCA), element('p', 'Riesgo IRCA · ' + risk),
      element('p', enrollment + (school.ZONA_IRCA ? ' · ' + school.ZONA_IRCA.toLowerCase() : '')));
    $('fichas').append(article);
  }
  schoolOffset += 12;
  $('mas-fichas').hidden = schoolOffset >= schoolList.length;
}

function polygons(feature) {
  return feature.geometry.type === 'Polygon' ? [feature.geometry.coordinates] : feature.geometry.coordinates;
}

function setupDeliveryTables() {
  const deliveries = Object.entries(data.escolaresPorMunicipio)
    .filter(([, count]) => count > 0)
    .sort(([townA, countA], [townB, countB]) => countB - countA
      || friendlyName(townA).localeCompare(friendlyName(townB), 'es'));
  $('municipios-entregas').textContent = format(deliveries.length);
  $('municipios-entregas-acciones').textContent = format(deliveries.length);
  for (const [table, rows] of [
    [$('entregas-destacadas'), deliveries.slice(0, 5)],
    [$('entregas-completas'), deliveries]
  ]) {
    for (const [town, count] of rows) {
      const row = document.createElement('tr');
      const label = element('th', friendlyName(town));
      label.scope = 'row';
      row.append(label, element('td', format(count)));
      table.append(row);
    }
  }
}

function setupMap(features) {
  const all = features.flatMap(feature => polygons(feature).flat(2));
  const x = all.map(point => point[0]);
  const y = all.map(point => point[1]);
  const width = Math.max(...x) - Math.min(...x);
  const height = Math.max(...y) - Math.min(...y);
  const scale = Math.min(530 / width, 570 / height);
  const xStart = (570 - width * scale) / 2;
  const yStart = (610 - height * scale) / 2;
  const west = Math.min(...x);
  const north = Math.max(...y);
  for (const feature of features) {
    const key = municipalityKey(feature.properties.canonical);
    const hasData = data.municipios.includes(key);
    const deliveries = data.escolaresPorMunicipio[key] || 0;
    const band = [0, 5, 20, 100].filter(limit => deliveries > limit).length;
    const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    const geometry = polygons(feature).flatMap(polygon => polygon.map(ring => ring.map(([lon, lat], index) =>
      (index ? 'L' : 'M') + (xStart + (lon - west) * scale).toFixed(1) + ' ' + (yStart + (north - lat) * scale).toFixed(1)
    ).join(' ') + 'Z')).join(' ');
    path.setAttribute('d', geometry);
    path.setAttribute('fill-rule', 'evenodd');
    const title = document.createElementNS('http://www.w3.org/2000/svg', 'title');
    title.textContent = friendlyName(key) + ' · ' + format(deliveries) + ' filtros escolares';
    path.append(title);
    path.dataset.entregas = String(band);
    const ratio = data.sinRiesgo.porMunicipio[key];
    path.dataset.sr = ratio === undefined ? 'na' : String([0.8, 0.9, 0.95].filter(limit => ratio >= limit).length);
    path.dataset.tituloEntregas = title.textContent;
    path.dataset.tituloRiesgo = friendlyName(key) + ' · ' + (ratio === undefined ? 'fuera de la línea base' : pct(ratio) + ' de estudiantes sin riesgo');
    if (hasData) {
      path.dataset.choice = key;
      path.addEventListener('click', () => {
        select.value = key;
        $('detalle-municipio').open = true;
        setTerritory();
      });
    }
    $('mapa').append(path);
  }
}

function dateLabel(value) {
  return new Intl.DateTimeFormat('es-CO', {day:'numeric', month:'short', year:'numeric', timeZone:'UTC'})
    .format(new Date(value + 'T12:00:00Z'));
}

function photoFigure(photo) {
  const thumb = element('button', '');
  thumb.type = 'button';
  thumb.setAttribute('aria-label', 'Ampliar foto: ' + photo.alt);
  const image = element('img', '');
  image.src = photo.src;
  image.alt = photo.alt;
  image.loading = 'lazy';
  thumb.append(image);
  thumb.addEventListener('click', () => {
    const dialog = $('visor-foto');
    const large = element('img', '');
    large.src = photo.src;
    large.alt = photo.alt;
    dialog.querySelector('figure').replaceChildren(large, element('figcaption', photo.caption));
    dialog.showModal();
  });
  const figure = document.createElement('figure');
  figure.append(thumb, element('figcaption', photo.caption));
  return figure;
}

function showPhotos(photos, internal = false) {
  const validPath = internal ? /^\/revision-interna\/fotos\/FOTO-\d{3}\.jpg$/
    : /^assets\/[a-z0-9_-]+\.(jpg|jpeg|webp|png)$/i;
  const highlights = {
    '/revision-interna/fotos/FOTO-002.jpg': 'comunidades',
    '/revision-interna/fotos/FOTO-006.jpg': 'comunidades',
    '/revision-interna/fotos/FOTO-005.jpg': 'aprende',
    '/revision-interna/fotos/FOTO-007.jpg': 'aprende',
  };
  const chapters = {comunidades: $('fotos-comunidades'), aprende: $('fotos-aprende')};
  for (const photo of photos) {
    if (!validPath.test(photo.src) || !photo.alt || !photo.caption) continue;
    $('galeria').append(photoFigure(photo));
    const chapter = internal ? highlights[photo.src] : photo.chapter;
    if (Object.hasOwn(chapters, chapter)) {
      chapters[chapter].append(photoFigure(photo));
      chapters[chapter].hidden = false;
    }
  }
  const visible = $('galeria').childElementCount > 0;
  $('galeria-estado').hidden = visible;
  if (!visible) $('galeria-estado').textContent = 'El registro fotográfico está temporalmente indisponible.';
  $('galeria-interna').hidden = !internal || !visible;
}

function goToSlide(index) {
  currentSlide = Math.max(0, Math.min(sections.length - 1, index));
  $('paso').textContent = (currentSlide + 1) + ' de ' + sections.length;
  $('anterior').disabled = currentSlide === 0;
  $('siguiente').disabled = currentSlide === sections.length - 1;
  sections[currentSlide].scrollIntoView({block:'start'});
}

function exitPresentation() {
  presenting = false;
  document.body.classList.remove('presentation-active');
  $('controles-presentacion').hidden = true;
  if (ownFullscreen && document.fullscreenElement) document.exitFullscreen().catch(() => {});
  ownFullscreen = false;
  $('presentar').focus();
}

$('presentar').addEventListener('click', async () => {
  if (presenting) return;
  presenting = true;
  document.body.classList.add('presentation-active');
  $('controles-presentacion').hidden = false;
  if (!document.fullscreenElement && document.documentElement.requestFullscreen) {
    try {
      await document.documentElement.requestFullscreen();
      ownFullscreen = true;
    } catch {
      // La navegación de presentación también funciona dentro de la ventana.
    }
  }
  goToSlide(Math.max(0, sections.findIndex(section => '#' + section.id === location.hash)));
  $('siguiente').focus({preventScroll:true});
});
$('salir').addEventListener('click', exitPresentation);
$('anterior').addEventListener('click', () => goToSlide(currentSlide - 1));
$('siguiente').addEventListener('click', () => goToSlide(currentSlide + 1));
document.addEventListener('fullscreenchange', () => {
  if (ownFullscreen && !document.fullscreenElement && presenting) exitPresentation();
});
document.addEventListener('keydown', event => {
  if (!presenting || event.altKey || event.ctrlKey || event.metaKey || event.target.closest('select, dialog')) return;
  if (event.key === 'Escape') exitPresentation();
  if (event.key === 'ArrowRight' || event.key === 'ArrowLeft') {
    event.preventDefault();
    goToSlide(currentSlide + (event.key === 'ArrowRight' ? 1 : -1));
  }
});

select.addEventListener('change', setTerritory);
$('vista-entregas').addEventListener('click', () => setMapView('entregas'));
$('vista-sinriesgo').addEventListener('click', () => setMapView('sinriesgo'));
$('mas-fichas').addEventListener('click', showSchools);
async function init() {
  try {
    data = await getJSON(root + 'data/impacto_filtros_escolares/current/intervenciones.json');
    document.querySelectorAll('[data-metric]').forEach(node => {
      node.textContent = format(data.totales[node.dataset.metric]);
    });
    data.sinRiesgo = riskSummary(data.sedes);
    showRisk();
    $('fuera-buenaventura').textContent = format(data.totales.escolares - data.totales.escolaresBuenaventura);
    for (const town of [...data.municipios].sort((a, b) => friendlyName(a).localeCompare(friendlyName(b), 'es'))) {
      select.add(new Option(friendlyName(town), town));
    }
    select.disabled = false;
    $('fuentes').append(
      element('li', 'Entregas de filtros · ' + data.cortes.entregasAnios.join(', ') + '.'),
      element('li', 'Encuestas de seguimiento · ' + dateLabel(data.cortes.encuestasInicio) + ' a ' + dateLabel(data.cortes.encuestasFin) + '.'),
      element('li', 'Actividades F.13 · ' + dateLabel(data.cortes.f13Inicio) + ' a ' + dateLabel(data.cortes.f13Fin) + '.')
    );
    setTerritory();
    setupDeliveryTables();
    $('estado').hidden = true;
  } catch {
    $('estado').textContent = 'No se pudieron cargar los indicadores. Recarga la página para reintentar.';
    return;
  }
  try {
    const map = await getJSON('../respuesta_sanitaria_story/data/municipios_story.geojson');
    setupMap(map.features);
  } catch {
    $('mapa').replaceWith(element('p', 'Mapa temporalmente no disponible. Las entregas están disponibles en las tablas.'));
  }
  if (['127.0.0.1', 'localhost'].includes(location.hostname)) {
    try {
      const photos = await getJSON('/revision-interna/fotos.json');
      if (photos.length) {
        showPhotos(photos, true);
        return;
      }
    } catch {
      // La galería pública también puede revisarse desde un servidor estático.
    }
  }
  try {
    showPhotos(await getJSON('fotos_autorizadas.json'));
  } catch {
    $('galeria-estado').textContent = 'La galería está temporalmente indisponible.';
  }
}
init();
