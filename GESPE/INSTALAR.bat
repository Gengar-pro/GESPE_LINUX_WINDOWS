@echo off
chcp 65001 > nul
title GESPE — Instalador
color 0A

echo.
echo  ╔══════════════════════════════════════════╗
echo  ║   GESPE v1.0 — Instalador               ║
echo  ║   Pensión El Refugio de la Brisa        ║
echo  ╚══════════════════════════════════════════╝
echo.

:: Verificar Python
python --version > nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Python no encontrado.
    echo  Descargalo desde: https://python.org
    echo  Asegurate de marcar "Add to PATH" al instalar.
    pause
    exit /b 1
)
echo  [OK] Python encontrado.

:: Crear .env si no existe
if not exist "backend\.env" (
    copy "backend\.env.example" "backend\.env" > nul
    echo  [OK] Archivo .env creado desde .env.example
) else (
    echo  [OK] .env ya existe.
)

:: Crear carpeta db si no existe
if not exist "backend\db" mkdir "backend\db"

:: Instalar dependencias
echo.
echo  Instalando dependencias Python...
echo  (esto puede tardar 1-2 minutos la primera vez)
echo.
cd backend
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo  [ERROR] Fallo al instalar dependencias.
    pause
    exit /b 1
)
echo  [OK] Dependencias instaladas.

:: Inicializar base de datos
echo.
echo  Inicializando base de datos SQLite...
python db/init.py
if errorlevel 1 (
    echo  [ERROR] Fallo al inicializar la base de datos.
    pause
    exit /b 1
)

cd ..

echo.
echo  ╔══════════════════════════════════════════╗
echo  ║   Instalacion completada exitosamente!  ║
echo  ║                                          ║
echo  ║   Ahora ejecuta: INICIAR.bat            ║
echo  ║                                          ║
echo  ║   Usuario: admin                        ║
echo  ║   Contraseña: admin123                  ║
echo  ╚══════════════════════════════════════════╝
echo.
pause
