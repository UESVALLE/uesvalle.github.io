@echo off
chcp 65001 > nul
setlocal EnableExtensions EnableDelayedExpansion

title UESVALLE - Seguimiento semanal muestras registradas de agua

set "PORTAL_ROOT=G:\Mi unidad\8.UES\PAGINA INDICADORES\UESVALLE"
set "SCRIPT_DIR=%PORTAL_ROOT%\scripts\resultados_agua\04_seguimiento_muestras"
set "SCRIPT=Seguimiento_Muestras_Registradas_Agua.py"
set "SCRIPT_PATH=%SCRIPT_DIR%\%SCRIPT%"

cls
echo.
echo ============================================================
echo      UESVALLE - SEGUIMIENTO MUESTRAS REGISTRADAS AGUA
echo ============================================================
echo.
echo Este proceso:
echo   - NO descarga PDF.
echo   - NO abre fichas.
echo   - Solo lee la tabla inicial de Listado de Muestras Registradas.
echo   - Usa los mismos usuarios y claves del script V7.
echo   - Actualiza current y guarda copia historica.
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
"%PYTHON_EXE%" -c "import selenium, pandas, openpyxl, webdriver_manager" > nul 2>&1
if errorlevel 1 (
    echo [AVISO] Faltan dependencias. Se intentara instalarlas.
    "%PYTHON_EXE%" -m pip install selenium webdriver-manager pandas openpyxl
)

cd /d "%PORTAL_ROOT%"
"%PYTHON_EXE%" "%SCRIPT_PATH%"

echo.
echo ============================================================
echo          PROCESO FINALIZADO
echo ============================================================
pause
endlocal
