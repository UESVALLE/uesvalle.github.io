@echo off
setlocal EnableExtensions
chcp 65001 >nul

echo =============================================================================
echo  ACTUALIZAR DATOS TABLERO SEDES EDUCATIVAS V4 - ANALITICA Y PRIORIZACION
echo =============================================================================

set "ROOT=G:\Mi unidad\8.UES\PAGINA INDICADORES\UESVALLE"
set "PYTHON_EXE=C:\Users\Javier\miniconda3\envs\analitica\python.exe"
set "SCRIPT=%ROOT%\scripts\sedes_educativas\normalizar_sedes_educativas_V4_analitica_priorizacion.py"
set "RAW=%ROOT%\data\sedes_educativas\raw"

echo Repositorio: %ROOT%
echo Python     : %PYTHON_EXE%
echo Script     : %SCRIPT%
echo Fuentes    : %RAW%
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

if not exist "%RAW%\maestro_acueductos_uesvalle_2026_actualizado.csv" (
  echo [ERROR] Falta el archivo fuente:
  echo %RAW%\maestro_acueductos_uesvalle_2026_actualizado.csv
  pause
  exit /b 1
)

if not exist "%RAW%\MEN_SEDES_EDUCATIVAS_PREESCOLAR_BASICA_Y_MEDIA_20260605.csv" (
  if not exist "%RAW%\MEN_SEDES_EDUCATIVAS_PREESCOLAR_BÁSICA_Y_MEDIA_20260605.csv" (
    echo [ERROR] Falta el archivo fuente MEN:
    echo %RAW%\MEN_SEDES_EDUCATIVAS_PREESCOLAR_BASICA_Y_MEDIA_20260605.csv
    echo.
    echo Tambien se acepta el nombre con tilde en BASICA.
    pause
    exit /b 1
  )
)

cd /d "%ROOT%"

echo.
echo Ejecutando normalizador V4...
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
echo  PROCESO V4 FINALIZADO CORRECTAMENTE
echo =============================================================================
echo.
echo Revise las salidas principales en:
echo %ROOT%\data\sedes_educativas\current
echo.
echo Nuevo archivo analitico:
echo - resumen_grupo_seguimiento.csv
echo.
echo Campos nuevos en sedes_educativas_irca_consolidado.csv:
echo - GRUPO_SEGUIMIENTO
echo - RIESGO_IRCA_AGRUPADO
echo - BRECHAS_INFORMACION
echo - CALIDAD_DATO_SEDE
echo - INDICE_PRIORIDAD_SANITARIA_ESCOLAR
echo - NIVEL_PRIORIDAD_ANALITICA
echo - ACCION_SUGERIDA
echo.
pause
endlocal
