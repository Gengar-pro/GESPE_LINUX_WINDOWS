"""
GESPE — Inicializar base de datos SQLite y crear usuario admin.
Ejecutar una sola vez: python db/init.py
"""
import asyncio
import os
import sys

# Asegurar que el path sea correcto
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

import aiosqlite
from passlib.context import CryptContext

DB_PATH = os.getenv("DB_PATH", "./db/gespe.db")
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schema.sql")

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

MESAS_INICIALES = [
    (1, 4, "salon"), (2, 4, "salon"), (3, 4, "salon"), (4, 6, "salon"),
    (5, 6, "salon"), (6, 2, "barra"), (7, 2, "barra"), (8, 4, "terraza"),
    (9, 4, "terraza"), (10, 8, "vip"),
]

async def init():
    os.makedirs(os.path.dirname(DB_PATH) if os.path.dirname(DB_PATH) else ".", exist_ok=True)

    print(f"📦 Conectando a: {DB_PATH}")
    db = await aiosqlite.connect(DB_PATH)
    await db.execute("PRAGMA foreign_keys = ON")
    await db.execute("PRAGMA journal_mode = WAL")

    # Ejecutar schema
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema = f.read()
    await db.executescript(schema)
    print("✅ Esquema creado")

    # Crear admin
    admin_pass = pwd_ctx.hash("admin123")
    await db.execute("""
        INSERT OR IGNORE INTO usuarios (username, email, password_hash, rol)
        VALUES (?, ?, ?, ?)
    """, ("admin", "admin@gespe.local", admin_pass, "admin"))

    # Crear mesas iniciales
    for num, cap, zona in MESAS_INICIALES:
        await db.execute("""
            INSERT OR IGNORE INTO mesas (numero, capacidad, zona) VALUES (?, ?, ?)
        """, (num, cap, zona))

    # Combos de ejemplo
    await db.execute("SELECT id FROM categorias WHERE nombre='Almuerzo'")
    row = await (await db.execute("SELECT id FROM categorias WHERE nombre='Almuerzo'")).fetchone()
    if row:
        cat_id = row[0]
        combos = [
            ("Almuerzo completo", "Sopa + segundo + postre + refresco", 35.0, cat_id),
            ("Almuerzo simple", "Segundo + refresco", 25.0, cat_id),
            ("Sopa del día", "Sopa casera con pan", 12.0, cat_id),
        ]
        for c in combos:
            await db.execute("""
                INSERT OR IGNORE INTO combos (nombre, descripcion, precio, categoria_id)
                VALUES (?, ?, ?, ?)
            """, c)

    row2 = await (await db.execute("SELECT id FROM categorias WHERE nombre='Desayuno'")).fetchone()
    if row2:
        cat_id2 = row2[0]
        desayunos = [
            ("Desayuno completo", "Té/café + pan + huevos + fruta", 20.0, cat_id2),
            ("Desayuno simple", "Té/café + pan con mantequilla", 12.0, cat_id2),
        ]
        for d in desayunos:
            await db.execute("""
                INSERT OR IGNORE INTO combos (nombre, descripcion, precio, categoria_id)
                VALUES (?, ?, ?, ?)
            """, d)

    row3 = await (await db.execute("SELECT id FROM categorias WHERE nombre='Bebidas'")).fetchone()
    if row3:
        cat_id3 = row3[0]
        await db.execute("""
            INSERT OR IGNORE INTO combos (nombre, descripcion, precio, categoria_id)
            VALUES ('Refresco natural', 'Jugo de fruta de temporada', 8.0, ?)
        """, (cat_id3,))

    await db.commit()
    await db.close()

    print("✅ Usuario admin creado")
    print("   → usuario: admin")
    print("   → contraseña: admin123")
    print("✅ 10 mesas creadas")
    print("✅ Combos de ejemplo creados")
    print("\n🚀 Base de datos lista. Ejecuta main.py para iniciar el servidor.")

if __name__ == "__main__":
    asyncio.run(init())
