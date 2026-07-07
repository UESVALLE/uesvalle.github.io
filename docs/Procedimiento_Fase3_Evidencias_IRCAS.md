# Procedimiento Fase 3 - Evidencias IRCAS

## Objetivo
Consolidar fichas de inspección, actas de laboratorio, fotografías y hallazgos técnicos por acueducto crítico para generar una ficha ejecutiva de soporte a la toma de decisiones.

## Flujo propuesto
1. Mantener el tablero IRCAS como fuente de riesgo y priorización.
2. Mantener SISA como fuente operativa de visita y muestreo para la Fase 2.
3. Crear un maestro de evidencias por sistema en `data/ircas/current/evidencias_sistemas.csv`.
4. Guardar los soportes documentales y fotográficos en `docs/ircas/evidencias/<sistema>/`.
5. Cruzar el maestro contra IRCAS/SISA mediante `CODIGO_ANTERIOR`.
6. Mostrar en la Fase 3 una ficha ejecutiva por sistema crítico con diagnóstico, evidencias y recomendación gerencial.

## Campos mínimos del maestro
- CODIGO_ANTERIOR
- MUNICIPIO
- SISTEMA
- PERSONA_PRESTADORA
- FECHA_INSPECCION
- POBLACION
- USUARIOS
- IRCA_REFERENCIA
- NIVEL_RIESGO
- INTERVENCION_PRINCIPAL
- INTERVENCIONES_COMPLEMENTARIAS
- HALLAZGOS_CLAVE
- DIAGNOSTICO_EJECUTIVO
- RECOMENDACION_GERENCIAL
- RUTA_FICHA
- RUTA_LAB_1
- RUTA_LAB_2
- FOTO_1
- FOTO_2
- FOTO_3

## Recomendación para automatización posterior
Para automatizar todos los acueductos, se debe crear un script que lea una carpeta por sistema, extraiga texto de las fichas DOCX/PDF, identifique campos estándar y alimente el maestro. El piloto El Chilcal deja definida la estructura de salida antes de automatizar la extracción masiva.
