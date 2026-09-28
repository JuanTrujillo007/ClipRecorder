@echo off
chcp 65001 >nul
title Compilador de Game Clip Recorder

echo ========================================================
echo   Preparando la compilacion de GameClipRecorder a .exe
echo ========================================================
echo.

echo 1. Instalando herramienta de compilacion (PyInstaller)...
pip install pyinstaller --quiet
echo.

echo 2. Construyendo archivo ejecutable (Esto tomara 1-2 minutos)...
echo.
:: --noconsole oculta la ventana negra de MS-DOS por detras
:: --onefile empaqueta todo en un solo .exe
pyinstaller --noconsole --onefile GameClipRecorder.py

echo.
echo ========================================================
echo COMPILACION TERMINADA
echo ========================================================
echo Si todo salio bien, veras una nueva carpeta llamada "dist"
echo Entra a la carpeta "dist" y ahi estara "GameClipRecorder.exe"
echo Ese es el archivo que le debes pasar a tus amigos.
echo.
pause
