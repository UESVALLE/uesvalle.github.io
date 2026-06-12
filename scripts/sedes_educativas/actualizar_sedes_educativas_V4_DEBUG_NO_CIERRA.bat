@echo off
setlocal EnableExtensions
chcp 65001 >nul

set "ROOT=G:\Mi unidad\8.UES\PAGINA INDICADORES\UESVALLE"
set "PYTHON_EXE=C:\Users\Javier\miniconda3\envs\analitica\python.exe"
set "SCRIPT=%ROOT%\scripts\sedes_educativas\normalizar_sedes_educativas_V4_analitica_priorizacion.py"
set "RAW=%ROOT%\data\sedes_educativas\raw"
set "LOG=%ROOT%\scripts\sedes_educativas\LOG_SEDES_EDUCATIVAS_V4.txt"

echo =============================================================================
echo  ACTUALIZAR DATOS TABLERO SEDES EDUCATIVAS V4 - DEBUG
echo =============================================================================
echo.
echo Este BAT no se cerrara automaticamente.
echo Si ocurre un error, revise tambien:
echo %LOG%
echo.
echo Repositorio: %ROOT%
echo Python     : %PYTHON_EXE%
echo Script     : %SCRIPT%
echo Fuentes    : %RAW%
echo.

echo ============================================================================= > "%LOG%"
echo ACTUALIZAR DATOS TABLERO SEDES EDUCATIVAS V4 - DEBUG >> "%LOG%"
echo Fecha/hora: %DATE% %TIME% >> "%LOG%"
echo Repositorio: %ROOT% >> "%LOG%"
echo Python: %PYTHON_EXE% >> "%LOG%"
echo Script: %SCRIPT% >> "%LOG%"
echo Fuentes: %RAW% >> "%LOG%"
echo ============================================================================= >> "%LOG%"
echo. >> "%LOG%"

if not exist "%PYTHON_EXE%" (
  echo [ERROR] No se encuentra Python:
  echo %PYTHON_EXE%
  echo [ERROR] No se encuentra Python: %PYTHON_EXE% >> "%LOG%"
  goto FIN_ERROR
)

if not exist "%SCRIPT%" (
  echo [ERROR] No se encuentra el script:
  echo %SCRIPT%
  echo [ERROR] No se encuentra el script: %SCRIPT% >> "%LOG%"
  goto FIN_ERROR
)

if not exist "%RAW%\Escuelas_IRCAS.xlsx" (
  echo [ERROR] Falta Escuelas_IRCAS.xlsx
  echo [ERROR] Falta Escuelas_IRCAS.xlsx >> "%LOG%"
  goto FIN_ERROR
)

if not exist "%RAW%\SedesUESVALLE.xlsx" (
  echo [ERROR] Falta SedesUESVALLE.xlsx
  echo [ERROR] Falta SedesUESVALLE.xlsx >> "%LOG%"
  goto FIN_ERROR
)

if not exist "%RAW%\maestro_acueductos_uesvalle_2026_actualizado.csv" (
  echo [ERROR] Falta maestro_acueductos_uesvalle_2026_actualizado.csv
  echo [ERROR] Falta maestro_acueductos_uesvalle_2026_actualizado.csv >> "%LOG%"
  goto FIN_ERROR
)

if not exist "%RAW%\MEN_SEDES_EDUCATIVAS_PREESCOLAR_BASICA_Y_MEDIA_20260605.csv" (
  if not exist "%RAW%\MEN_SEDES_EDUCATIVAS_PREESCOLAR_BÁSICA_Y_MEDIA_20260605.csv" (
    echo [ERROR] Falta archivo fuente MEN.
    echo Buscado:
    echo %RAW%\MEN_SEDES_EDUCATIVAS_PREESCOLAR_BASICA_Y_MEDIA_20260605.csv
    echo [ERROR] Falta archivo fuente MEN. >> "%LOG%"
    goto FIN_ERROR
  )
)

cd /d "%ROOT%"
if errorlevel 1 (
  echo [ERROR] No se pudo entrar a la carpeta del repositorio.
  echo [ERROR] No se pudo entrar a la carpeta del repositorio. >> "%LOG%"
  goto FIN_ERROR
)

echo.
echo Ejecutando normalizador V4...
echo.

"%PYTHON_EXE%" "%SCRIPT%" 1>> "%LOG%" 2>>&1

set "ERR=%ERRORLEVEL%"

type "%LOG%"

if not "%ERR%"=="0" (
  echo.
  echo [ERROR] El proceso finalizo con errores. Codigo: %ERR%
  echo [ERROR] El proceso finalizo con errores. Codigo: %ERR% >> "%LOG%"
  goto FIN_ERROR
)

echo.
echo =============================================================================
echo  PROCESO V4 FINALIZADO CORRECTAMENTE
echo =============================================================================
echo.
echo Revise las salidas en:
echo %ROOT%\data\sedes_educativas\current
echo.
echo Nuevo archivo esperado:
echo %ROOT%\data\sedes_educativas\current\resumen_grupo_seguimiento.csv
echo.
goto FIN_OK

:FIN_ERROR
echo.
echo =============================================================================
echo  PROCESO DETENIDO CON ERROR
echo =============================================================================
echo.
echo Copie el contenido de esta ventana o revise el log:
echo %LOG%
echo.

:FIN_OK
pause
endlocal
