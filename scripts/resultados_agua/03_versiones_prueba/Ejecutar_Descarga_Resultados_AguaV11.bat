@echo off
chcp 65001 > nul
setlocal EnableExtensions EnableDelayedExpansion

title UESVALLE - Descarga Resultados Agua - Manual Fechas

REM ============================================================
REM  UESVALLE - DESCARGA RESULTADOS DE AGUA
REM  VERSION ESTABLE: FECHAS MANUALES SEPARADAS POR COMA
REM
REM  Ejecuta:
REM    Descargar_Resultados_Agua_UESVALLE_MANUAL_FECHAS.py
REM
REM  Ubicacion recomendada:
REM    G:\Mi unidad\8.UES\PAGINA INDICADORES\UESVALLE\scripts\resultados_agua\01_operativos
REM ============================================================

set "PORTAL_ROOT=G:\Mi unidad\8.UES\PAGINA INDICADORES\UESVALLE"
set "SCRIPT_DIR=%PORTAL_ROOT%\scripts\resultados_agua\01_operativos"
set "SCRIPT=Descargar_Resultados_Agua_UESVALLE_MANUAL_FECHAS.py"
set "SCRIPT_PATH=%SCRIPT_DIR%\%SCRIPT%"

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
echo No usa filtro automatico por año.
echo No construye plan de descarga.
echo.
echo ------------------------------------------------------------
echo.
echo Portal:
echo   %PORTAL_ROOT%
echo.
echo Script:
echo   %SCRIPT_PATH%
echo.

if not exist "%SCRIPT_PATH%" (
    echo [ERROR] No se encontro el script:
    echo   %SCRIPT_PATH%
    echo.
    echo Verifica que el archivo este en:
    echo   %SCRIPT_DIR%
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
)

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
