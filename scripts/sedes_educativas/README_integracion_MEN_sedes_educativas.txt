# Integración MEN - Tablero Sedes Educativas UESVALLE

## Archivos fuente requeridos en data/sedes_educativas/raw

- Escuelas_IRCAS.xlsx
- SedesUESVALLE.xlsx
- maestro_acueductos_uesvalle_2026_actualizado.csv
- MEN_SEDES_EDUCATIVAS_PREESCOLAR_BÁSICA_Y_MEDIA_20260605.csv

## Regla de matrícula final

1. Si Escuelas_IRCAS tiene Número de Estudiantes_Actual > 0:
   - Usa Escuelas_IRCAS.

2. Si Escuelas_IRCAS está vacío o cero y SedesUESVALLE tiene Total_general_INS > 0:
   - Usa SedesUESVALLE.

3. Si no hay dato en SedesUESVALLE y MEN tiene matrícula con coincidencia fuerte:
   - Usa MEN como referencia histórica y marca validación.

4. Si ninguna fuente tiene dato:
   - Mantiene 0 y marca SIN_DATO_MATRICULA.

## Regla de coordenada final

1. Si SedesUESVALLE tiene coordenada válida:
   - Usa SedesUESVALLE.

2. Si no tiene coordenada válida y MEN tiene coordenada válida:
   - Usa MEN y marca COMPLEMENTADA_CON_MEN.

3. Si ninguna tiene coordenada válida:
   - Marca SIN_COORDENADA.

## Nuevas salidas

- validacion_matricula_fuentes.csv
- validacion_men_sedes.csv

El CSV principal sedes_educativas_irca_consolidado.csv mantiene los campos ESTUDIANTES_ACTUAL, LATITUD y LONGITUD para que el HTML funcione sin cambios mayores.
