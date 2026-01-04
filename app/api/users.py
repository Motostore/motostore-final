from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.core.database import get_db
from app import models
# Importamos el validador de seguridad desde auth (asumiendo que el segundo archivo es app/api/auth.py)
from app.api.auth import get_current_user 

router = APIRouter()


# ---------- Esquema de salida (Lectura) ---------- #

class UserRead(BaseModel):
    id: int
    name: str
    email: EmailStr
    username: str
    role: str          
    is_superuser: bool
    balance: float
    # Agregamos estos campos para que el frontend los reciba si existen
    cedula: Optional[str] = None
    phone: Optional[str] = None
    telefono: Optional[str] = None 

    class Config:
        from_attributes = True  # Pydantic v2


# ---------- Esquema de Entrada (Edición) ---------- #
# 👇 ESTO ES NUEVO: Define qué datos permitimos editar
class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    telefono: Optional[str] = None
    cedula: Optional[str] = None # Recibimos string o numeros parseados
    dni: Optional[str] = None


# ---------- Endpoints ---------- #

@router.get("", response_model=List[UserRead])
def get_all_users(db: Session = Depends(get_db)):
    """
    GET /api/v1/users
    Devuelve TODOS los usuarios.
    """
    users = db.query(models.User).order_by(models.User.id.asc()).all()
    return users


@router.get("/{user_id}", response_model=UserRead)
def get_user(user_id: int, db: Session = Depends(get_db)):
    """
    GET /api/v1/users/{user_id}
    Devuelve un usuario por id.
    """
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user


# 👇👇 AQUÍ ESTÁ LA MAGIA QUE FALTABA 👇👇

@router.put("/{user_id}", response_model=UserRead)
def update_user(
    user_id: int, 
    user_in: UserUpdate, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user) # Seguridad: Token requerido
):
    """
    PUT /api/v1/users/{user_id}
    Actualiza datos del perfil (Nombre, Email, Teléfono, Cédula).
    """
    
    # 1. Buscar usuario en BD
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # 2. Seguridad: ¿Quién intenta editar?
    # Solo permitimos editar si eres el dueño de la cuenta O si eres Superuser
    if current_user.id != user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="No tienes permiso para editar este usuario")

    # 3. Actualizar campos (Solo si vienen en el JSON)
    if user_in.name is not None:
        user.name = user_in.name
    
    if user_in.email is not None:
        # Validar que el email no esté tomado por OTRO usuario
        existing_email = db.query(models.User).filter(models.User.email == user_in.email).first()
        if existing_email and existing_email.id != user_id:
             raise HTTPException(status_code=400, detail="Ese correo ya está registrado por otro usuario")
        user.email = user_in.email

    # Manejo flexible de telefono (phone o telefono)
    if user_in.phone is not None:
        user.phone = user_in.phone # Asumiendo que tu modelo tiene campo 'phone'
        # Si tu modelo usa 'telefono', descomenta la linea de abajo:
        # user.telefono = user_in.phone 
    elif user_in.telefono is not None:
        user.phone = user_in.telefono

    # Manejo flexible de cédula (cedula o dni)
    # Convertimos a string para guardar uniformemente
    if user_in.cedula is not None:
        user.cedula = str(user_in.cedula)
    elif user_in.dni is not None:
        user.cedula = str(user_in.dni)

    # 4. Guardar cambios
    db.commit()
    db.refresh(user)
    
    return user