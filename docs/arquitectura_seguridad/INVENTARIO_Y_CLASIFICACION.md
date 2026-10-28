# Inventario y clasificación del dato

**Corte técnico:** árbol de `main` leído el 28/10/2026. Inventario de rutas disponible en [INVENTARIO_TECNICO_2026-10-28.csv](INVENTARIO_TECNICO_2026-10-28.csv); su contenido es un listado de nombres/rutas/tamaños, **no una evaluación completa de cada registro**.

## Magnitud y alcance

- **704 archivos** en el repositorio y **561 archivos** en `data/`.
- **19 módulos** dentro de `data/`; código, documentación y `archive/` también entran en el perímetro.
- Formatos en el árbol: CSV 125, JSON 45, GeoJSON 18, HTML 28, imágenes, videos, XLSX, DOCX y otros. Estas cantidades son fotografías del inventario, no indicadores de calidad ni de confidencialidad.

## Matriz inicial de revisión

| Módulo (`data/<módulo>`) | Archivos | Prioridad preliminar | Verificación principal |
|---|---:|---|---|
| inspeccion_sedes | 87 | Crítica | Fotografías, videos, datos de inspección, metadatos |
| vigilancia_sanitaria | 118 | Crítica | Establecimientos, coordenadas, hallazgos y evidencia |
| edan | 20 | Alta | Afectaciones, población y reportes de emergencia |
| alojamientos_temporales | 7 | Alta | Datos de albergues y situación operativa |
| zoonosis | 15 | Alta | Eventos/seguimiento, riesgo de identificación |
| seguimiento_ach | 10 | Alta | Responsables, avance individual y actividad |
| mpr | 17 | Alta | Funcionarios, visitas, priorizaciones y resultados |
| estado_acueductos | 113 | Alta | Evidencia e información de infraestructura y gestión |
| ircas | 10 | Alta | Sistemas, visitas, resultados y soportes |
| muestras_irca | 18 | Alta | Detalle de muestras, coordenadas, parámetros |
| resultados_agua | 15 | Alta | Índices de archivos, vínculos a PDF/Drive |
| sedes_educativas | 12 | Alta | Sedes, dirección, teléfonos, estudiantes, calidad del agua |
| filtros | 6 | Media-alta | Variables de encuestas, hogares/beneficiarios si existen |
| piscinas | 4 | Media-alta | Datos de establecimientos |
| empresas_plaguicidas | 5 | Media-alta | Empresas, ubicaciones y revisión de tratamiento |
| cementerios | 65 | Media-alta | Fichas, imágenes y registros sanitarios |
| fenomeno_nino | 36 | Media-alta | Capas de acueductos y datos geográficos detallados |
| dosificacion_cloro | 2 | Revisar | Comprobar si existen insumos fuera de `data/` |
| portal | 1 | Revisar | Catálogo con URLs, estados y marcas de clave |

**Advertencia:** prioridad significa orden para revisar, no clasificación legal confirmada. El contenido de los archivos puede ser público, interno o restringido según autorización, finalidad y contexto. No se han abierto todos los archivos para inspeccionar datos personales.

## Campos obligatorios de la matriz definitiva

`ruta, modulo, tipo, tamano_bytes, fuente, responsable_dato, responsable_tecnico, fecha_corte, nivel_acceso, contiene_datos_personales, contiene_evidencias, retencion, consumidores, destino_autorizado, publicacion_aprobada_por, enlace_evidencia_revision, estado, observaciones`.

En la versión de inventario automático se incluyen sólo atributos técnicos verificables; los campos de evaluación se dejan para diligenciar con el responsable de cada proceso. Niveles propuestos:
- **PÚBLICO APROBADO**: mínimo necesario, validado, con autorización de difusión.
- **INTERNO**: usuarios institucionales autorizados.
- **RESTRINGIDO**: acceso caso por caso, roles y finalidad, evidencias o detalles sensibles.
- **POR CLASIFICAR**: no publicar y no migrar a zona pública.

## Proceso de clasificación

1. Conciliar archivos en `data/`, `archive/`, assets y contenido incrustado en HTML/JS con los consumidores reales.
2. Identificar procedencia, base de tratamiento, responsable, periodicidad y retención.
3. Inspeccionar columnas y una muestra representativa **en un entorno restringido**; registrar hallazgos sin replicar valores personales.
4. Definir publicar/migrar/archivar de forma segura; tratar permisos de Drive y objetos multimedia por separado.
5. Aprobar cambios con el dueño del dato y conservar evidencia mínima de la decisión.
6. Repetir inventario tras cada ola de migración.

**Pendiente:** validación documental, administrativa y jurídica de datos personales y acceso. Referencia de seguimiento: [SEC-02](https://github.com/UESVALLE/uesvalle.github.io/issues/3).
