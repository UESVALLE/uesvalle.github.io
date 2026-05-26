@echo off
chcp 65001 > nul
setlocal EnableExtensions EnableDelayedExpansion

title UESVALLE - Descarga Resultados Agua - Fechas Manuales

REM ============================================================
REM  UESVALLE - DESCARGA RESULTADOS DE AGUA
REM  VERSION ESTABLE - FECHAS MANUALES SEPARADAS POR COMA
REM
REM  Este BAT busca el script en este orden:
REM    1) En la misma carpeta donde esta este BAT
REM    2) En scripts\resultados_agua\01_operativos
REM
REM  Script esperado:
REM    Descargar_Resultados_Agua_UESVALLE_MANUAL_FECHAS.py
REM ============================================================

set "PORTAL_ROOT=G:\Mi unidad\8.UES\PAGINA INDICADORES\UESVALLE"
set "SCRIPT_NAME=Descargar_Resultados_Agua_UESVALLE_MANUAL_FECHAS.py"

REM Carpeta donde esta ubicado este BAT
set "BAT_DIR=%~dp0"
set "BAT_DIR=%BAT_DIR:~0,-1%"

REM Primera opcion: el script esta junto al BAT
set "SCRIPT_PATH=%BAT_DIR%\%SCRIPT_NAME%"

REM Segunda opcion: carpeta operativa del portal
if not exist "%SCRIPT_PATH%" (
    set "SCRIPT_PATH=%PORTAL_ROOT%\scripts\resultados_agua\01_operativos\%SCRIPT_NAME%"
)

cls
echo.
echo ============================================================
echo     UESVALLE - DESCARGA RESULTADOS AGUA
echo     VERSION ESTABLE - FECHAS MANUALES
echo ============================================================
echo.
echo Esta version usa el flujo estable:
echo   - Seleccion de proceso
echo   - Seleccion de alcance: TODAS AGUA, MR, VDM, VIG, DIAG, DSAN
echo   - Seleccion de ARO
echo   - Fechas de recepcion separadas por coma
echo   - Descarga PDF desde la plataforma
echo.
echo No usa inventario maestro.
echo No usa filtro automatico por anio.
echo No construye plan de descarga.
echo.
echo ------------------------------------------------------------
echo.
echo Portal:
echo   %PORTAL_ROOT%
echo.
echo Carpeta BAT:
echo   %BAT_DIR%
echo.
echo Script a ejecutar:
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
    echo Verifica que exista uno de estos archivos:
    echo.
    echo   %BAT_DIR%\%SCRIPT_NAME%
    echo.
    echo o:
    echo.
    echo   %PORTAL_ROOT%\scripts\resultados_agua\01_operativos\%SCRIPT_NAME%
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
    echo [AVISO] Faltan dependencias. Se intentara instalarlas automaticamente.
    "%PYTHON_EXE%" -m pip install selenium webdriver-manager pandas openpyxl
    echo.
    echo Reintentando validacion...
    "%PYTHON_EXE%" -c "import selenium, pandas, openpyxl, webdriver_manager" > nul 2>&1

    if errorlevel 1 (
        echo.
        echo [ERROR] No se pudieron validar las dependencias.
        echo Ejecuta manualmente:
        echo   "%PYTHON_EXE%" -m pip install selenium webdriver-manager pandas openpyxl
        echo.
        pause
        exit /b 1
    )
)

echo [OK] Dependencias listas.
echo.
echo Ejecutando descarga estable por fechas manuales...
echo.

cd /d "%PORTAL_ROOT%"
"%PYTHON_EXE%" "%SCRIPT_PATH%"

echo.
echo ============================================================
echo          PROCESO FINALIZADO
echo ============================================================
echo.
pause
endlocal
