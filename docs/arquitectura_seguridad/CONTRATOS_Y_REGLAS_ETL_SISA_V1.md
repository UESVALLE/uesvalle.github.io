# Contratos de datos y ETL — Integración SISA y otras fuentes (V1)

**Estado:** extracción documental de cabeceras de `main`, sin leer registros ni modificar normalizadores. **No es contrato definitivo validado con los dueños de datos.**

## A. SISA — Programación y ejecución MPR

**Programación (fuente institucional distinta del SISA):** `data/mpr/current/programados_mpr.csv`
```text
ID, ARO, MUNICIPIO, LOCALIDAD, CODIGO ANTERIOR, FUNCIONARIO, PERSONA_PRESTADORA
```

**Ejecución de actividades:** `data/mpr/current/actividades_mpr_ejecutadas.csv`
```text
ACTIVIDAD, CODIGO_LLAVE, CODIGO_SISA_ORIGINAL, CODIGO_PROGRAMADO_CRUCE,
TIPO_CRUCE_MPR, PUNTAJE_CRUCE_MPR, MUNICIPIO, NOMBRE_SISTEMA,
PERSONA_PRESTADORA, NOMBRE_ARO, FUNCIONARIO, FECHA_ACTIVIDAD,
ACTA, CONSECUTIVO VISITA, ESTADO, PROGRAMADO, FUNCIONARIO_PROGRAMADO,
COINCIDE_FUNCIONARIO_PROGRAMADO
```
Campos seleccionados de la cabecera verificada; hay 24 en total. Codificación SISA por MPR: **1.3 / 1.4 / 1.5**.

**Salida derivada de cruce:** `data/mpr/current/seguimiento_mpr_sistemas.csv`
- `ejecuto_13`, `fecha_13`, `funcionario_13`, `acta_13` (1.3).
- `ejecuto_14`, `fecha_14`, `funcionario_14`, `acta_14` (1.4).
- `ejecuto_15`, `fecha_15`, `funcionario_15`, `acta_15` (1.5).
- `DIAS_13_A_14`, `ESTADO_MPR`, `PROGRAMADO`, `ARO_PROGRAMADO`, `CODIGO_LLAVE`.

**Evidencia de proceso:** `data/mpr/current/metadata_mpr.json` indica normalizador **V2.7**, generación **2026-06-25**, entradas `censo_visitasMPR.xlsx` y `Programados.xlsx`, 3.204 registros de censo leídos, 95 filtrados MPR, 74 programados, 77 cruces por código, 16 por texto y 1 sin cruce. Son conteos **históricos del corte**, no estado actual del SISA; no usarlos como totales de producción nuevos.

**Transformación propuesta:**
1. Ingresar lote de programación a `ues_operacion.programacion_mpr`.
2. Ingresar **eventos SISA** a `ues_operacion.actividad_sisa` con fuente y lote.
3. Registrar `codigo_llave` / alias y `tipo_cruce`, `puntaje_cruce` separando confirmado de sugerido.
4. Generar `cruce_mpr` (programado ↔ eventos), conservar historia de cambios y ausencia de cruce.
5. Comparar totales por ARO/municipio/funcionario/código/etapa con `seguimiento_mpr_sistemas.csv`.

## B. Seguimiento ACH — RASEM y programación

`data/seguimiento_ach/current/seguimiento_actividades_ACH_detalle.csv`, cabecera observada:
```text
NOMBRE_ORIGINAL, RESPONSABLE, ROL_EQUIPO, MUNICIPIO_ORIGINAL,
MUNICIPIO_NORMALIZADO, CODIGO_ACTIVIDAD, ARO, PERIODO_ORIGINAL,
PERIODO_NORMALIZADO, ANIO, MES_INICIO, MES_FIN, TIPO,
PROGRAMADO, EJECUTADO_RASEM, PENDIENTE_CALCULADO,
CUMPLIMIENTO_CALCULADO, FUENTE_ARCHIVO, FECHA_PROCESAMIENTO
```
Campos seleccionados de 30 totales. **No registrar `EJECUTADO_RASEM` como si fuera un evento individual de SISA**: puede ser agregado y requiere linaje/conciliación propio.

**Contrato:** observación por período/actividad/municipio/ARO/responsable/fuente; `programado` y `ejecutado` calculados con definición explícita de corte.

## C. IRCAS — actividad 1.2 y muestreo 1.7

`data/ircas/current/sisa_visitas_ach.csv`:
```text
CODIGO_ANTERIOR, MUNICIPIO, PERSONA_PRESTADORA, NOMBRE_SISTEMA,
ARO, FECHA_VISITA_1_2, CONCEPTO_1_2, FUNCIONARIO_1_2, IRCA_1_2,
OBSERVACION_1_2, FECHA_MUESTREO_1_7, IRCA_1_7,
CODIGO_LABORATORIO_1_7, RESULTADO_1_7, ESTADO_MUESTRA_1_7,
SOPORTE_SISA, TOTAL_VISITAS_1_2, TOTAL_MUESTREOS_1_7
```
Campos seleccionados de 23 totales.

**Metadatos:** `metadata_sisa_visitas_ach.json`, fecha de generación **2026-07-06**, 3.360 registros de Excel, 524 códigos de sistema de salida, 393 códigos con visita 1.2 y 477 con muestreo 1.7. Es un **agregado por sistema**, no tabla maestra de eventos.

**Contrato:** almacenar eventos origen por separado; generar resumen por `sistema_id` y fecha corte. Vincular resultados analíticos por identificador de muestra validado.

## D. Maestro de sistemas / IRCAS

`data/ircas/current/IRCAS.csv` utiliza **punto y coma** y contiene `CODIGO_ANTERIOR`, `CODIGO_SISTEMA`, `CODIGO IVC2`, `CODIGO MUESTREO`, `ID_SSPD`, `Latitud_X`, `Longitud_Y`, `MUNICIPIO`, `ARO`, `Persona Prestadora`, `SUSCRIPTORES`, `POBLACION` y series `IRCA_2020` ... `IRCA_2026`.

**Normalización:** despivotar históricos por año para series de indicadores (con fecha y fuente), no añadir una columna nueva por año a la tabla maestra. Verificar semántica de `Latitud_X` / `Longitud_Y` y SRID antes de crear geometría.

## E. Muestras, laboratorio y SIVICAP

`data/muestras_irca/current/coordenadas_sistemas.csv` incluye `CODIGO_SISTEMA, MUNICIPIO, SISTEMA_DISTRIBUCION, ARO, LATITUD, LONGITUD, MUESTRAS, ANIOS, IRCA_PROMEDIO` y clasificación/riesgo. Es **salida agregada**; no usar promedio como fila de muestra.

`data/muestras_irca/current/catalogo_parametros_normativo.csv` incluye `PARAMETRO, GRUPO_PARAMETRO, METODO, VALOR_MAXIMO_PERMISIBLE, UNIDAD, NORMA_REFERENCIA`: diccionario de referencia versionado.

`data/resultados_agua/seguimiento_muestras/current/seguimiento_muestras_registradas_agua.csv` contiene `CODIGO_MUESTRA, FECHA_ENVIO, FECHA_RECEPCION, FECHA_RESULTADOS, ESTADO, FECHA_TOMA_MUESTRA_DETALLE, NUMERO_ACTA, PUNTO_MUESTREO, PH, CLORO_RESIDUAL, TURBIEDAD, ANALISIS_SOLICITADO, NOMBRE_ACUEDUCTO_DETALLE` y otros campos: verificar el origen específico de cada valor antes de asignar fuente.

**Contratos separados:**
- `muestra`: identificador externo de muestra, sistema, punto, fecha y laboratorio, situación de muestreo.
- `resultado_parametro`: resultado de análisis individual, unidad, método, valoración, fecha y fuente.
- `indicador_irca`: resultado oficial del indicador, período, autoridad, sistema/punto y algoritmo/versión.
- `documento_resultado`: metadatos y objeto privado de PDF; nunca usar enlace Drive como credencial de acceso.

## F. Identidad y controles de normalización

| Campo origen | Interpretación segura | Regla |
|---|---|---|
| `CODIGO_ANTERIOR`, `CODIGO_SISTEMA` | Alias posiblemente del mismo sistema | Resolver contra catálogo maestro, conservar valores |
| `CODIGO IVC2`, `CODIGO MUESTREO` | Claves de otros subsistemas | No equiparar automáticamente al código del sistema |
| `CODIGO_LLAVE` | Clave de cruce construida por normalizador | No usar como ID universal sin validación |
| `CONSECUTIVO VISITA`, `ACTA` | Evidencia/documento de evento | No suponer unicidad global |
| `FECHA_ACTIVIDAD` | Fecha de evento reportada | Separar de fecha de extracción, cargue y procesamiento |
| `ARO`, `MUNICIPIO` | Ámbito territorial | Verificar vigencia y código DIVIPOLA, mantener nombre original |
| `FUNCIONARIO`, `RESPONSABLE` | Personas de origen | Cargar bajo autorización específica; no vincular automáticamente con `auth.users` |
| `IRCA_1_7`, `IRCA_2025` | Valores calculados/referenciados en salidas | Conservar origen/fecha/calidad, no sobrescribir resultados oficiales |

## Reglas de aceptación de ETL

- **Formato:** separador, BOM, codificación, nombres y esquema por fuente; rechazar si se rompe contrato.
- **Idempotencia:** mismo archivo y misma versión de normalizador no genera duplicados.
- **Corrección:** si SISA cambia un registro ya cargado, conservar revisión y sustituir estado vigente con bitácora, no eliminar la huella.
- **Conciliación:** contar filas antes/después, fuera de rango, sin código, cruces por código/texto, excepciones, fechas imposibles, duplicados, programaciones sin ejecución y eventos sin programación.
- **Carga atómica:** no actualizar el producto aprobado si existen errores críticos.
- **Seguridad:** ficheros originales y evidencias en almacenamiento privado, credenciales sólo servidor, trazas sin PII/secretos.
- **Reproducibilidad:** registrar SHA-256, período de corte y versión de ETL.

## Primer piloto verificable

MPR con muestras sintéticas que cubran: mismo evento repetido, sistema sin coincidencia, dos eventos distintos del mismo día, evento fuera de programación, etapas 1.3/1.4/1.5 y diferencia de funcionario. La comparación final con los archivos de 25/06/2026 requiere autorización para tratar registros de origen.
