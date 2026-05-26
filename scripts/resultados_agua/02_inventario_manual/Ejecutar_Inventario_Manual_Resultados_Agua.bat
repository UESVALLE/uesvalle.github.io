@echo off
chcp 65001 > nul
setlocal EnableExtensions EnableDelayedExpansion

title UESVALLE - Generar Inventario Manual Resultados Agua

REM ============================================================
REM  UESVALLE - GENERAR INVENTARIO MANUAL RESULTADOS AGUA
REM
REM  Lee:
REM    scripts\resultados_agua\02_inventario_manual\FECHAS CARTAGO.txt
REM    scripts\resultados_agua\02_inventario_manual\FECHAS CALI.txt
REM    scripts\resultados_agua\02_inventario_manual\FECHAS TULUA.txt
REM
REM  Genera:
REM    data\resultados_agua\current\inventario_resultados_agua.csv
REM    data\resultados_agua\current\inventario_resultados_agua_bruto.csv
REM    data\resultados_agua\current\duplicados_inventario_resultados_agua.csv
REM    data\resultados_agua\current\resumen_fechas_resultados_agua.csv
REM    data\resultados_agua\current\resumen_resultados_agua.csv
REM ============================================================

set "PORTAL_ROOT=G:\Mi unidad\8.UES\PAGINA INDICADORES\UESVALLE"
set "SCRIPT_PATH=%PORTAL_ROOT%\scripts\resultados_agua\02_inventario_manual\generar_inventario_manual_resultados_agua.py"

cls
echo.
echo ============================================================
echo      UESVALLE - INVENTARIO MANUAL RESULTADOS AGUA
echo ============================================================
echo.
echo Portal:
echo   %PORTAL_ROOT%
echo.
echo Script:
echo   %SCRIPT_PATH%
echo.

if not exist "%PORTAL_ROOT%" (
    echo [ERROR] No se encontro la carpeta del portal:
    echo   %PORTAL_ROOT%
    echo.
    pause
    exit /b 1
)

if not exist "%SCRIPT_PATH%" (
    echo [ERROR] No se encontro el script:
    echo   %SCRIPT_PATH%
    echo.
    echo Verifica que este BAT este apuntando a la carpeta correcta.
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
"%PYTHON_EXE%" -c "import pandas" > nul 2>&1

if errorlevel 1 (
    echo.
    echo [AVISO] Falta pandas. Se intentara instalar.
    "%PYTHON_EXE%" -m pip install pandas
)

echo.
echo Ejecutando inventario manual...
echo.

cd /d "%PORTAL_ROOT%"
"%PYTHON_EXE%" "%SCRIPT_PATH%"

echo.
echo ============================================================
echo            PROCESO FINALIZADO
echo ============================================================
echo.
echo Revisa las salidas en:
echo   %PORTAL_ROOT%\data\resultados_agua\current
echo.
pause
endlocal
