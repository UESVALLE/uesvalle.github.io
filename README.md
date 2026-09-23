# Portal de Tableros UESVALLE

Repositorio institucional de la Unidad Ejecutora de Saneamiento del Valle del Cauca para la publicación de tableros HTML, datos y documentación técnica mediante GitHub Pages.

Portal: https://uesvalle.github.io/

## Organización del portal (V2.5)

La página principal presenta el **mapa de procesos** de la entidad como una rueda interactiva: los cuatro procesos misionales en el centro, con los colores institucionales, y un anillo exterior con los eventos y los tableros transversales. Al seleccionar una opción se muestran sus tableros en el panel lateral, que también tiene un buscador por nombre. En computador la página ocupa una sola pantalla: columna institucional a la izquierda, rueda al centro y panel a la derecha.

### Procesos y eventos

El portal se organiza según los **procesos misionales** de la entidad (Plan Operativo Anual 2026, F-PI-04) y un bloque de **eventos** con los tableros creados para situaciones específicas:

- Agua para Consumo Humano y Saneamiento Básico
- Alimentos y Medicamentos
- Establecimientos de Interés Sanitario (EIS)
- Zoonosis y Enfermedades de Transmisión Vectorial
- Eventos: Sismo del 10 de agosto de 2026 · Fenómeno de El Niño 2026

Las tarjetas se generan desde `data/portal/catalogo_tableros.json`. Para agregar o actualizar un tablero se edita ese archivo; no es necesario modificar `index.html`.

Campos de cada tablero: `titulo`, `descripcion`, `url`, `tipo` (Tablero, Herramienta, Informe, Historia), `proceso` (ach, aym, eis, zoo o transversal), `evento` (id del evento o null), `version`, `publicado` (AAAA-MM-DD), `requiere_clave`, `estado` (publicado o proximamente) y `enlaces` adicionales.

El portal no tiene clave de acceso. Los tableros que lo requieren la solicitan al abrirse.

## Estructura

- `index.html`: portal principal.
- `assets/portal/`: estilos, script y logos del portal.
- `data/portal/catalogo_tableros.json`: catálogo de tableros.
- `dashboards/`: tableros HTML por módulo.
- `data/`: datos publicados por módulo.
- `docs/`: documentación técnica.
