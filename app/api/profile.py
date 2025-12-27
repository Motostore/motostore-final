# app/api/users.py
#
# Endpoints de usuarios (solo lectura por ahora)
#
#   GET /api/v1/users           -> lista todos los usuarios
#   GET /api/v1/users/{user_id} -> detalle de un usuario
#
# No exponemos password. Incluimos: id, name, email, username, role,
# is_superuser y balance.

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app import models

router = APIRouter()


# ---------- Schemas ---------- #

class UserRead(BaseModel):
    id: int
    name: str
    email: str
    username: str
    role: str
    is_superuser: bool
    balance: float

    class Config:
        from_attributes = True  # Pydantic v2 (equivalente a orm_mode=True)


# ---------- Endpoints ---------- #

@router.get("", response_model=List[UserRead])
def list_users(db: Session = Depends(get_db)):
    """
    GET /api/v1/users

    Devuelve todos los usuarios de la tabla users.
    """
    users = db.query(models.User).order_by(models.User.id.asc()).all()
    return users


@router.get("/{user_id}", response_model=UserRead)
def get_user(user_id: int, db: Session = Depends(get_db)):
    """
    GET /api/v1/users/{user_id}
    """
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user

