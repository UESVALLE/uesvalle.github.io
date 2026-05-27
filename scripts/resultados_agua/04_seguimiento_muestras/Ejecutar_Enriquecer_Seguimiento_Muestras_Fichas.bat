@echo off
chcp 65001 > nul
setlocal EnableExtensions EnableDelayedExpansion

title UESVALLE - Enriquecer seguimiento muestras con fichas

set "PORTAL_ROOT=G:\Mi unidad\8.UES\PAGINA INDICADORES\UESVALLE"
set "SCRIPT_DIR=%PORTAL_ROOT%\scripts\resultados_agua\04_seguimiento_muestras"
set "SCRIPT=enriquecer_seguimiento_muestras_con_fichas.py"
set "SCRIPT_PATH=%SCRIPT_DIR%\%SCRIPT%"

cls
echo.
echo ============================================================
echo   UESVALLE - ENRIQUECER SEGUIMIENTO MUESTRAS CON FICHAS
echo ============================================================
echo.
echo Este proceso:
echo   - Lee data\resultados_agua\seguimiento_muestras\current.
echo   - Lee Control_Descargas\Lote_*\muestras_fichas_CONSOLIDADO_lote_*.csv.
echo   - Cruza por CODIGO_MUESTRA / Codigo Interno.
echo   - Agrega municipio, prestador y campos de ficha al seguimiento.
echo.
echo Script:
echo   %SCRIPT_PATH%
echo.

if not exist "%SCRIPT_PATH%" (
    echo [ERROR] No se encontro el script:
    echo   %SCRIPT_PATH%
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
"%PYTHON_EXE%" -c "import pandas, openpyxl" > nul 2>&1
if errorlevel 1 (
    echo [AVISO] Faltan dependencias. Se intentara instalarlas.
    "%PYTHON_EXE%" -m pip install pandas openpyxl
)

cd /d "%PORTAL_ROOT%"
"%PYTHON_EXE%" "%SCRIPT_PATH%"

echo.
echo ============================================================
echo          PROCESO FINALIZADO
echo ============================================================
pause
endlocal
