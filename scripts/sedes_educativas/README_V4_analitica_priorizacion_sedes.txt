# V4 - Tablero Sedes Educativas UESVALLE

## Objetivo
Agregar campos analíticos para mejorar la priorización territorial y operativa del tablero.

## Nuevos campos en sedes_educativas_irca_consolidado.csv
- GRUPO_SEGUIMIENTO
- RIESGO_IRCA_AGRUPADO
- BRECHAS_INFORMACION
- TIENE_BRECHA_INFORMACION
- CALIDAD_DATO_SEDE
- INDICE_PRIORIDAD_SANITARIA_ESCOLAR
- NIVEL_PRIORIDAD_ANALITICA
- ACCION_SUGERIDA

## Nuevo resumen
data/sedes_educativas/current/resumen_grupo_seguimiento.csv

## Grupos de seguimiento
- RUTINARIO: Sin riesgo y bajo
- PREVENTIVO: Medio
- PRIORITARIO: Alto e inviable sanitariamente
- BRECHA INFORMACION: Sin dato o información incompleta

## Ejecución
Copiar:
normalizar_sedes_educativas_V4_analitica_priorizacion.py
en:
G:\Mi unidad\8.UES\PAGINA INDICADORES\UESVALLE\scripts\sedes_educativas\

Copiar:
actualizar_sedes_educativas_V4_analitica_priorizacion.bat
en la misma carpeta.

Ejecutar el BAT.
