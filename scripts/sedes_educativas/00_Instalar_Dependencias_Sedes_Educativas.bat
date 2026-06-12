@echo off
setlocal EnableExtensions
chcp 65001 >nul

echo =============================================================================
echo  INSTALAR DEPENDENCIAS - TABLERO SEDES EDUCATIVAS
echo =============================================================================
set "PYTHON_EXE=C:\Users\Javier\miniconda3\envs\analitica\python.exe"

if not exist "%PYTHON_EXE%" (
  echo [ERROR] No se encuentra el entorno analitica:
  echo %PYTHON_EXE%
  pause
  exit /b 1
)

"%PYTHON_EXE%" -m pip install pandas openpyxl
if errorlevel 1 (
  echo [ERROR] No fue posible instalar dependencias.
  pause
  exit /b 1
)

echo.
echo [OK] Dependencias instaladas.
pause
endlocal
