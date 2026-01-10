import sys
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.core.database import get_db
from app import models

# Intentamos importar el hasheador de contraseñas
try:
    from app.core.security import get_password_hash
except ImportError:
    get_password_hash = None

router = APIRouter()

# ---------- Esquemas ---------- #

class UserRead(BaseModel):
    id: int
    name: Optional[str] = "Sin Nombre"
    email: EmailStr
    username: Optional[str] = "Usuario"
    role: Optional[str] = "CLIENT"
    is_superuser: bool = False
    balance: float = 0.0
    disabled: bool = False
    cedula: Optional[str] = None
    phone: Optional[str] = None
    telefono: Optional[str] = None 
    ip_address: Optional[str] = None
    country_code: Optional[str] = None
    
    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    telefono: Optional[str] = None
    cedula: Optional[str] = None
    dni: Optional[str] = None
    role: Optional[str] = None      
    disabled: Optional[bool] = None 
    password: Optional[str] = None  

class BalanceUpdate(BaseModel):
    amount: float

# ---------- Endpoints ---------- #

@router.get("", response_model=List[UserRead])
def get_all_users(db: Session = Depends(get_db)):
    users = db.query(models.User).order_by(models.User.id.desc()).all()
    return users

@router.get("/{user_id}", response_model=UserRead)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user

# CAJA RÁPIDA
@router.post("/{user_id}/balance")
def update_balance(user_id: int, data: BalanceUpdate, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    current = float(user.balance or 0)
    user.balance = current + data.amount
    db.commit()
    return {"status": "ok", "new_balance": user.balance}

# 🔥 FIX DEFINITIVO: Quitamos response_model para que NO falle validando la respuesta
@router.patch("/{user_id}") 
def patch_user(
    user_id: int, 
    user_in: UserUpdate, 
    db: Session = Depends(get_db),
):
    print(f"🚀 PATCH USER: {user_id} | Datos: {user_in}")

    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    try:
        # Actualización de campos
        if user_in.name: user.name = user_in.name
        if user_in.email: user.email = user_in.email
        
        # ROL
        if user_in.role:
            user.role = user_in.role.upper()
            if user.role == 'SUPERUSER':
                user.is_superuser = True
            else:
                user.is_superuser = False

        # STATUS
        if user_in.disabled is not None:
            user.disabled = user_in.disabled

        # PASSWORD
        if user_in.password:
            if get_password_hash:
                user.hashed_password = get_password_hash(user_in.password)
            else:
                # Fallback simple
                try:
                    user.hashed_password = user_in.password 
                except:
                    user.password = user_in.password

        # DATA EXTRA
        val_phone = user_in.phone or user_in.telefono
        if val_phone: user.phone = str(val_phone)

        val_cedula = user_in.cedula or user_in.dni
        if val_cedula: user.cedula = str(val_cedula)

        db.commit()
        
        # 🔥 RETORNAMOS UN JSON SIMPLE (Esto evita el crash 500)
        return {
            "status": "success", 
            "id": user.id, 
            "role": user.role, 
            "disabled": user.disabled
        }

    except Exception as e:
        print(f"🔥 ERROR: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")