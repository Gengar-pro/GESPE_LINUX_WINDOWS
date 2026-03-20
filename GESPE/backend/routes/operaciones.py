from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from db.database import get_db
from auth import get_current_user

router = APIRouter(tags=["operaciones"])

# ════════════════════════════════════════════════════
# MESAS
# ════════════════════════════════════════════════════
mesa_router = APIRouter(prefix="/api/mesas")

class MesaUpdate(BaseModel):
    estado: Optional[str] = None
    capacidad: Optional[int] = None
    zona: Optional[str] = None

@mesa_router.get("/")
async def listar_mesas(db=Depends(get_db), user=Depends(get_current_user)):
    rows = await (await db.execute("""
        SELECT m.*, 
               (SELECT COUNT(*) FROM pedidos p WHERE p.mesa_id=m.id AND p.estado NOT IN ('cerrado','anulado')) as pedidos_activos
        FROM mesas m ORDER BY m.numero
    """)).fetchall()
    return [dict(r) for r in rows]

@mesa_router.put("/{mid}")
async def actualizar_mesa(mid: int, data: MesaUpdate, db=Depends(get_db), user=Depends(get_current_user)):
    fields, values = [], []
    if data.estado   is not None: fields.append("estado=?");   values.append(data.estado)
    if data.capacidad is not None: fields.append("capacidad=?"); values.append(data.capacidad)
    if data.zona     is not None: fields.append("zona=?");     values.append(data.zona)
    if not fields:
        raise HTTPException(status_code=400, detail="Nada que actualizar")
    fields.append("updated_at=datetime('now','localtime')")
    values.append(mid)
    await db.execute(f"UPDATE mesas SET {', '.join(fields)} WHERE id=?", values)
    await db.commit()
    return {"message": "Mesa actualizada"}

@mesa_router.post("/")
async def crear_mesa(numero: int, capacidad: int = 4, zona: str = "salon",
                     db=Depends(get_db), user=Depends(get_current_user)):
    try:
        await db.execute("INSERT INTO mesas (numero, capacidad, zona) VALUES (?,?,?)", (numero, capacidad, zona))
        await db.commit()
        return {"message": "Mesa creada"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ════════════════════════════════════════════════════
# COMBOS / MENÚ
# ════════════════════════════════════════════════════
combo_router = APIRouter(prefix="/api/combos")

class ComboCreate(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    precio: float
    categoria_id: Optional[int] = None
    disponible: int = 1

class ComboUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    precio: Optional[float] = None
    categoria_id: Optional[int] = None
    disponible: Optional[int] = None

@combo_router.get("/")
async def listar_combos(disponible: Optional[int] = None, db=Depends(get_db), user=Depends(get_current_user)):
    if disponible is not None:
        rows = await (await db.execute("""
            SELECT c.*, cat.nombre as categoria_nombre, cat.icono as categoria_icono
            FROM combos c LEFT JOIN categorias cat ON c.categoria_id=cat.id
            WHERE c.disponible=? ORDER BY cat.nombre, c.nombre
        """, (disponible,))).fetchall()
    else:
        rows = await (await db.execute("""
            SELECT c.*, cat.nombre as categoria_nombre, cat.icono as categoria_icono
            FROM combos c LEFT JOIN categorias cat ON c.categoria_id=cat.id
            ORDER BY cat.nombre, c.nombre
        """)).fetchall()
    return [dict(r) for r in rows]

@combo_router.get("/categorias")
async def listar_categorias(db=Depends(get_db), user=Depends(get_current_user)):
    rows = await (await db.execute("SELECT * FROM categorias WHERE activo=1 ORDER BY nombre")).fetchall()
    return [dict(r) for r in rows]

@combo_router.post("/")
async def crear_combo(data: ComboCreate, db=Depends(get_db), user=Depends(get_current_user)):
    await db.execute(
        "INSERT INTO combos (nombre, descripcion, precio, categoria_id, disponible) VALUES (?,?,?,?,?)",
        (data.nombre, data.descripcion, data.precio, data.categoria_id, data.disponible)
    )
    await db.commit()
    row = await (await db.execute("SELECT last_insert_rowid() as id")).fetchone()
    return {"id": row["id"], "message": "Combo creado"}

@combo_router.put("/{cid}")
async def actualizar_combo(cid: int, data: ComboUpdate, db=Depends(get_db), user=Depends(get_current_user)):
    fields, values = [], []
    for k, v in data.dict(exclude_none=True).items():
        fields.append(f"{k}=?")
        values.append(v)
    if not fields:
        raise HTTPException(status_code=400, detail="Nada que actualizar")
    values.append(cid)
    await db.execute(f"UPDATE combos SET {', '.join(fields)} WHERE id=?", values)
    await db.commit()
    return {"message": "Actualizado"}

@combo_router.delete("/{cid}")
async def eliminar_combo(cid: int, db=Depends(get_db), user=Depends(get_current_user)):
    await db.execute("UPDATE combos SET disponible=0 WHERE id=?", (cid,))
    await db.commit()
    return {"message": "Desactivado"}

# ════════════════════════════════════════════════════
# PEDIDOS / POS
# ════════════════════════════════════════════════════
pedido_router = APIRouter(prefix="/api/pedidos")

class PedidoItem(BaseModel):
    combo_id: int
    cantidad: int = 1
    notas: Optional[str] = None

class PedidoCreate(BaseModel):
    mesa_id: int
    items: List[PedidoItem]
    notas: Optional[str] = None

class ItemAdd(BaseModel):
    combo_id: int
    cantidad: int = 1
    notas: Optional[str] = None

@pedido_router.get("/")
async def listar_pedidos(estado: Optional[str] = None, db=Depends(get_db), user=Depends(get_current_user)):
    q = """
        SELECT p.*, m.numero as mesa_numero, u.username as mesero
        FROM pedidos p
        LEFT JOIN mesas m ON p.mesa_id = m.id
        LEFT JOIN usuarios u ON p.usuario_id = u.id
    """
    params = []
    if estado:
        q += " WHERE p.estado=?"
        params.append(estado)
    q += " ORDER BY p.created_at DESC LIMIT 100"
    rows = await (await db.execute(q, params)).fetchall()
    return [dict(r) for r in rows]

@pedido_router.get("/{pid}")
async def obtener_pedido(pid: int, db=Depends(get_db), user=Depends(get_current_user)):
    pedido = await (await db.execute("""
        SELECT p.*, m.numero as mesa_numero, u.username as mesero
        FROM pedidos p
        LEFT JOIN mesas m ON p.mesa_id = m.id
        LEFT JOIN usuarios u ON p.usuario_id = u.id
        WHERE p.id=?
    """, (pid,))).fetchone()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")

    items = await (await db.execute("""
        SELECT pi.*, c.nombre as combo_nombre
        FROM pedido_items pi JOIN combos c ON pi.combo_id=c.id
        WHERE pi.pedido_id=?
    """, (pid,))).fetchall()
    result = dict(pedido)
    result["items"] = [dict(i) for i in items]
    return result

@pedido_router.post("/")
async def crear_pedido(data: PedidoCreate, db=Depends(get_db), user=Depends(get_current_user)):
    total = 0
    items_data = []
    for item in data.items:
        combo = await (await db.execute("SELECT precio FROM combos WHERE id=? AND disponible=1", (item.combo_id,))).fetchone()
        if not combo:
            raise HTTPException(status_code=404, detail=f"Combo {item.combo_id} no disponible")
        precio = combo["precio"]
        total += precio * item.cantidad
        items_data.append((item.combo_id, item.cantidad, precio, item.notas))

    await db.execute(
        "INSERT INTO pedidos (mesa_id, usuario_id, total, notas) VALUES (?,?,?,?)",
        (data.mesa_id, user["id"], total, data.notas)
    )
    row = await (await db.execute("SELECT last_insert_rowid() as id")).fetchone()
    pedido_id = row["id"]

    for combo_id, cantidad, precio, notas in items_data:
        await db.execute(
            "INSERT INTO pedido_items (pedido_id, combo_id, cantidad, precio_unitario, notas) VALUES (?,?,?,?,?)",
            (pedido_id, combo_id, cantidad, precio, notas)
        )

    await db.execute("UPDATE mesas SET estado='ocupada', updated_at=datetime('now','localtime') WHERE id=?", (data.mesa_id,))
    await db.commit()
    return {"id": pedido_id, "total": total, "message": "Pedido creado"}

@pedido_router.put("/{pid}/estado")
async def cambiar_estado(pid: int, estado: str, db=Depends(get_db), user=Depends(get_current_user)):
    pedido = await (await db.execute("SELECT * FROM pedidos WHERE id=?", (pid,))).fetchone()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    await db.execute(
        "UPDATE pedidos SET estado=?, updated_at=datetime('now','localtime') WHERE id=?",
        (estado, pid)
    )
    if estado in ("cerrado", "anulado"):
        other = await (await db.execute(
            "SELECT COUNT(*) as c FROM pedidos WHERE mesa_id=? AND estado NOT IN ('cerrado','anulado') AND id!=?",
            (pedido["mesa_id"], pid)
        )).fetchone()
        if other["c"] == 0:
            await db.execute("UPDATE mesas SET estado='libre', updated_at=datetime('now','localtime') WHERE id=?", (pedido["mesa_id"],))
    await db.commit()
    return {"message": f"Estado actualizado a {estado}"}

@pedido_router.post("/{pid}/items")
async def agregar_item(pid: int, data: ItemAdd, db=Depends(get_db), user=Depends(get_current_user)):
    combo = await (await db.execute("SELECT precio FROM combos WHERE id=? AND disponible=1", (data.combo_id,))).fetchone()
    if not combo:
        raise HTTPException(status_code=404, detail="Combo no disponible")
    await db.execute(
        "INSERT INTO pedido_items (pedido_id, combo_id, cantidad, precio_unitario, notas) VALUES (?,?,?,?,?)",
        (pid, data.combo_id, data.cantidad, combo["precio"], data.notas)
    )
    subtotal = combo["precio"] * data.cantidad
    await db.execute(
        "UPDATE pedidos SET total=total+?, updated_at=datetime('now','localtime') WHERE id=?",
        (subtotal, pid)
    )
    await db.commit()
    return {"message": "Item agregado"}

@pedido_router.delete("/{pid}/items/{iid}")
async def quitar_item(pid: int, iid: int, db=Depends(get_db), user=Depends(get_current_user)):
    item = await (await db.execute("SELECT * FROM pedido_items WHERE id=? AND pedido_id=?", (iid, pid))).fetchone()
    if not item:
        raise HTTPException(status_code=404, detail="Item no encontrado")
    subtotal = item["precio_unitario"] * item["cantidad"]
    await db.execute("DELETE FROM pedido_items WHERE id=?", (iid,))
    await db.execute(
        "UPDATE pedidos SET total=MAX(0,total-?), updated_at=datetime('now','localtime') WHERE id=?",
        (subtotal, pid)
    )
    await db.commit()
    return {"message": "Item eliminado"}

# Registrar todos los sub-routers
router.include_router(mesa_router)
router.include_router(combo_router)
router.include_router(pedido_router)
