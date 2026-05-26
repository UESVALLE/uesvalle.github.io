@echo off
chcp 65001 > nul
setlocal EnableExtensions EnableDelayedExpansion

title UESVALLE - Inventario General Resultados Agua

REM ============================================================
REM  UESVALLE - INVENTARIO GENERAL DE RESULTADOS DE AGUA
REM
REM  BAT FINAL OPERATIVO
REM
REM  Este archivo ejecuta:
REM    Inventario_Resultados_Agua_UESVALLE.py
REM
REM  Ubicación recomendada:
REM    G:\Mi unidad\8.UES\PAGINA INDICADORES\UESVALLE\scripts\resultados_agua
REM
REM  En esa misma carpeta deben estar:
REM    - Ejecutar_Inventario_Resultados_Agua.bat
REM    - Inventario_Resultados_Agua_UESVALLE.py
REM
REM  Nota:
REM    Si se trabaja con versiones V4, V5 o V6, la versión definitiva
REM    debe renombrarse como:
REM      Inventario_Resultados_Agua_UESVALLE.py
REM ============================================================

set "PORTAL_ROOT=G:\Mi unidad\8.UES\PAGINA INDICADORES\UESVALLE"
set "SCRIPT_DIR=G:\Mi unidad\8.UES\PAGINA INDICADORES\UESVALLE\scripts\resultados_agua"
set "SCRIPT=Inventario_Resultados_Agua_UESVALLE.py"
set "SCRIPT_PATH=%SCRIPT_DIR%\%SCRIPT%"

cls
echo.
echo ============================================================
echo        UESVALLE - INVENTARIO GENERAL RESULTADOS AGUA
echo ============================================================
echo.
echo  Este asistente consulta la tabla general de resultados
echo  de gestion-muestras.valledelcauca.gov.co/results
echo.
echo  Funcion:
echo    - Inicia sesion por ARO.
echo    - Aplica Clase de muestra = Agua.
echo    - Mantiene Estado = Finalizada.
echo    - Cambia el paginador a 100 registros.
echo    - Recorre las paginas de la tabla.
echo    - Genera inventario y fechas disponibles.
echo.
echo  No descarga PDF.
echo  No entra a cada registro.
echo  No requiere ingresar fechas.
echo.
echo ------------------------------------------------------------
echo.

echo Portal UESVALLE:
echo   %PORTAL_ROOT%
echo.
echo Script a ejecutar:
echo   %SCRIPT_PATH%
echo.

if not exist "%PORTAL_ROOT%" (
    echo [ERROR] No se encontro la carpeta del portal:
    echo   %PORTAL_ROOT%
    echo.
    pause
    exit /b 1
)

if not exist "%SCRIPT_DIR%" (
    echo [ERROR] No se encontro la carpeta de scripts:
    echo   %SCRIPT_DIR%
    echo.
    pause
    exit /b 1
)

if not exist "%SCRIPT_PATH%" (
    echo [ERROR] No se encontro el script:
    echo   %SCRIPT_PATH%
    echo.
    echo Verifica que la version final del script este guardada con este nombre:
    echo   Inventario_Resultados_Agua_UESVALLE.py
    echo.
    echo Si descargaste una version como:
    echo   Inventario_Resultados_Agua_UESVALLE_V6.py
    echo debes renombrarla como:
    echo   Inventario_Resultados_Agua_UESVALLE.py
    echo.
    pause
    exit /b 1
)

cd /d "%PORTAL_ROOT%"

REM ------------------------------------------------------------
REM  Seleccion de Python
REM ------------------------------------------------------------
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
    echo.
    "%PYTHON_EXE%" -m pip install selenium webdriver-manager pandas openpyxl
    echo.
    echo Reintentando validacion de dependencias...
    "%PYTHON_EXE%" -c "import selenium, pandas, openpyxl, webdriver_manager" > nul 2>&1

    if errorlevel 1 (
        echo.
        echo [ERROR] No fue posible validar las dependencias.
        echo Ejecuta manualmente:
        echo   "%PYTHON_EXE%" -m pip install selenium webdriver-manager pandas openpyxl
        echo.
        pause
        exit /b 1
    )
)

echo [OK] Dependencias listas.
echo.
echo ------------------------------------------------------------
echo  Iniciando inventario general de resultados de agua...
echo ------------------------------------------------------------
echo.

"%PYTHON_EXE%" "%SCRIPT_PATH%"

echo.
echo ============================================================
echo        PROCESO FINALIZADO - INVENTARIO RESULTADOS AGUA
echo ============================================================
echo.
echo Revisa los archivos generados en:
echo   G:\Mi unidad\8.UES\PAGINA INDICADORES\UESVALLE\data\resultados_agua\current
echo.
pause
endlocal
