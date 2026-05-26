@echo off
chcp 65001 > nul
setlocal EnableExtensions EnableDelayedExpansion

title UESVALLE - Detectar Fechas Resultados Agua

REM ============================================================
REM  UESVALLE - DETECTAR FECHAS DISPONIBLES DE RESULTADOS DE AGUA
REM  Ejecuta:
REM    Detectar_Fechas_Resultados_Agua_UESVALLE.py
REM ============================================================

set "PORTAL_ROOT=G:\Mi unidad\8.UES\PAGINA INDICADORES\UESVALLE"
set "SCRIPT=Detectar_Fechas_Resultados_Agua_UESVALLE.py"
set "SCRIPT_PATH=%~dp0%SCRIPT%"

cls
echo.
echo ============================================================
echo        UESVALLE - DETECTAR FECHAS RESULTADOS AGUA
echo ============================================================
echo.
echo  Este asistente consulta la tabla general de resultados
echo  sin descargar PDF, para identificar fechas con registros.
echo.
echo  Portal UESVALLE:
echo    %PORTAL_ROOT%
echo.
echo ------------------------------------------------------------
echo.

if not exist "%SCRIPT_PATH%" (
    echo [ERROR] No se encontro el script:
    echo         %SCRIPT_PATH%
    echo.
    echo Deben estar juntos estos dos archivos:
    echo   - Detectar_Fechas_Resultados_Agua_UESVALLE.py
    echo   - Ejecutar_Detectar_Fechas_Resultados_Agua.bat
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
"%PYTHON_EXE%" -c "import selenium, pandas, openpyxl, webdriver_manager" > nul 2>&1

if errorlevel 1 (
    echo.
    echo [AVISO] Faltan dependencias. Se intentara instalarlas automaticamente.
    "%PYTHON_EXE%" -m pip install selenium webdriver-manager pandas openpyxl
)

echo.
echo Iniciando consulta de fechas disponibles...
echo.

"%PYTHON_EXE%" "%SCRIPT_PATH%"

echo.
echo ============================================================
echo        PROCESO FINALIZADO - UESVALLE
echo ============================================================
echo.
pause
endlocal
