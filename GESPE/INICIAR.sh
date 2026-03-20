#!/bin/bash
# GESPE v1.0 — Iniciar servidor en Linux/Ubuntu
# Ejecutar con: bash INICIAR.sh

echo ""
echo " ╔══════════════════════════════════════════╗"
echo " ║   GESPE v1.0 — Iniciando servidor...    ║"
echo " ╚══════════════════════════════════════════╝"
echo ""

# ── Verificar que la BD exista ────────────────────────────────
if [ ! -f "backend/db/gespe.db" ]; then
    echo " [AVISO] Base de datos no encontrada."
    echo " Ejecuta primero: bash INSTALAR.sh"
    exit 1
fi

# ── Usar venv si existe, sino python3 del sistema ─────────────
if [ -f "backend/venv/bin/python3.12" ]; then
    PYTHON="backend/venv/bin/python3.12"
elif [ -f "backend/venv/bin/python3" ]; then
    PYTHON="backend/venv/bin/python3"
else
    PYTHON="python3"
fi

echo " Servidor disponible en:"
echo ""
echo "   http://localhost:8000"
echo "   http://localhost:8000/docs  (API Docs)"
echo ""
echo " Presiona Ctrl+C para detener."
echo ""

cd backend
source venv/bin/activate
python main.py
