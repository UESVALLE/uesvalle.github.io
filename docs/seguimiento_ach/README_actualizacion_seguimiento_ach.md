# Flujo oficial de actualización - Tablero Seguimiento ACH

## 1. Estructura del módulo

```text
UESVALLE/
├── data/
│   └── seguimiento_ach/
│       ├── raw/
│       │   └── Seguimiento_ACH_2026.xlsx
│       ├── current/
│       │   ├── seguimiento_actividades_ACH_detalle.csv
│       │   ├── seguimiento_actividades_ACH_resumen_municipal.csv
│       │   ├── seguimiento_actividades_ACH_resumen_responsable.csv
│       │   ├── seguimiento_actividades_ACH_resumen_actividad.csv
│       │   ├── seguimiento_actividades_ACH_resumen_aro.csv
│       │   ├── seguimiento_actividades_ACH_resumen_tipo.csv
│       │   └── seguimiento_actividades_ACH_kpis_historicos.csv
│       └── historical/
├── dashboards/
│   └── seguimiento_ach/
│       └── seguimiento_ach.html
└── scripts/
    └── seguimiento_ach/
        ├── normalizar_seguimiento_ach.py
        └── actualizar_seguimiento_ach.bat
```

## 2. Archivo fuente principal

El archivo fuente oficial queda en:

```text
data/seguimiento_ach/raw/Seguimiento_ACH_2026.xlsx
```

Cuando se reciba un nuevo corte, se reemplaza ese archivo conservando el mismo nombre. El script detecta el periodo desde la columna `PERIODO` del Excel.

## 3. Ejecución manual desde PowerShell

```powershell
cd "G:\Mi unidad\8.UES\PAGINA INDICADORES\UESVALLE"
& "C:\Users\Javier\miniconda3\envs\analitica\python.exe" "scripts\seguimiento_ach\normalizar_seguimiento_ach.py"
```

También se puede ejecutar:

```powershell
scripts\seguimiento_ach\actualizar_seguimiento_ach.bat
```

## 4. Prueba local del tablero

```powershell
cd "G:\Mi unidad\8.UES\PAGINA INDICADORES\UESVALLE"
python -m http.server 8000
```

Abrir en el navegador:

```text
http://localhost:8000/dashboards/seguimiento_ach/seguimiento_ach.html
```

## 5. Publicación en GitHub Pages

```powershell
git status --short
git add data/seguimiento_ach/current data/seguimiento_ach/raw scripts/seguimiento_ach docs/seguimiento_ach
git commit -m "Actualiza fuente y flujo del tablero seguimiento ACH"
git push uesvalle main
```

## 6. Notas operativas

- El tablero HTML ya está configurado para leer los CSV desde `../../data/seguimiento_ach/current/`.
- No se debe editar el HTML para cada actualización de datos.
- La carpeta `historical/` guarda respaldos automáticos de fuentes y salidas anteriores.
- La carpeta `raw/` conserva únicamente la fuente principal vigente.
