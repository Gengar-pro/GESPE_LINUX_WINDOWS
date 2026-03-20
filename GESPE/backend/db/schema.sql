-- GESPE v1.0 — Pensión El Refugio de la Brisa
-- Schema SQLite

PRAGMA foreign_keys = ON;

-- ─────────────────────────────────────────
-- USUARIOS DEL SISTEMA
-- ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS usuarios (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    username    TEXT UNIQUE NOT NULL,
    email       TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    rol         TEXT NOT NULL DEFAULT 'mesero' CHECK(rol IN ('admin','cajero','mesero','cocinero')),
    activo      INTEGER NOT NULL DEFAULT 1,
    created_at  TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);

-- ─────────────────────────────────────────
-- MESAS
-- ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS mesas (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    numero      INTEGER UNIQUE NOT NULL,
    capacidad   INTEGER NOT NULL DEFAULT 4,
    estado      TEXT NOT NULL DEFAULT 'libre' CHECK(estado IN ('libre','ocupada','reservada','mantenimiento')),
    zona        TEXT NOT NULL DEFAULT 'salon' CHECK(zona IN ('salon','terraza','vip','barra')),
    updated_at  TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);

-- ─────────────────────────────────────────
-- CATEGORÍAS DE MENÚ
-- ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS categorias (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre      TEXT UNIQUE NOT NULL,
    icono       TEXT DEFAULT '🍽️',
    activo      INTEGER NOT NULL DEFAULT 1
);

-- ─────────────────────────────────────────
-- COMBOS / MENÚ
-- ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS combos (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre      TEXT NOT NULL,
    descripcion TEXT,
    precio      REAL NOT NULL,
    categoria_id INTEGER REFERENCES categorias(id),
    disponible  INTEGER NOT NULL DEFAULT 1,
    imagen_url  TEXT,
    created_at  TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);

-- ─────────────────────────────────────────
-- PEDIDOS
-- ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS pedidos (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    mesa_id     INTEGER REFERENCES mesas(id),
    usuario_id  INTEGER REFERENCES usuarios(id),
    estado      TEXT NOT NULL DEFAULT 'abierto' CHECK(estado IN ('abierto','en_cocina','listo','cerrado','anulado')),
    total       REAL NOT NULL DEFAULT 0,
    notas       TEXT,
    created_at  TEXT NOT NULL DEFAULT (datetime('now','localtime')),
    updated_at  TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);

CREATE TABLE IF NOT EXISTS pedido_items (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    pedido_id       INTEGER NOT NULL REFERENCES pedidos(id) ON DELETE CASCADE,
    combo_id        INTEGER NOT NULL REFERENCES combos(id),
    cantidad        INTEGER NOT NULL DEFAULT 1,
    precio_unitario REAL NOT NULL,
    notas           TEXT,
    estado          TEXT NOT NULL DEFAULT 'pendiente' CHECK(estado IN ('pendiente','en_cocina','listo','entregado'))
);

-- ─────────────────────────────────────────
-- PENSIONADOS
-- ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS pensionados (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre          TEXT NOT NULL,
    apellido        TEXT NOT NULL,
    ci              TEXT UNIQUE,
    telefono        TEXT,
    direccion       TEXT,
    tipo_pension    TEXT NOT NULL DEFAULT 'completa' CHECK(tipo_pension IN ('completa','almuerzo','cena','desayuno')),
    precio_mensual  REAL NOT NULL DEFAULT 0,
    activo          INTEGER NOT NULL DEFAULT 1,
    notas           TEXT,
    created_at      TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);

CREATE TABLE IF NOT EXISTS cuponeras (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    pensionado_id   INTEGER NOT NULL REFERENCES pensionados(id),
    mes             INTEGER NOT NULL CHECK(mes BETWEEN 1 AND 12),
    anio            INTEGER NOT NULL,
    total_cupones   INTEGER NOT NULL DEFAULT 30,
    cupones_usados  INTEGER NOT NULL DEFAULT 0,
    activo          INTEGER NOT NULL DEFAULT 1,
    created_at      TEXT NOT NULL DEFAULT (datetime('now','localtime')),
    UNIQUE(pensionado_id, mes, anio)
);

CREATE TABLE IF NOT EXISTS uso_cuponera (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    cuponera_id     INTEGER NOT NULL REFERENCES cuponeras(id),
    tipo_comida     TEXT NOT NULL DEFAULT 'almuerzo' CHECK(tipo_comida IN ('desayuno','almuerzo','cena')),
    fecha           TEXT NOT NULL DEFAULT (date('now','localtime')),
    usuario_id      INTEGER REFERENCES usuarios(id)
);

-- ─────────────────────────────────────────
-- INVENTARIO
-- ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS inventario (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre          TEXT NOT NULL,
    categoria       TEXT NOT NULL DEFAULT 'otros',
    cantidad        REAL NOT NULL DEFAULT 0,
    unidad          TEXT NOT NULL DEFAULT 'unidad',
    precio_costo    REAL NOT NULL DEFAULT 0,
    stock_minimo    REAL NOT NULL DEFAULT 0,
    proveedor       TEXT,
    updated_at      TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);

CREATE TABLE IF NOT EXISTS movimientos_inventario (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    inventario_id   INTEGER NOT NULL REFERENCES inventario(id),
    tipo            TEXT NOT NULL CHECK(tipo IN ('entrada','salida','ajuste')),
    cantidad        REAL NOT NULL,
    descripcion     TEXT,
    usuario_id      INTEGER REFERENCES usuarios(id),
    created_at      TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);

-- ─────────────────────────────────────────
-- CAJA
-- ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS cajas (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha           TEXT NOT NULL DEFAULT (date('now','localtime')),
    saldo_inicial   REAL NOT NULL DEFAULT 0,
    saldo_final     REAL,
    estado          TEXT NOT NULL DEFAULT 'abierta' CHECK(estado IN ('abierta','cerrada')),
    usuario_id      INTEGER REFERENCES usuarios(id),
    notas           TEXT,
    created_at      TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);

CREATE TABLE IF NOT EXISTS movimientos_caja (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    caja_id         INTEGER NOT NULL REFERENCES cajas(id),
    tipo            TEXT NOT NULL CHECK(tipo IN ('ingreso','egreso')),
    monto           REAL NOT NULL,
    descripcion     TEXT NOT NULL,
    referencia      TEXT,
    metodo_pago     TEXT DEFAULT 'efectivo' CHECK(metodo_pago IN ('efectivo','tarjeta','transferencia','otro')),
    usuario_id      INTEGER REFERENCES usuarios(id),
    created_at      TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);

-- ─────────────────────────────────────────
-- PERSONAL
-- ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS personal (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre      TEXT NOT NULL,
    apellido    TEXT NOT NULL,
    ci          TEXT UNIQUE,
    cargo       TEXT NOT NULL DEFAULT 'mesero',
    telefono    TEXT,
    email       TEXT,
    sueldo      REAL NOT NULL DEFAULT 0,
    fecha_ingreso TEXT DEFAULT (date('now','localtime')),
    activo      INTEGER NOT NULL DEFAULT 1,
    notas       TEXT,
    created_at  TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);

-- ─────────────────────────────────────────
-- CONFIGURACIÓN
-- ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS config (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    clave       TEXT UNIQUE NOT NULL,
    valor       TEXT NOT NULL,
    descripcion TEXT
);

-- ─────────────────────────────────────────
-- DATOS INICIALES
-- ─────────────────────────────────────────
INSERT OR IGNORE INTO config (clave, valor, descripcion) VALUES
    ('nombre_negocio', 'Pensión El Refugio de la Brisa', 'Nombre del negocio'),
    ('moneda', 'Bs', 'Símbolo de moneda'),
    ('telefono', '', 'Teléfono del negocio'),
    ('direccion', '', 'Dirección del negocio'),
    ('impuesto', '0', 'Porcentaje de impuesto'),
    ('propina_sugerida', '10', 'Propina sugerida en %');

INSERT OR IGNORE INTO categorias (nombre, icono) VALUES
    ('Desayuno', '🌅'),
    ('Almuerzo', '🍱'),
    ('Cena', '🌙'),
    ('Bebidas', '🥤'),
    ('Postres', '🍮'),
    ('Extras', '➕');
