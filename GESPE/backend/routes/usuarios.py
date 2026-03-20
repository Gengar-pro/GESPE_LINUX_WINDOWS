from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from typing import Optional
from db.database import get_db
from auth import hash_password, get_current_user, require_admin

router = APIRouter(prefix="/api/usuarios", tags=["usuarios"])

class UsuarioCreate(BaseModel):
    username: str
    email: str
    password: str
    rol: str = "mesero"

class UsuarioUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
    rol: Optional[str] = None
    activo: Optional[int] = None

@router.get("/")
async def listar(db=Depends(get_db), user=Depends(require_admin)):
    rows = await (await db.execute(
        "SELECT id, username, email, rol, activo, created_at FROM usuarios ORDER BY id"
    )).fetchall()
    return [dict(r) for r in rows]

@router.post("/")
async def crear(data: UsuarioCreate, db=Depends(get_db), user=Depends(require_admin)):
    try:
        await db.execute(
            "INSERT INTO usuarios (username, email, password_hash, rol) VALUES (?, ?, ?, ?)",
            (data.username, data.email, hash_password(data.password), data.rol)
        )
        await db.commit()
        row = await (await db.execute("SELECT last_insert_rowid() as id")).fetchone()
        return {"id": row["id"], "message": "Usuario creado"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error: {str(e)}")

@router.put("/{uid}")
async def actualizar(uid: int, data: UsuarioUpdate, db=Depends(get_db), user=Depends(require_admin)):
    fields, values = [], []
    if data.username is not None: fields.append("username=?"); values.append(data.username)
    if data.email    is not None: fields.append("email=?");    values.append(data.email)
    if data.password is not None: fields.append("password_hash=?"); values.append(hash_password(data.password))
    if data.rol      is not None: fields.append("rol=?");      values.append(data.rol)
    if data.activo   is not None: fields.append("activo=?");   values.append(data.activo)
    if not fields:
        raise HTTPException(status_code=400, detail="Nada que actualizar")
    values.append(uid)
    await db.execute(f"UPDATE usuarios SET {', '.join(fields)} WHERE id=?", values)
    await db.commit()
    return {"message": "Actualizado"}

@router.delete("/{uid}")
async def eliminar(uid: int, db=Depends(get_db), user=Depends(require_admin)):
    await db.execute("UPDATE usuarios SET activo=0 WHERE id=?", (uid,))
    await db.commit()
    return {"message": "Desactivado"}
