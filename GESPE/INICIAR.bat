@echo off
chcp 65001 > nul
title GESPE — Servidor
color 0B

echo.
echo  ╔══════════════════════════════════════════╗
echo  ║   GESPE v1.0 — Iniciando servidor...    ║
echo  ╚══════════════════════════════════════════╝
echo.

:: Verificar que la BD exista
if not exist "backend\db\gespe.db" (
    echo  [AVISO] Base de datos no encontrada.
    echo  Ejecuta primero INSTALAR.bat
    pause
    exit /b 1
)

echo  Servidor disponible en:
echo.
echo    http://localhost:8000
echo    http://localhost:8000/docs  (API Docs)
echo.
echo  Presiona Ctrl+C para detener el servidor.
echo.

cd backend
python main.py

pause
