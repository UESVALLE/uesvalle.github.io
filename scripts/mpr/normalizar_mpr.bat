@echo off
chcp 65001 >nul
setlocal

echo ==============================================================================
echo NORMALIZAR SEGUIMIENTO MAPAS DE RIESGO MPR - UESVALLE V1.2
echo ==============================================================================

set "PYTHON_EXE=C:\Users\Javier\miniconda3\envs\analitica\python.exe"
set "REPO_ROOT=G:\Mi unidad\8.UES\PAGINA INDICADORES\UESVALLE"
set "SCRIPT=%REPO_ROOT%\scripts\mpr\normalizar_mpr.py"

echo Repo: %REPO_ROOT%
echo Script: %SCRIPT%
echo Python: %PYTHON_EXE%
echo.

"%PYTHON_EXE%" "%SCRIPT%"

echo.
echo Proceso finalizado.
pause
