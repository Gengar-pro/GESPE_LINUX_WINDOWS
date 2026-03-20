#!/bin/bash
# GESPE v1.0 — Instalador para Linux/Ubuntu
# Ejecutar una sola vez: bash INSTALAR.sh

set -e

echo ""
echo " ╔══════════════════════════════════════════╗"
echo " ║   GESPE v1.0 — Instalador Linux         ║"
echo " ║   Pensión El Refugio de la Brisa        ║"
echo " ╚══════════════════════════════════════════╝"
echo ""

# ── Verificar Python ─────────────────────────────────────────
if ! command -v python3 &>/dev/null; then
    echo " [!] Python3 no encontrado. Instalando..."
    sudo apt update && sudo apt install python3 python3-pip python3-venv -y
else
    echo " [OK] Python3 encontrado: $(python3 --version)"
fi

# ── Crear .env si no existe ───────────────────────────────────
if [ ! -f "backend/.env" ]; then
    cp backend/.env.example backend/.env
    echo " [OK] Archivo .env creado"
else
    echo " [OK] .env ya existe"
fi

# ── Crear carpeta db ──────────────────────────────────────────
mkdir -p backend/db

# ── Entorno virtual ───────────────────────────────────────────
if [ ! -d "backend/venv" ]; then
    echo ""
    echo " Creando entorno virtual..."
    python3 -m venv backend/venv
    echo " [OK] Entorno virtual creado"
fi

# ── Instalar dependencias ─────────────────────────────────────
echo ""
echo " Instalando dependencias Python..."
backend/venv/bin/pip install --upgrade pip -q
backend/venv/bin/pip install -r backend/requirements.txt -q
echo " [OK] Dependencias instaladas"

# ── Inicializar base de datos ─────────────────────────────────
echo ""
echo " Inicializando base de datos SQLite..."
cd backend
../backend/venv/bin/python3 db/init.py
cd ..

echo ""
echo " ╔══════════════════════════════════════════╗"
echo " ║   Instalación completada exitosamente!  ║"
echo " ║                                          ║"
echo " ║   Ahora ejecuta: bash INICIAR.sh        ║"
echo " ║                                          ║"
echo " ║   Usuario:    admin                     ║"
echo " ║   Contraseña: admin123                  ║"
echo " ╚══════════════════════════════════════════╝"
echo ""
