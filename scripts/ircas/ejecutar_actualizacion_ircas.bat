@echo off
chcp 65001 >nul
title UESVALLE - Actualizar datos tablero IRCAS 2020-2026

echo ============================================================
echo   UESVALLE - ACTUALIZAR DATOS TABLERO IRCAS 2020-2026
echo ============================================================
echo.

set "REPO=G:\Mi unidad\8.UES\PAGINA INDICADORES\UESVALLE"
set "SCRIPT=%REPO%\scripts\ircas\generar_ircas_desde_base_acueductos.py"
set "INPUT=%REPO%\data\ircas\input\Base_Datos_Acueductos_2026.xlsx"
set "OUTPUT=%REPO%\data\ircas\current\IRCAS.csv"

REM Entorno usado en procesos anteriores de UESVALLE.
set "PY_ANALITICA=C:\Users\Javier\miniconda3\envs\analitica\python.exe"

echo Repo:
echo   %REPO%
echo.
echo Entrada esperada:
echo   %INPUT%
echo.
echo Salida esperada:
echo   %OUTPUT%
echo.

if not exist "%REPO%" (
    echo ERROR: No existe la carpeta del repositorio.
    echo %REPO%
    pause
    exit /b 1
)

if not exist "%SCRIPT%" (
    echo ERROR: No se encontro el script generador.
    echo %SCRIPT%
    pause
    exit /b 1
)

if not exist "%INPUT%" (
    echo ERROR: No se encontro el archivo de entrada.
    echo Copia Base_Datos_Acueductos_2026.xlsx en:
    echo %REPO%\data\ircas\input\
    pause
    exit /b 1
)

if exist "%PY_ANALITICA%" (
    set "PYTHON_EXE=%PY_ANALITICA%"
) else (
    set "PYTHON_EXE=python"
)

echo Python seleccionado:
echo   %PYTHON_EXE%
echo.

echo Verificando librerias requeridas...
"%PYTHON_EXE%" -c "import pandas, openpyxl; print('OK pandas:', pandas.__version__)" 2>nul

if errorlevel 1 (
    echo.
    echo ERROR: El Python seleccionado no tiene pandas/openpyxl.
    echo.
    echo Solucion recomendada:
    echo   conda activate analitica
    echo   conda install pandas openpyxl -y
    echo.
    echo O usando pip:
    echo   "%PYTHON_EXE%" -m pip install pandas openpyxl
    echo.
    pause
    exit /b 1
)

echo.
echo Ejecutando generador...
echo.

cd /d "%REPO%"
"%PYTHON_EXE%" "%SCRIPT%"

if errorlevel 1 (
    echo.
    echo ERROR: El proceso fallo. Revisa los mensajes anteriores.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo   PROCESO FINALIZADO CORRECTAMENTE
echo ============================================================
echo.
echo Archivo actualizado:
echo   %OUTPUT%
echo.
echo Siguiente paso recomendado:
echo   1. Abrir tablero local y validar.
echo   2. Ejecutar git status.
echo   3. Hacer commit y push cuando el HTML tambien quede ajustado a 2026.
echo.

pause
