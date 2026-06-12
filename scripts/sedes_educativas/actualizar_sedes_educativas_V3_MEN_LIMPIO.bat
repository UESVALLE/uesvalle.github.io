@echo off
setlocal EnableExtensions
chcp 65001 >nul

echo =============================================================================
echo  ACTUALIZAR DATOS TABLERO SEDES EDUCATIVAS V3 - MEN MATRICULA COORDENADAS
echo =============================================================================

set "ROOT=G:\Mi unidad\8.UES\PAGINA INDICADORES\UESVALLE"
set "PYTHON_EXE=C:\Users\Javier\miniconda3\envs\analitica\python.exe"
set "SCRIPT=%ROOT%\scripts\sedes_educativas\normalizar_sedes_educativas_V3_MEN_matricula_coordenadas.py"
set "RAW=%ROOT%\data\sedes_educativas\raw"

echo Repositorio: %ROOT%
echo Python     : %PYTHON_EXE%
echo Script     : %SCRIPT%
echo Fuentes    : %RAW%
echo.

if not exist "%PYTHON_EXE%" (
  echo [ERROR] No se encuentra el entorno Python analitica:
  echo %PYTHON_EXE%
  echo.
  echo Verifique que exista:
  echo C:\Users\Javier\miniconda3\envs\analitica\python.exe
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

if not exist "%RAW%\maestro_acueductos_uesvalle_2026_actualizado.csv" (
  echo [ERROR] Falta el archivo fuente para la capa de acueductos:
  echo %RAW%\maestro_acueductos_uesvalle_2026_actualizado.csv
  pause
  exit /b 1
)

if not exist "%RAW%\MEN_SEDES_EDUCATIVAS_PREESCOLAR_BASICA_Y_MEDIA_20260605.csv" (
  echo [ERROR] Falta el archivo fuente MEN:
  echo %RAW%\MEN_SEDES_EDUCATIVAS_PREESCOLAR_BASICA_Y_MEDIA_20260605.csv
  echo.
  echo IMPORTANTE:
  echo Para evitar errores con tildes, renombre el archivo MEN asi:
  echo MEN_SEDES_EDUCATIVAS_PREESCOLAR_BASICA_Y_MEDIA_20260605.csv
  pause
  exit /b 1
)

cd /d "%ROOT%"

echo.
echo Ejecutando normalizador V3...
echo.

"%PYTHON_EXE%" "%SCRIPT%"

if errorlevel 1 (
  echo.
  echo [ERROR] El proceso finalizo con errores. Revise el mensaje anterior.
  pause
  exit /b 1
)

echo.
echo =============================================================================
echo  PROCESO V3 FINALIZADO CORRECTAMENTE
echo =============================================================================
echo.
echo Revise las salidas principales en:
echo %ROOT%\data\sedes_educativas\current
echo.
echo Nuevos archivos de trazabilidad:
echo - validacion_matricula_fuentes.csv
echo - validacion_men_sedes.csv
echo.
echo Excel de control:
echo %ROOT%\docs\sedes_educativas\SEDES_EDUCATIVAS_IRCA_BASE_CONSOLIDADA_CONTROL.xlsx
echo.
pause
endlocal
