from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from db.database import get_db
from auth import get_current_user

router = APIRouter(prefix="/api/pensionados", tags=["pensionados"])

class PensionadoCreate(BaseModel):
    nombre: str
    apellido: str
    ci: Optional[str] = None
    telefono: Optional[str] = None
    direccion: Optional[str] = None
    tipo_pension: str = "completa"
    precio_mensual: float = 0
    notas: Optional[str] = None

class PensionadoUpdate(BaseModel):
    nombre: Optional[str] = None
    apellido: Optional[str] = None
    ci: Optional[str] = None
    telefono: Optional[str] = None
    direccion: Optional[str] = None
    tipo_pension: Optional[str] = None
    precio_mensual: Optional[float] = None
    activo: Optional[int] = None
    notas: Optional[str] = None

class CuponeraCreate(BaseModel):
    pensionado_id: int
    mes: int
    anio: int
    total_cupones: int = 30

class UsarCupon(BaseModel):
    cuponera_id: int
    tipo_comida: str = "almuerzo"

# ── Pensionados ──────────────────────────────────────────────
@router.get("/")
async def listar(activo: Optional[int] = None, db=Depends(get_db), user=Depends(get_current_user)):
    if activo is not None:
        rows = await (await db.execute(
            "SELECT * FROM pensionados WHERE activo=? ORDER BY apellido, nombre", (activo,)
        )).fetchall()
    else:
        rows = await (await db.execute(
            "SELECT * FROM pensionados ORDER BY apellido, nombre"
        )).fetchall()
    return [dict(r) for r in rows]

@router.get("/{pid}")
async def obtener(pid: int, db=Depends(get_db), user=Depends(get_current_user)):
    row = await (await db.execute("SELECT * FROM pensionados WHERE id=?", (pid,))).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Pensionado no encontrado")
    return dict(row)

@router.post("/")
async def crear(data: PensionadoCreate, db=Depends(get_db), user=Depends(get_current_user)):
    try:
        await db.execute("""
            INSERT INTO pensionados (nombre, apellido, ci, telefono, direccion, tipo_pension, precio_mensual, notas)
            VALUES (?,?,?,?,?,?,?,?)
        """, (data.nombre, data.apellido, data.ci, data.telefono, data.direccion,
              data.tipo_pension, data.precio_mensual, data.notas))
        await db.commit()
        row = await (await db.execute("SELECT last_insert_rowid() as id")).fetchone()
        return {"id": row["id"], "message": "Pensionado creado"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{pid}")
async def actualizar(pid: int, data: PensionadoUpdate, db=Depends(get_db), user=Depends(get_current_user)):
    fields, values = [], []
    for k, v in data.dict(exclude_none=True).items():
        fields.append(f"{k}=?")
        values.append(v)
    if not fields:
        raise HTTPException(status_code=400, detail="Nada que actualizar")
    values.append(pid)
    await db.execute(f"UPDATE pensionados SET {', '.join(fields)} WHERE id=?", values)
    await db.commit()
    return {"message": "Actualizado"}

@router.delete("/{pid}")
async def eliminar(pid: int, db=Depends(get_db), user=Depends(get_current_user)):
    await db.execute("UPDATE pensionados SET activo=0 WHERE id=?", (pid,))
    await db.commit()
    return {"message": "Desactivado"}

# ── Cuponeras ─────────────────────────────────────────────────
@router.get("/{pid}/cuponeras")
async def cuponeras_pensionado(pid: int, db=Depends(get_db), user=Depends(get_current_user)):
    rows = await (await db.execute(
        "SELECT * FROM cuponeras WHERE pensionado_id=? ORDER BY anio DESC, mes DESC", (pid,)
    )).fetchall()
    return [dict(r) for r in rows]

@router.post("/cuponeras")
async def crear_cuponera(data: CuponeraCreate, db=Depends(get_db), user=Depends(get_current_user)):
    try:
        await db.execute("""
            INSERT INTO cuponeras (pensionado_id, mes, anio, total_cupones)
            VALUES (?,?,?,?)
        """, (data.pensionado_id, data.mes, data.anio, data.total_cupones))
        await db.commit()
        row = await (await db.execute("SELECT last_insert_rowid() as id")).fetchone()
        return {"id": row["id"], "message": "Cuponera creada"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/cuponeras/usar")
async def usar_cupon(data: UsarCupon, db=Depends(get_db), user=Depends(get_current_user)):
    cup = await (await db.execute(
        "SELECT * FROM cuponeras WHERE id=? AND activo=1", (data.cuponera_id,)
    )).fetchone()
    if not cup:
        raise HTTPException(status_code=404, detail="Cuponera no encontrada o inactiva")
    if cup["cupones_usados"] >= cup["total_cupones"]:
        raise HTTPException(status_code=400, detail="Cuponera sin cupones disponibles")

    await db.execute(
        "UPDATE cuponeras SET cupones_usados = cupones_usados + 1 WHERE id=?",
        (data.cuponera_id,)
    )
    await db.execute(
        "INSERT INTO uso_cuponera (cuponera_id, tipo_comida, usuario_id) VALUES (?,?,?)",
        (data.cuponera_id, data.tipo_comida, user["id"])
    )
    await db.commit()
    return {"message": "Cupón registrado", "usados": cup["cupones_usados"] + 1}

@router.get("/cuponeras/all")
async def todas_cuponeras(db=Depends(get_db), user=Depends(get_current_user)):
    rows = await (await db.execute("""
        SELECT c.*, p.nombre || ' ' || p.apellido as pensionado_nombre
        FROM cuponeras c
        JOIN pensionados p ON c.pensionado_id = p.id
        ORDER BY c.anio DESC, c.mes DESC
    """)).fetchall()
    return [dict(r) for r in rows]
