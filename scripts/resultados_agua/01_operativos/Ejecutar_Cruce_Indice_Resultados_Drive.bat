@echo off
chcp 65001 > nul
setlocal EnableExtensions EnableDelayedExpansion

title UESVALLE - Cruzar indice resultados con Drive

set "PORTAL_ROOT=G:\Mi unidad\8.UES\PAGINA INDICADORES\UESVALLE"
set "SCRIPT_PATH=%PORTAL_ROOT%\scripts\resultados_agua\01_operativos\cruzar_indice_resultados_con_drive.py"

cls
echo.
echo ============================================================
echo      UESVALLE - CRUZAR INDICE RESULTADOS CON DRIVE
echo ============================================================
echo.
echo Este proceso actualiza:
echo   data\resultados_agua\current\indice_resultados_agua.csv
echo.
echo Agregando:
echo   DRIVE_FILE_ID
echo   URL_DRIVE_VIEW
echo   URL_DRIVE_PREVIEW
echo   MATCH_DRIVE
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

cd /d "%PORTAL_ROOT%"
"%PYTHON_EXE%" "%SCRIPT_PATH%"

echo.
echo ============================================================
echo          PROCESO FINALIZADO
echo ============================================================
echo.
pause
endlocal
