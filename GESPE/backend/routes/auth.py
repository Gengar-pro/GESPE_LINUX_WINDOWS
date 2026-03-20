from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from db.database import get_db
from auth import verify_password, create_token, get_current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: dict

@router.post("/login")
async def login(form: OAuth2PasswordRequestForm = Depends(), db=Depends(get_db)):
    row = await (await db.execute(
        "SELECT id, username, email, password_hash, rol, activo FROM usuarios WHERE username=? OR email=?",
        (form.username, form.username)
    )).fetchone()

    if not row or not verify_password(form.password, row["password_hash"]):
        raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")

    if not row["activo"]:
        raise HTTPException(status_code=403, detail="Usuario inactivo")

    token = create_token({"sub": str(row["id"]), "rol": row["rol"], "username": row["username"]})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": row["id"],
            "username": row["username"],
            "email": row["email"],
            "rol": row["rol"],
        }
    }

@router.get("/me")
async def me(user=Depends(get_current_user), db=Depends(get_db)):
    row = await (await db.execute(
        "SELECT id, username, email, rol, activo, created_at FROM usuarios WHERE id=?",
        (user["id"],)
    )).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return dict(row)
