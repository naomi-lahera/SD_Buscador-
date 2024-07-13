@echo off
setlocal enabledelayedexpansion

:: Captura todos los argumentos pasados a run.bat
set ARGUMENTOS=%*

:: Ejecuta el comando docker con los argumentos capturados
docker run -it --rm -v "C:\Users\53527\Desktop\SD_Buscador-:/app" sist-dist:v0 /bin/bash -c "python3 src/server/__init__.py %ARGUMENTOS% && exec bash"