"""
GESPE v1.0 — Pensión El Refugio de la Brisa
Servidor principal FastAPI con SQLite
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# ── Importar routers ──────────────────────────────────────────
from routes.auth          import router as auth_router
from routes.usuarios      import router as usuarios_router
from routes.pensionados   import router as pensionados_router
from routes.operaciones   import router as operaciones_router
from routes.administracion import router as admin_router

# ── App ───────────────────────────────────────────────────────
app = FastAPI(
    title="GESPE — Pensión El Refugio de la Brisa",
    description="Sistema de gestión para pensión/restaurante",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────
app.include_router(auth_router)
app.include_router(usuarios_router)
app.include_router(pensionados_router)
app.include_router(operaciones_router)
app.include_router(admin_router)

# ── Servir frontend ───────────────────────────────────────────
FRONTEND_DIR = Path(__file__).parent.parent / "frontend"

@app.get("/")
async def root():
    index = FRONTEND_DIR / "index.html"
    if index.exists():
        return FileResponse(str(index))
    return {"message": "GESPE API corriendo. Frontend no encontrado."}

@app.get("/health")
async def health():
    return {"status": "ok", "app": "GESPE v1.0"}

# Montar archivos estáticos del frontend
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

# ── Punto de entrada ──────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    print(f"""
╔══════════════════════════════════════════════╗
║   GESPE v1.0 — Pensión El Refugio de Brisa  ║
╠══════════════════════════════════════════════╣
║  Servidor:  http://localhost:{port}            ║
║  API Docs:  http://localhost:{port}/docs       ║
║  ReDoc:     http://localhost:{port}/redoc      ║
╚══════════════════════════════════════════════╝
    """)
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
