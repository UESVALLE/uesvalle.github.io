@echo off
chcp 65001 > nul
setlocal EnableExtensions EnableDelayedExpansion

title UESVALLE - Actualizacion integral seguimiento muestras registradas

set "PORTAL_ROOT=G:\Mi unidad\8.UES\PAGINA INDICADORES\UESVALLE"
set "SCRIPT_DIR=%PORTAL_ROOT%\scripts\resultados_agua\04_seguimiento_muestras"

set "SCRIPT_SEGUIMIENTO=%SCRIPT_DIR%\Seguimiento_Muestras_Registradas_Agua.py"
set "SCRIPT_ENRIQUECER=%SCRIPT_DIR%\enriquecer_seguimiento_muestras_con_fichas.py"

cls
echo.
echo ============================================================
echo   UESVALLE - ACTUALIZACION INTEGRAL SEGUIMIENTO MUESTRAS
echo ============================================================
echo.
echo Este proceso realiza:
echo.
echo   1. Consulta semanal de muestras registradas.
echo      - NO descarga PDF.
echo      - NO abre fichas.
echo      - Lee el listado inicial de muestras registradas.
echo.
echo   2. Enriquecimiento con fichas descargadas.
echo      - Cruza CODIGO_MUESTRA con Codigo Interno.
echo      - Agrega municipio, prestador y datos de punto de muestreo.
echo.
echo Salidas:
echo   data\resultados_agua\seguimiento_muestras\current
echo.
echo ------------------------------------------------------------
echo.

if not exist "%SCRIPT_SEGUIMIENTO%" (
    echo [ERROR] No se encontro el script de seguimiento:
    echo   %SCRIPT_SEGUIMIENTO%
    echo.
    pause
    exit /b 1
)

if not exist "%SCRIPT_ENRIQUECER%" (
    echo [ERROR] No se encontro el script de enriquecimiento:
    echo   %SCRIPT_ENRIQUECER%
    echo.
    pause
    exit /b 1
)

set "PYTHON_EXE="
if exist "C:\Users\Javier\miniconda3\envs\analitica\python.exe" (
    set "PYTHON_EXE=C:\Users\Javier\miniconda3\envs\analitica\python.exe"
) else if exist "C:\Users\Javier\anaconda3\envs\analitica\python.exe" (
    set "PYTHON_EXE=C:\Users\Javier\anaconda3\envs\analitica\python.exe"
) else (
    set "PYTHON_EXE=python"
)

echo Python seleccionado:
echo   %PYTHON_EXE%
echo.

echo Verificando dependencias...
"%PYTHON_EXE%" -c "import selenium, pandas, openpyxl, webdriver_manager" > nul 2>&1
if errorlevel 1 (
    echo.
    echo [AVISO] Faltan dependencias. Se intentara instalarlas.
    "%PYTHON_EXE%" -m pip install selenium webdriver-manager pandas openpyxl
)

echo.
echo ============================================================
echo   PASO 1 DE 2 - CONSULTAR LISTADO DE MUESTRAS REGISTRADAS
echo ============================================================
echo.
echo Recomendado:
echo   ARO: 0
echo   Rango dias: 15
echo   Max paginas: 3
echo   Registros pagina: 100
echo   Headless: S
echo.

cd /d "%PORTAL_ROOT%"
"%PYTHON_EXE%" "%SCRIPT_SEGUIMIENTO%"

if errorlevel 1 (
    echo.
    echo [ERROR] Fallo el paso 1: seguimiento de muestras.
    echo No se ejecutara el enriquecimiento.
    echo.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo   PASO 2 DE 2 - ENRIQUECER CON FICHAS DESCARGADAS
echo ============================================================
echo.

"%PYTHON_EXE%" "%SCRIPT_ENRIQUECER%"

if errorlevel 1 (
    echo.
    echo [ERROR] Fallo el paso 2: enriquecimiento con fichas.
    echo Revisa el log mostrado en pantalla.
    echo.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo        ACTUALIZACION INTEGRAL FINALIZADA CORRECTAMENTE
echo ============================================================
echo.
echo Revisa las salidas en:
echo   %PORTAL_ROOT%\data\resultados_agua\seguimiento_muestras\current
echo.
echo Archivos principales:
echo   seguimiento_muestras_registradas_agua.csv
echo   seguimiento_muestras_registradas_agua.xlsx
echo   metadata_seguimiento_muestras.json
echo   resumen_cruce_seguimiento_fichas.json
echo.
pause
endlocal
