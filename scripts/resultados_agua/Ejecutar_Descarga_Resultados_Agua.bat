@echo off
chcp 65001 > nul
setlocal EnableExtensions EnableDelayedExpansion

title UESVALLE - Descarga de Resultados de Agua

REM ============================================================
REM  UESVALLE - DESCARGA DE RESULTADOS DE AGUA
REM  Ubicación recomendada:
REM    G:\Mi unidad\8.UES\PAGINA INDICADORES\UESVALLE\scripts\resultados_agua
REM
REM  Este BAT ejecuta:
REM    Descargar_Resultados_Agua_UESVALLE_V7.py
REM ============================================================

set "PORTAL_ROOT=G:\Mi unidad\8.UES\PAGINA INDICADORES\UESVALLE"
set "SCRIPT=Descargar_Resultados_Agua_UESVALLE_V7.py"
set "SCRIPT_PATH=%~dp0%SCRIPT%"

cls
echo.
echo ============================================================
echo        UESVALLE - DESCARGA DE RESULTADOS DE AGUA
echo ============================================================
echo.
echo  Portal UESVALLE:
echo    %PORTAL_ROOT%
echo.
echo  Repositorio documental PDF:
echo    G:\.shortcut-targets-by-id\1yROfpmz8yE8ttn9XJ1jioWMULcTpV8XA\2026\Agua para consumo\Resultados_muestras
echo.
echo  Salida PDF:
echo    Resultados_muestras\PDF_Resultados\2026\Cartago
echo    Resultados_muestras\PDF_Resultados\2026\Cali
echo    Resultados_muestras\PDF_Resultados\2026\Tulua
echo.
echo ------------------------------------------------------------
echo.

if not exist "%SCRIPT_PATH%" (
    echo [ERROR] No se encontro el script:
    echo         %SCRIPT_PATH%
    echo.
    echo Deben estar juntos estos dos archivos:
    echo   - Ejecutar_Descarga_Resultados_Agua.bat
    echo   - Descargar_Resultados_Agua_UESVALLE_V7.py
    echo.
    pause
    exit /b 1
)

if not exist "%PORTAL_ROOT%" (
    echo [ERROR] No se encontro la carpeta del portal:
    echo         %PORTAL_ROOT%
    echo.
    pause
    exit /b 1
)

cd /d "%PORTAL_ROOT%"

REM ------------------------------------------------------------
REM  Seleccion de Python
REM ------------------------------------------------------------
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
    echo.
    "%PYTHON_EXE%" -m pip install selenium webdriver-manager pandas openpyxl
    echo.
    echo Reintentando validacion...
    "%PYTHON_EXE%" -c "import selenium, pandas, openpyxl, webdriver_manager" > nul 2>&1

    if errorlevel 1 (
        echo.
        echo [ERROR] No fue posible validar las dependencias.
        echo Ejecuta manualmente:
        echo   "%PYTHON_EXE%" -m pip install selenium webdriver-manager pandas openpyxl
        echo.
        pause
        exit /b 1
    )
)

echo [OK] Dependencias listas.
echo.
echo ------------------------------------------------------------
echo  Iniciando descarga...
echo ------------------------------------------------------------
echo.

"%PYTHON_EXE%" "%SCRIPT_PATH%"

echo.
echo ============================================================
echo        PROCESO FINALIZADO - UESVALLE
echo ============================================================
echo.
pause
endlocal
