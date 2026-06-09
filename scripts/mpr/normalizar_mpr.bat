@echo off
setlocal

echo ==============================================================================
echo NORMALIZAR SEGUIMIENTO MAPAS DE RIESGO MPR - UESVALLE
echo ==============================================================================

set "PYTHON_EXE=C:\Users\Javier\miniconda3\envs\analitica\python.exe"
set "REPO_ROOT=G:\Mi unidad\8.UES\PAGINA INDICADORES\UESVALLE"
set "SCRIPT=%REPO_ROOT%\scripts\mpr\normalizar_mpr.py"

echo Repo: %REPO_ROOT%
echo Script: %SCRIPT%
echo Python: %PYTHON_EXE%
echo.

if not exist "%PYTHON_EXE%" (
    echo [ERROR] No existe el ejecutable de Python:
    echo %PYTHON_EXE%
    pause
    exit /b 1
)

if not exist "%SCRIPT%" (
    echo [ERROR] No existe el script:
    echo %SCRIPT%
    pause
    exit /b 1
)

cd /d "%REPO_ROOT%"
"%PYTHON_EXE%" "%SCRIPT%"

if errorlevel 1 (
    echo.
    echo [ERROR] El proceso termino con errores. Revise los mensajes anteriores.
    pause
    exit /b 1
)

echo.
echo Proceso finalizado correctamente.
pause
