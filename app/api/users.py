import sys
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.core.database import get_db
from app import models

# ⚠️ TRUCO PARA EVITAR CRASH: No importamos auth aquí arriba
router = APIRouter()

# ---------- Esquemas ---------- #

class UserRead(BaseModel):
    id: int
    name: Optional[str] = "Sin Nombre"
    email: EmailStr
    username: str
    role: str          
    is_superuser: bool
    balance: float
    cedula: Optional[str] = None
    phone: Optional[str] = None
    telefono: Optional[str] = None 
    
    # 👇 NUEVOS CAMPOS PARA MONITOREO 👇
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


# ---------- Endpoints ---------- #

@router.get("", response_model=List[UserRead])
def get_all_users(db: Session = Depends(get_db)):
    # Ordenamos por ID para que los nuevos salgan al final (o al principio si prefieres .desc())
    users = db.query(models.User).order_by(models.User.id.desc()).all()
    return users


@router.get("/{user_id}", response_model=UserRead)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user


# 👇👇 LÓGICA DE ACTUALIZACIÓN BLINDADA 👇👇

@router.put("/{user_id}") 
def update_user(
    user_id: int, 
    user_in: UserUpdate, 
    db: Session = Depends(get_db),
):
    """
    PUT /api/v1/users/{user_id}
    """
    print(f"🚀 RECIBIDA PETICIÓN PUT PARA USER ID: {user_id}")
    print(f"📦 DATOS: {user_in}")

    # 1. IMPORTACIÓN LOCAL (Rompe el círculo vicioso)
    try:
        from app.api.auth import get_current_user
    except ImportError as e:
        print(f"❌ ERROR IMPORTANDO AUTH: {e}")
        # No lanzamos error aquí para no romper la ejecución si solo falta una dependencia circular
        pass

    try:
        # 2. BUSCAR USUARIO
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        # 3. ACTUALIZAR CAMPOS
        if user_in.name:
            user.name = user_in.name
        
        if user_in.email:
             # Validación simple de duplicados
            existing = db.query(models.User).filter(models.User.email == user_in.email).first()
            if existing and existing.id != user_id:
                 raise HTTPException(status_code=400, detail="Email ya registrado")
            user.email = user_in.email

        # Teléfono (Mapeo doble para compatibilidad)
        val_phone = user_in.phone or user_in.telefono
        if val_phone:
            user.phone = str(val_phone)
            # user.telefono = str(val_phone) # Descomentar si existe esa columna en models.py

        # Cédula (Mapeo doble y limpieza)
        val_cedula = user_in.cedula or user_in.dni
        if val_cedula:
            try:
                # Intenta limpiar y guardar
                # Si tu columna es String en la BD, usa str(val_cedula) directamente
                # Si es Integer, usa la limpieza:
                # clean = ''.join(filter(str.isdigit, str(val_cedula)))
                # if clean: user.cedula = int(clean)
                
                user.cedula = str(val_cedula) # Asumimos String para mayor seguridad
            except:
                pass

        db.commit()
        db.refresh(user)
        print("✅ USUARIO ACTUALIZADO CON ÉXITO")
        return user

    except Exception as e:
        print(f"🔥 ERROR CRÍTICO EN UPDATE_USER: {e}")
        raise HTTPException(status_code=500, detail=f"Error del servidor: {str(e)}")