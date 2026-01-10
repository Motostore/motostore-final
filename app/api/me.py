# app/api/me.py
#
# Perfil del usuario actual basado en JWT (Authorization: Bearer <token>)
# - GET /api/v1/me              -> devuelve el usuario logueado (DATOS FRESCOS)
# - GET /api/v1/me?user_id=2    -> (solo SUPERUSER) devuelve el usuario indicado
#
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr

from app.core.database import get_db
from app import models
from app.api.auth import get_current_user

router = APIRouter()


class MeUserView(BaseModel):
    id: int
    name: str = "Sin Nombre"
    email: EmailStr
    username: str
    role: str
    is_superuser: bool
    balance: float

    # ✅ campos extra que existen en tu tabla
    is_active: Optional[bool] = True
    full_name: Optional[str] = None
    cedula: Optional[str] = None
    telefono: Optional[str] = None

    class Config:
        from_attributes = True  # Pydantic v2


@router.get("", response_model=MeUserView)
def get_me(
    user_id: Optional[int] = Query(
        default=None,
        description="(Solo SUPERUSER) ID de usuario a consultar. Si no se envía, devuelve el usuario logueado.",
    ),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    # ✅ CASO 1: Si no piden user_id, devolvemos el usuario logueado PERO ACTUALIZADO
    if user_id is None:
        # 🔥 EL TRUCO: Consultamos la BD de nuevo para obtener el saldo real en este segundo
        fresh_user = db.query(models.User).filter(models.User.id == current_user.id).first()
        return fresh_user

    # ✅ CASO 2: Si piden otro user_id, solo permitir si es superuser
    if not getattr(current_user, "is_superuser", False):
        # Si no es admin, ignoramos el user_id y devolvemos su propio perfil actualizado
        fresh_user = db.query(models.User).filter(models.User.id == current_user.id).first()
        return fresh_user

    # ✅ CASO 3: Es Superuser buscando a otro usuario
    user = db.query(models.User).filter(models.User.id == int(user_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    return user