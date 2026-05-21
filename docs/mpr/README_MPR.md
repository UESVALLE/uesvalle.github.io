# Tablero Seguimiento Mapas de Riesgo MPR - UESVALLE

## Ubicación recomendada dentro del repositorio

Copiar estas carpetas en:

`G:\Mi unidad\8.UES\PAGINA INDICADORES\UESVALLE`

Estructura:

```text
UESVALLE/
├─ dashboards/
│  └─ mpr/
│     └─ seguimiento_mpr.html
├─ data/
│  └─ mpr/
│     ├─ raw/
│     │  ├─ Programados.csv
│     │  ├─ 1.3_VisitasMPR.csv
│     │  ├─ 1.4_MuestreoMPR.csv
│     │  ├─ 1.5_ResolucionesMPR.csv   # opcional cuando esté disponible
│     │  └─ Codigos_poa.csv
│     ├─ current/
│     └─ historical/
├─ docs/
│  └─ mpr/
│     └─ README_MPR.md
└─ scripts/
   ├─ normalizar_mpr.py
   └─ normalizar_mpr.bat
```

## Flujo de trabajo

1. Reemplazar los archivos fuente en `data/mpr/raw/`.
2. Ejecutar:

```bat
scripts\normalizar_mpr.bat
```

O desde PowerShell:

```powershell
cd "G:\Mi unidad\8.UES\PAGINA INDICADORES\UESVALLE"
C:\Users\Javier\miniconda3\envs\analitica\python.exe scripts\normalizar_mpr.py
```

3. Revisar salidas en `data/mpr/current/`.
4. Abrir el tablero local usando servidor local, por ejemplo:

```powershell
cd "G:\Mi unidad\8.UES\PAGINA INDICADORES\UESVALLE"
python -m http.server 8000
```

Luego abrir:

`http://localhost:8000/dashboards/mpr/seguimiento_mpr.html`

## Archivos generados

- `seguimiento_mpr_sistemas.csv`: tabla maestra por sistema programado.
- `actividades_mpr_ejecutadas.csv`: tabla larga con actividades ejecutadas.
- `resumen_mpr_aro.csv`: resumen por ARO.
- `resumen_mpr_municipio.csv`: resumen por ARO y municipio.
- `alertas_mpr.csv`: pendientes, inconsistencias, duplicados y ejecutados no programados.
- `catalogo_codigos_poa_mpr.csv`: catálogo POA de actividades MPR.
- `metadata_mpr.json`: trazabilidad de generación.

## Lógica de estados

- `SIN EJECUCIÓN`: sistema programado sin actividades ejecutadas.
- `PENDIENTE 1.4 MUESTREO`: tiene visita 1.3 pero no muestra 1.4.
- `PENDIENTE 1.5 RESOLUCIÓN`: tiene visita 1.3 y muestra 1.4, pero no resolución 1.5.
- `COMPLETO 1.3 + 1.4 + 1.5`: ciclo completo.
- `ALERTA`: actividad posterior sin evidencia de actividad previa en los archivos cargados.

## Nota sobre 1.5

Cuando exista el archivo de la actividad 1.5, debe guardarse como:

`data/mpr/raw/1.5_ResolucionesMPR.csv`

El script lo detectará automáticamente.
