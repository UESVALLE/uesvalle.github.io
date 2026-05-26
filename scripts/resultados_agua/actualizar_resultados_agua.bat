@echo off
chcp 65001 > nul
setlocal EnableExtensions EnableDelayedExpansion

title UESVALLE - Actualizar índice resultados agua

REM ============================================================
REM  ACTUALIZAR ÍNDICE RESULTADOS AGUA - UESVALLE
REM  Ejecuta:
REM    generar_indice_resultados_agua.py
REM ============================================================

set "PORTAL_ROOT=G:\Mi unidad\8.UES\PAGINA INDICADORES\UESVALLE"
set "SCRIPT=generar_indice_resultados_agua.py"
set "SCRIPT_PATH=%~dp0%SCRIPT%"

cls
echo.
echo ============================================================
echo       UESVALLE - ACTUALIZAR ÍNDICE RESULTADOS AGUA
echo ============================================================
echo.
echo  Este proceso genera los CSV que alimentan el tablero:
echo.
echo    data\resultados_agua\current\indice_resultados_agua.csv
echo    data\resultados_agua\current\resumen_resultados_agua.csv
echo    data\resultados_agua\current\metadata_resultados_agua.json
echo.
echo ------------------------------------------------------------
echo.

if not exist "%SCRIPT_PATH%" (
    echo [ERROR] No se encontro el script:
    echo         %SCRIPT_PATH%
    echo.
    pause
    exit /b 1
)

cd /d "%PORTAL_ROOT%"

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
    echo.
    echo [AVISO] Faltan dependencias. Se intentara instalarlas automaticamente.
    echo.
    "%PYTHON_EXE%" -m pip install pandas openpyxl
)

echo.
echo Iniciando actualización de índice...
echo.

"%PYTHON_EXE%" "%SCRIPT_PATH%"

echo.
echo ============================================================
echo        ACTUALIZACIÓN FINALIZADA
echo ============================================================
echo.
pause
endlocal
