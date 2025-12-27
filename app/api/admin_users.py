# app/api/admin_users.py
#
# Administración de usuarios (equivalente a UserAdminController).
#
# Rutas reales (porque en main.py usas prefix="/api/v1/admin/users"):
#
#   GET    /api/v1/admin/users               -> list_users
#   GET    /api/v1/admin/users/{user_id}     -> get_user_admin
#   POST   /api/v1/admin/users               -> create_user_admin
#   PUT    /api/v1/admin/users/{user_id}     -> update_user_admin
#   DELETE /api/v1/admin/users/{user_id}     -> delete_user_admin
#
# ⚠️ Todas requieren actor_id=... (SUPERUSER o ADMIN)

from typing import List, Optional, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app import models

router = APIRouter()

# ---- ROLES EXACTOS DEL FRONTEND ---- #

AllowedRole = Literal[
    "SUPERUSER",
    "ADMIN",
    "DISTRIBUTOR",
    "RESELLER",
    "TAQUILLA",
    "CLIENT",
]

VALID_ROLES = {
    "SUPERUSER",
    "ADMIN",
    "DISTRIBUTOR",
    "RESELLER",
    "TAQUILLA",
    "CLIENT",
}


def normalize_role(r: str) -> str:
    if not r:
        return "CLIENT"
    r = r.strip().upper()
    if r.startswith("ROLE_"):
        r = r[5:]
    return r


def require_valid_role(role: str) -> str:
    role = normalize_role(role)
    if role not in VALID_ROLES:
        raise HTTPException(400, f"Rol inválido: {role}. Permitidos: {sorted(VALID_ROLES)}")
    return role


def get_actor(db: Session, actor_id: int) -> models.User:
    actor = db.query(models.User).filter(models.User.id == actor_id).first()
    if not actor:
        raise HTTPException(404, "Actor no encontrado")
    return actor


def require_admin(actor: models.User):
    role = normalize_role(actor.role)
    if role not in {"SUPERUSER", "ADMIN"}:
        raise HTTPException(403, "No tienes permisos para administrar usuarios")


# -------- Schemas -------- #

class AdminUserRead(BaseModel):
    id: int
    name: str
    email: EmailStr
    username: str
    role: str
    is_superuser: bool
    balance: float

    class Config:
        from_attributes = True


class AdminUserCreate(BaseModel):
    name: str
    email: EmailStr
    username: str
    password: str = Field(..., min_length=4)
    role: AllowedRole = "CLIENT"
    is_superuser: bool = False
    balance: float = 0.0


class AdminUserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    password: Optional[str] = Field(None, min_length=4)
    role: Optional[AllowedRole] = None
    is_superuser: Optional[bool] = None
    balance: Optional[float] = None


# -------- Endpoints -------- #

@router.get("", response_model=List[AdminUserRead])
def list_users(
    actor_id: int = Query(...),
    role: Optional[str] = Query(None, description="Filtrar por rol"),
    db: Session = Depends(get_db),
):
    actor = get_actor(db, actor_id)
    require_admin(actor)

    q = db.query(models.User)

    if role:
        q = q.filter(models.User.role == require_valid_role(role))

    return q.order_by(models.User.id.asc()).all()


@router.get("/{user_id}", response_model=AdminUserRead)
def get_user_admin(
    user_id: int,
    actor_id: int = Query(...),
    db: Session = Depends(get_db),
):
    actor = get_actor(db, actor_id)
    require_admin(actor)

    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(404, "Usuario no encontrado")

    return user


@router.post("", response_model=AdminUserRead)
def create_user_admin(
    data: AdminUserCreate,
    actor_id: int = Query(...),
    db: Session = Depends(get_db),
):
    actor = get_actor(db, actor_id)
    require_admin(actor)

    # email único
    if db.query(models.User).filter(models.User.email == data.email).first():
        raise HTTPException(400, "El correo ya está en uso")

    # username único
    if db.query(models.User).filter(models.User.username == data.username).first():
        raise HTTPException(400, "El username ya está en uso")

    user = models.User(
        name=data.name,
        email=data.email,
        username=data.username,
        password=data.password,
        role=require_valid_role(data.role),
        is_superuser=data.is_superuser,
        balance=data.balance,
    )

    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.put("/{user_id}", response_model=AdminUserRead)
def update_user_admin(
    user_id: int,
    data: AdminUserUpdate,
    actor_id: int = Query(...),
    db: Session = Depends(get_db),
):
    actor = get_actor(db, actor_id)
    require_admin(actor)

    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(404, "Usuario no encontrado")

    update = data.model_dump(exclude_unset=True)

    # Validación email único
    if "email" in update and update["email"] != user.email:
        if db.query(models.User).filter(models.User.email == update["email"]).first():
            raise HTTPException(400, "El correo ya está en uso")

    # Validación username único
    if "username" in update and update["username"] != user.username:
        if db.query(models.User).filter(models.User.username == update["username"]).first():
            raise HTTPException(400, "El username ya está en uso")

    # Validación rol
    if "role" in update and update["role"]:
        update["role"] = require_valid_role(update["role"])

    for field, value in update.items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)
    return user


@router.delete("/{user_id}")
def delete_user_admin(
    user_id: int,
    actor_id: int = Query(...),
    db: Session = Depends(get_db),
):
    actor = get_actor(db, actor_id)
    require_admin(actor)

    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(404, "Usuario no encontrado")

    db.delete(user)
    db.commit()
    return {"message": "Usuario eliminado correctamente"}

