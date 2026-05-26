@echo off
chcp 65001 > nul
setlocal EnableExtensions

title Actualizar indice resultados agua UESVALLE

set "PORTAL_ROOT=G:\Mi unidad\8.UES\PAGINA INDICADORES\UESVALLE"
set "SCRIPT_DIR=G:\Mi unidad\8.UES\PAGINA INDICADORES\UESVALLE\scripts\resultados_agua"
set "SCRIPT=generar_indice_resultados_agua.py"
set "SCRIPT_PATH=%SCRIPT_DIR%\%SCRIPT%"

cls
echo.
echo ============================================================
echo     ACTUALIZAR INDICE RESULTADOS AGUA - UESVALLE
echo ============================================================
echo.
echo Portal:
echo   %PORTAL_ROOT%
echo.
echo Script:
echo   %SCRIPT_PATH%
echo.

if not exist "%PORTAL_ROOT%" (
    echo [ERROR] No existe la carpeta del portal:
    echo   %PORTAL_ROOT%
    echo.
    pause
    exit /b 1
)

if not exist "%SCRIPT_PATH%" (
    echo [ERROR] No se encontro el script:
    echo   %SCRIPT_PATH%
    echo.
    echo Verifica que el archivo generar_indice_resultados_agua.py este en:
    echo   %SCRIPT_DIR%
    echo.
    pause
    exit /b 1
)

set "PYTHON_EXE=C:\Users\Javier\miniconda3\envs\analitica\python.exe"

if not exist "%PYTHON_EXE%" (
    set "PYTHON_EXE=C:\Users\Javier\anaconda3\envs\analitica\python.exe"
)

if not exist "%PYTHON_EXE%" (
    set "PYTHON_EXE=python"
)

echo Python seleccionado:
echo   %PYTHON_EXE%
echo.

echo Verificando dependencias...
"%PYTHON_EXE%" -c "import pandas, openpyxl" > nul 2>&1

if errorlevel 1 (
    echo.
    echo [AVISO] Faltan dependencias. Se intentara instalar pandas y openpyxl.
    "%PYTHON_EXE%" -m pip install pandas openpyxl
)

echo.
echo Ejecutando generacion de indice...
echo.

cd /d "%PORTAL_ROOT%"
"%PYTHON_EXE%" "%SCRIPT_PATH%"

echo.
echo ============================================================
echo     ACTUALIZACION FINALIZADA
echo ============================================================
echo.
pause
endlocal
