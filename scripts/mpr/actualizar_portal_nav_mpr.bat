@echo off
chcp 65001 >nul
setlocal

echo ================================================================================
echo ACTUALIZAR PORTAL Y NAVEGACION COMUN - MPR UESVALLE
echo ================================================================================

set "PYTHON_EXE=C:\Users\Javier\miniconda3\envs\analitica\python.exe"
set "SCRIPT=G:\Mi unidad\8.UES\PAGINA INDICADORES\UESVALLE\scripts\mpr\actualizar_portal_nav_mpr.py"

echo Python: %PYTHON_EXE%
echo Script: %SCRIPT%
echo.

"%PYTHON_EXE%" "%SCRIPT%"

echo.
pause
