from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from db.database import get_db
from auth import get_current_user, require_admin, require_cajero

router = APIRouter(tags=["administracion"])

# ════════════════════════════════════════════════════
# DASHBOARD
# ════════════════════════════════════════════════════
dash_router = APIRouter(prefix="/api/dashboard")

@dash_router.get("/")
async def dashboard(db=Depends(get_db), user=Depends(get_current_user)):
    # Mesas
    mesas_total    = (await (await db.execute("SELECT COUNT(*) as c FROM mesas")).fetchone())["c"]
    mesas_ocupadas = (await (await db.execute("SELECT COUNT(*) as c FROM mesas WHERE estado='ocupada'")).fetchone())["c"]
    # Pedidos hoy
    pedidos_hoy    = (await (await db.execute(
        "SELECT COUNT(*) as c FROM pedidos WHERE date(created_at)=date('now','localtime')"
    )).fetchone())["c"]
    pedidos_activos = (await (await db.execute(
        "SELECT COUNT(*) as c FROM pedidos WHERE estado NOT IN ('cerrado','anulado')"
    )).fetchone())["c"]
    # Ingresos hoy
    ingresos_hoy   = (await (await db.execute("""
        SELECT COALESCE(SUM(mc.monto),0) as total
        FROM movimientos_caja mc JOIN cajas ca ON mc.caja_id=ca.id
        WHERE mc.tipo='ingreso' AND date(mc.created_at)=date('now','localtime')
    """)).fetchone())["total"]
    # Stock bajo
    stock_bajo     = (await (await db.execute(
        "SELECT COUNT(*) as c FROM inventario WHERE cantidad <= stock_minimo AND stock_minimo > 0"
    )).fetchone())["c"]
    # Pensionados activos
    pensionados    = (await (await db.execute("SELECT COUNT(*) as c FROM pensionados WHERE activo=1")).fetchone())["c"]
    # Pedidos recientes
    recientes      = await (await db.execute("""
        SELECT p.id, p.estado, p.total, p.created_at, m.numero as mesa, u.username as mesero
        FROM pedidos p
        LEFT JOIN mesas m ON p.mesa_id=m.id
        LEFT JOIN usuarios u ON p.usuario_id=u.id
        ORDER BY p.created_at DESC LIMIT 8
    """)).fetchall()

    return {
        "mesas_total": mesas_total,
        "mesas_ocupadas": mesas_ocupadas,
        "pedidos_hoy": pedidos_hoy,
        "pedidos_activos": pedidos_activos,
        "ingresos_hoy": ingresos_hoy,
        "alertas_stock": stock_bajo,
        "pensionados_activos": pensionados,
        "pedidos_recientes": [dict(r) for r in recientes],
    }

# ════════════════════════════════════════════════════
# INVENTARIO
# ════════════════════════════════════════════════════
inv_router = APIRouter(prefix="/api/inventario")

class InvCreate(BaseModel):
    nombre: str
    categoria: str = "otros"
    cantidad: float = 0
    unidad: str = "unidad"
    precio_costo: float = 0
    stock_minimo: float = 0
    proveedor: Optional[str] = None

class InvUpdate(BaseModel):
    nombre: Optional[str] = None
    categoria: Optional[str] = None
    unidad: Optional[str] = None
    precio_costo: Optional[float] = None
    stock_minimo: Optional[float] = None
    proveedor: Optional[str] = None

class MovInv(BaseModel):
    inventario_id: int
    tipo: str  # entrada | salida | ajuste
    cantidad: float
    descripcion: Optional[str] = None

@inv_router.get("/")
async def listar_inv(db=Depends(get_db), user=Depends(get_current_user)):
    rows = await (await db.execute(
        "SELECT *, (cantidad <= stock_minimo AND stock_minimo > 0) as stock_critico FROM inventario ORDER BY nombre"
    )).fetchall()
    return [dict(r) for r in rows]

@inv_router.post("/")
async def crear_inv(data: InvCreate, db=Depends(get_db), user=Depends(get_current_user)):
    await db.execute("""
        INSERT INTO inventario (nombre, categoria, cantidad, unidad, precio_costo, stock_minimo, proveedor)
        VALUES (?,?,?,?,?,?,?)
    """, (data.nombre, data.categoria, data.cantidad, data.unidad,
          data.precio_costo, data.stock_minimo, data.proveedor))
    await db.commit()
    row = await (await db.execute("SELECT last_insert_rowid() as id")).fetchone()
    return {"id": row["id"], "message": "Producto creado"}

@inv_router.put("/{iid}")
async def actualizar_inv(iid: int, data: InvUpdate, db=Depends(get_db), user=Depends(get_current_user)):
    fields, values = [], []
    for k, v in data.dict(exclude_none=True).items():
        fields.append(f"{k}=?")
        values.append(v)
    if not fields:
        raise HTTPException(status_code=400, detail="Nada que actualizar")
    fields.append("updated_at=datetime('now','localtime')")
    values.append(iid)
    await db.execute(f"UPDATE inventario SET {', '.join(fields)} WHERE id=?", values)
    await db.commit()
    return {"message": "Actualizado"}

@inv_router.post("/movimiento")
async def mov_inventario(data: MovInv, db=Depends(get_db), user=Depends(get_current_user)):
    inv = await (await db.execute("SELECT * FROM inventario WHERE id=?", (data.inventario_id,))).fetchone()
    if not inv:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    if data.tipo == "entrada":
        nueva = inv["cantidad"] + data.cantidad
    elif data.tipo == "salida":
        nueva = max(0, inv["cantidad"] - data.cantidad)
    else:
        nueva = data.cantidad  # ajuste directo
    await db.execute(
        "UPDATE inventario SET cantidad=?, updated_at=datetime('now','localtime') WHERE id=?",
        (nueva, data.inventario_id)
    )
    await db.execute("""
        INSERT INTO movimientos_inventario (inventario_id, tipo, cantidad, descripcion, usuario_id)
        VALUES (?,?,?,?,?)
    """, (data.inventario_id, data.tipo, data.cantidad, data.descripcion, user["id"]))
    await db.commit()
    return {"message": "Movimiento registrado", "nueva_cantidad": nueva}

@inv_router.get("/movimientos")
async def listar_movimientos(db=Depends(get_db), user=Depends(get_current_user)):
    rows = await (await db.execute("""
        SELECT m.*, i.nombre as producto, u.username as usuario
        FROM movimientos_inventario m
        JOIN inventario i ON m.inventario_id=i.id
        LEFT JOIN usuarios u ON m.usuario_id=u.id
        ORDER BY m.created_at DESC LIMIT 100
    """)).fetchall()
    return [dict(r) for r in rows]

# ════════════════════════════════════════════════════
# CAJA
# ════════════════════════════════════════════════════
caja_router = APIRouter(prefix="/api/caja")

class AbrirCaja(BaseModel):
    saldo_inicial: float
    notas: Optional[str] = None

class MovCaja(BaseModel):
    tipo: str  # ingreso | egreso
    monto: float
    descripcion: str
    referencia: Optional[str] = None
    metodo_pago: str = "efectivo"

@caja_router.get("/actual")
async def caja_actual(db=Depends(get_db), user=Depends(get_current_user)):
    row = await (await db.execute(
        "SELECT * FROM cajas WHERE estado='abierta' ORDER BY id DESC LIMIT 1"
    )).fetchone()
    if not row:
        return {"caja": None, "mensaje": "No hay caja abierta"}
    caja = dict(row)
    # Calcular totales
    totales = await (await db.execute("""
        SELECT
            COALESCE(SUM(CASE WHEN tipo='ingreso' THEN monto ELSE 0 END),0) as total_ingresos,
            COALESCE(SUM(CASE WHEN tipo='egreso'  THEN monto ELSE 0 END),0) as total_egresos
        FROM movimientos_caja WHERE caja_id=?
    """, (caja["id"],))).fetchone()
    caja["total_ingresos"] = totales["total_ingresos"]
    caja["total_egresos"]  = totales["total_egresos"]
    caja["saldo_actual"]   = caja["saldo_inicial"] + totales["total_ingresos"] - totales["total_egresos"]
    return {"caja": caja}

@caja_router.post("/abrir")
async def abrir_caja(data: AbrirCaja, db=Depends(get_db), user=Depends(require_cajero)):
    open_caja = await (await db.execute("SELECT id FROM cajas WHERE estado='abierta'")).fetchone()
    if open_caja:
        raise HTTPException(status_code=400, detail="Ya hay una caja abierta")
    await db.execute(
        "INSERT INTO cajas (saldo_inicial, usuario_id, notas) VALUES (?,?,?)",
        (data.saldo_inicial, user["id"], data.notas)
    )
    await db.commit()
    return {"message": "Caja abierta"}

@caja_router.post("/cerrar")
async def cerrar_caja(db=Depends(get_db), user=Depends(require_cajero)):
    caja = await (await db.execute("SELECT * FROM cajas WHERE estado='abierta' ORDER BY id DESC LIMIT 1")).fetchone()
    if not caja:
        raise HTTPException(status_code=404, detail="No hay caja abierta")
    totales = await (await db.execute("""
        SELECT
            COALESCE(SUM(CASE WHEN tipo='ingreso' THEN monto ELSE 0 END),0) as ti,
            COALESCE(SUM(CASE WHEN tipo='egreso'  THEN monto ELSE 0 END),0) as te
        FROM movimientos_caja WHERE caja_id=?
    """, (caja["id"],))).fetchone()
    saldo_final = caja["saldo_inicial"] + totales["ti"] - totales["te"]
    await db.execute(
        "UPDATE cajas SET estado='cerrada', saldo_final=? WHERE id=?",
        (saldo_final, caja["id"])
    )
    await db.commit()
    return {"message": "Caja cerrada", "saldo_final": saldo_final}

@caja_router.post("/movimiento")
async def mov_caja(data: MovCaja, db=Depends(get_db), user=Depends(get_current_user)):
    caja = await (await db.execute("SELECT id FROM cajas WHERE estado='abierta' ORDER BY id DESC LIMIT 1")).fetchone()
    if not caja:
        raise HTTPException(status_code=400, detail="No hay caja abierta")
    await db.execute("""
        INSERT INTO movimientos_caja (caja_id, tipo, monto, descripcion, referencia, metodo_pago, usuario_id)
        VALUES (?,?,?,?,?,?,?)
    """, (caja["id"], data.tipo, data.monto, data.descripcion, data.referencia, data.metodo_pago, user["id"]))
    await db.commit()
    return {"message": "Movimiento registrado"}

@caja_router.get("/movimientos")
async def listar_mov_caja(db=Depends(get_db), user=Depends(get_current_user)):
    caja = await (await db.execute("SELECT id FROM cajas WHERE estado='abierta' ORDER BY id DESC LIMIT 1")).fetchone()
    if not caja:
        return []
    rows = await (await db.execute("""
        SELECT m.*, u.username FROM movimientos_caja m
        LEFT JOIN usuarios u ON m.usuario_id=u.id
        WHERE m.caja_id=? ORDER BY m.created_at DESC
    """, (caja["id"],))).fetchall()
    return [dict(r) for r in rows]

@caja_router.get("/historial")
async def historial_cajas(db=Depends(get_db), user=Depends(get_current_user)):
    rows = await (await db.execute("""
        SELECT c.*, u.username FROM cajas c LEFT JOIN usuarios u ON c.usuario_id=u.id
        ORDER BY c.created_at DESC LIMIT 30
    """)).fetchall()
    return [dict(r) for r in rows]

# ════════════════════════════════════════════════════
# PERSONAL
# ════════════════════════════════════════════════════
personal_router = APIRouter(prefix="/api/personal")

class PersonalCreate(BaseModel):
    nombre: str
    apellido: str
    ci: Optional[str] = None
    cargo: str = "mesero"
    telefono: Optional[str] = None
    email: Optional[str] = None
    sueldo: float = 0
    fecha_ingreso: Optional[str] = None
    notas: Optional[str] = None

class PersonalUpdate(BaseModel):
    nombre: Optional[str] = None
    apellido: Optional[str] = None
    ci: Optional[str] = None
    cargo: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None
    sueldo: Optional[float] = None
    activo: Optional[int] = None
    notas: Optional[str] = None

@personal_router.get("/")
async def listar_personal(db=Depends(get_db), user=Depends(get_current_user)):
    rows = await (await db.execute(
        "SELECT * FROM personal ORDER BY apellido, nombre"
    )).fetchall()
    return [dict(r) for r in rows]

@personal_router.post("/")
async def crear_personal(data: PersonalCreate, db=Depends(get_db), user=Depends(require_admin)):
    try:
        await db.execute("""
            INSERT INTO personal (nombre, apellido, ci, cargo, telefono, email, sueldo, fecha_ingreso, notas)
            VALUES (?,?,?,?,?,?,?,?,?)
        """, (data.nombre, data.apellido, data.ci, data.cargo, data.telefono,
              data.email, data.sueldo, data.fecha_ingreso, data.notas))
        await db.commit()
        row = await (await db.execute("SELECT last_insert_rowid() as id")).fetchone()
        return {"id": row["id"], "message": "Personal creado"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@personal_router.put("/{pid}")
async def actualizar_personal(pid: int, data: PersonalUpdate, db=Depends(get_db), user=Depends(require_admin)):
    fields, values = [], []
    for k, v in data.dict(exclude_none=True).items():
        fields.append(f"{k}=?")
        values.append(v)
    if not fields:
        raise HTTPException(status_code=400, detail="Nada que actualizar")
    values.append(pid)
    await db.execute(f"UPDATE personal SET {', '.join(fields)} WHERE id=?", values)
    await db.commit()
    return {"message": "Actualizado"}

@personal_router.delete("/{pid}")
async def eliminar_personal(pid: int, db=Depends(get_db), user=Depends(require_admin)):
    await db.execute("UPDATE personal SET activo=0 WHERE id=?", (pid,))
    await db.commit()
    return {"message": "Desactivado"}

# ════════════════════════════════════════════════════
# CONFIGURACIÓN
# ════════════════════════════════════════════════════
config_router = APIRouter(prefix="/api/config")

class ConfigUpdate(BaseModel):
    valor: str

@config_router.get("/")
async def listar_config(db=Depends(get_db), user=Depends(get_current_user)):
    rows = await (await db.execute("SELECT * FROM config ORDER BY clave")).fetchall()
    return {r["clave"]: r["valor"] for r in rows}

@config_router.put("/{clave}")
async def actualizar_config(clave: str, data: ConfigUpdate, db=Depends(get_db), user=Depends(require_admin)):
    await db.execute(
        "INSERT INTO config (clave, valor) VALUES (?,?) ON CONFLICT(clave) DO UPDATE SET valor=excluded.valor",
        (clave, data.valor)
    )
    await db.commit()
    return {"message": "Configuración actualizada"}

# Registrar todos
router.include_router(dash_router)
router.include_router(inv_router)
router.include_router(caja_router)
router.include_router(personal_router)
router.include_router(config_router)
