# app/api/users.py

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.core.database import get_db
from app import models

router = APIRouter()


# ---------- Esquema de salida ---------- #

class UserRead(BaseModel):
    id: int
    name: str
    email: EmailStr
    username: str
    role: str          # 👈 NUEVO: rol igual que en models.User
    is_superuser: bool
    balance: float

    class Config:
        from_attributes = True  # Pydantic v2


# ---------- Endpoints ---------- #

@router.get("", response_model=List[UserRead])
def get_all_users(db: Session = Depends(get_db)):
    """
    GET /api/v1/users
    Devuelve TODOS los usuarios reales de la BD.
    Incluye el superuser con su rol y saldo.
    """
    users = (
        db.query(models.User)
        .order_by(models.User.id.asc())
        .all()
    )
    return users


@router.get("/{user_id}", response_model=UserRead)
def get_user(user_id: int, db: Session = Depends(get_db)):
    """
    GET /api/v1/users/{user_id}
    Devuelve un usuario por id.
    """
    user = (
        db.query(models.User)
        .filter(models.User.id == user_id)
        .first()
    )
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user
