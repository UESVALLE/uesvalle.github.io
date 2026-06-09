@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion

set "REPO=G:\Mi unidad\8.UES\PAGINA INDICADORES\UESVALLE"
set "PYTHON=C:\Users\Javier\miniconda3\envs\analitica\python.exe"
set "DESCARGA_SCRIPT=%REPO%\scripts\mpr\01_descargar_censo_sisa_mpr.py"

echo ====================================================================================================
echo ACTUALIZAR MPR DESDE SISA - DESCARGA CENSO + NORMALIZACION + PUBLICACION GITHUB
echo ====================================================================================================
echo Repo:   %REPO%
echo Python: %PYTHON%
echo Script: %DESCARGA_SCRIPT%
echo.

cd /d "%REPO%"
if errorlevel 1 goto error

echo [1/5] Verificando que exista el archivo local de credenciales...
if not exist "%REPO%\scripts\mpr\config_sisa.env" (
    echo [ERROR] No existe scripts\mpr\config_sisa.env
    echo Cree este archivo local con las credenciales de SISA.
    echo Este archivo NO debe subirse a GitHub.
    pause
    exit /b 1
)

echo [2/5] Descargando censo desde SISA y normalizando tablero...
"%PYTHON%" "%DESCARGA_SCRIPT%"
if errorlevel 1 goto error

echo.
echo [3/5] Preparando archivos permitidos para GitHub...
echo Se suben salidas operativas y scripts.
echo No se suben credenciales, censos crudos, backups ni carpetas historicas.

git add data/mpr/current/
git add data/mpr/raw/Programados.csv
git add data/mpr/raw/Codigos_poa.csv
git add scripts/mpr/01_descargar_censo_sisa_mpr.py
git add scripts/mpr/actualizar_mpr_desde_sisa.bat
git add scripts/mpr/normalizar_mpr.py
git add scripts/mpr/normalizar_mpr.bat
git add .gitignore

REM Seguridad preventiva.
git reset -- scripts/mpr/config_sisa.env 2>nul
git reset -- data/mpr/raw/censo_visitasMPR.xlsx 2>nul
git reset -- data/mpr/raw/censo_visitasMPR_backup_*.xlsx 2>nul
git reset -- data/mpr/historical/ 2>nul
git reset -- archive/ 2>nul

echo.
echo [4/5] Estado de archivos preparados:
git status

echo.
set /p CONFIRMAR=¿Deseas crear commit y subir a GitHub ahora? Escribe S para continuar: 

if /I not "%CONFIRMAR%"=="S" (
    echo.
    echo Proceso local finalizado. No se subio a GitHub.
    pause
    exit /b 0
)

echo.
set "STAMP=%date:~-4%%date:~3,2%%date:~0,2%_%time:~0,2%%time:~3,2%"
set "STAMP=%STAMP: =0%"

echo [5/5] Creando commit...
git commit -m "Actualiza tablero MPR desde SISA %STAMP%"

if errorlevel 1 (
    echo.
    echo No se creo commit. Puede que no existan cambios nuevos.
    echo Se intentara hacer push por si existen commits pendientes.
)

echo.
echo Subiendo a GitHub...
git push uesvalle main
if errorlevel 1 goto error

echo.
echo ====================================================================================================
echo Proceso finalizado correctamente.
echo Tablero MPR actualizado localmente y publicado en GitHub.
echo ====================================================================================================
pause
exit /b 0

:error
echo.
echo [ERROR] El proceso termino con errores. Revise los mensajes anteriores.
pause
exit /b 1
