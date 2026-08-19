@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ============================================================
echo  S01_P4 - Naturaleza de los datos masivos
echo ============================================================
echo.
echo  Cada corrida se archiva en resultados\corridas\^<equipo^>\
echo  y NO sobrescribe a las anteriores. Si corre esto en sus dos
echo  maquinas, los entregables incluyen la comparacion entre ambas.
echo.
set "EQUIPO="
set /p EQUIPO="Etiqueta de este equipo (ej. portatil_16GB) [Enter = deducir sola]: "
if defined EQUIPO (set "ARG=--equipo %EQUIPO%") else (set "ARG=")
echo.
echo [1/4] Instalando dependencias...
python -m pip install --quiet pandas numpy psutil nbformat nbclient ipykernel
echo.
echo [1b] Autocomprobacion de los scripts...
python scripts\autocomprobacion.py
if errorlevel 1 (
  echo.
  echo  !! Los scripts tienen un problema. No se descarga nada hasta arreglarlo.
  pause
  exit /b 1
)
echo.
echo [2/4] Midiendo las fuentes...
echo       (SECOP II son ~200.000 filas: puede tardar varios minutos sin barra de progreso)
python scripts\ejecutar_todo.py %ARG%
if errorlevel 1 (
  echo.
  echo  !! La medicion fallo. Si fue por memoria, ESO ES UN RESULTADO:
  echo     anote con cuantas filas murio y reintente con menos, por ejemplo:
  echo         python scripts\ejecutar_todo.py %ARG% --filas 50000
  echo.
  pause
  exit /b 1
)
echo.
echo [3/4] Generando los entregables...
python scripts\generar_entregables.py
echo.
echo [4/4] Ejecutando el notebook...
python scripts\construir_notebook.py --ejecutar
echo.
echo ============================================================
echo  LISTO. Revise la carpeta resultados\
echo ============================================================
pause
