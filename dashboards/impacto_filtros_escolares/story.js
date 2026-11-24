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

function showPhotos(photos, internal = false) {
  for (const photo of photos) {
    const validPath = internal ? /^\/revision-interna\/fotos\/FOTO-\d{3}\.jpg$/
      : /^assets\/[a-z0-9_-]+\.(jpg|jpeg|webp|png)$/i;
    if (!validPath.test(photo.src) || !photo.alt || !photo.caption) continue;
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
      const figure = dialog.querySelector('figure');
      const large = element('img', '');
      large.src = photo.src;
      large.alt = photo.alt;
      const caption = element('figcaption', photo.caption);
      figure.replaceChildren(large, caption);
      dialog.showModal();
    });
    const figure = document.createElement('figure');
    figure.append(thumb, element('figcaption', photo.caption));
    $('galeria').append(figure);
  }
  const visible = $('galeria').childElementCount > 0;
  $('galeria-estado').hidden = visible;
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
$('mas-fichas').addEventListener('click', showSchools);
async function init() {
  try {
    data = await getJSON(root + 'data/impacto_filtros_escolares/current/intervenciones.json');
    document.querySelectorAll('[data-metric]').forEach(node => {
      node.textContent = format(data.totales[node.dataset.metric]);
    });
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
