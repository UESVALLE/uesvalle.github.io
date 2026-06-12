@echo off
setlocal EnableExtensions
chcp 65001 >nul

echo =============================================================================
echo  ACTUALIZAR DATOS TABLERO SEDES EDUCATIVAS - UESVALLE
echo =============================================================================

set "ROOT=G:\Mi unidad\8.UES\PAGINA INDICADORES\UESVALLE"
set "PYTHON_EXE=C:\Users\Javier\miniconda3\envs\analitica\python.exe"
set "SCRIPT=%ROOT%\scripts\sedes_educativas\normalizar_sedes_educativas.py"
set "RAW=%ROOT%\data\sedes_educativas\raw"

echo Repositorio: %ROOT%
echo Python     : %PYTHON_EXE%
echo Script     : %SCRIPT%
echo.

if not exist "%PYTHON_EXE%" (
  echo [ERROR] No se encuentra el entorno Python analitica:
  echo %PYTHON_EXE%
  pause
  exit /b 1
)

if not exist "%SCRIPT%" (
  echo [ERROR] No se encuentra el script:
  echo %SCRIPT%
  pause
  exit /b 1
)

if not exist "%RAW%\Escuelas_IRCAS.xlsx" (
  echo [ERROR] Falta el archivo fuente:
  echo %RAW%\Escuelas_IRCAS.xlsx
  pause
  exit /b 1
)

if not exist "%RAW%\SedesUESVALLE.xlsx" (
  echo [ERROR] Falta el archivo fuente:
  echo %RAW%\SedesUESVALLE.xlsx
  pause
  exit /b 1
)

cd /d "%ROOT%"
"%PYTHON_EXE%" "%SCRIPT%"
if errorlevel 1 (
  echo.
  echo [ERROR] El proceso finalizo con errores. Revise el mensaje anterior.
  pause
  exit /b 1
)

echo.
echo =============================================================================
echo  PROCESO FINALIZADO CORRECTAMENTE
echo =============================================================================
echo.
echo Revise las salidas en:
echo %ROOT%\data\sedes_educativas\current
echo.
echo Y el Excel de control en:
echo %ROOT%\docs\sedes_educativas
echo.
pause
endlocal
