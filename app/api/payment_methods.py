from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models import PaymentMethod

router = APIRouter()

# =======================
# 1. ESQUEMAS (Pydantic)
# =======================
# Definen qué datos esperamos recibir del Frontend y qué devolvemos

class PaymentMethodBase(BaseModel):
    name: str
    type: str
    # Campos opcionales (coinciden con el modelo de base de datos)
    bank_name: Optional[str] = None
    bank_code: Optional[str] = None
    account_number: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    id_number: Optional[str] = None
    address: Optional[str] = None

class PaymentMethodResponse(PaymentMethodBase):
    id: int
    is_active: bool

    class Config:
        from_attributes = True # Permite leer desde el modelo SQLAlchemy

# =======================
# 2. RUTAS (CRUD)
# =======================

# GET: Listar todos los métodos activos
@router.get("/", response_model=List[PaymentMethodResponse])
def get_payment_methods(db: Session = Depends(get_db)):
    return db.query(PaymentMethod).filter(PaymentMethod.is_active == True).all()

# POST: Crear un nuevo método
@router.post("/", response_model=PaymentMethodResponse, status_code=status.HTTP_201_CREATED)
def create_payment_method(method: PaymentMethodBase, db: Session = Depends(get_db)):
    # Creamos la instancia del modelo de BD con los datos recibidos
    new_method = PaymentMethod(**method.dict())
    db.add(new_method)
    db.commit()
    db.refresh(new_method)
    return new_method

# PUT: Editar un método existente
@router.put("/{method_id}", response_model=PaymentMethodResponse)
def update_payment_method(method_id: int, method: PaymentMethodBase, db: Session = Depends(get_db)):
    # Buscamos el método por ID
    db_method = db.query(PaymentMethod).filter(PaymentMethod.id == method_id).first()
    if not db_method:
        raise HTTPException(status_code=404, detail="Método de pago no encontrado")
    
    # Actualizamos los campos
    for key, value in method.dict().items():
        setattr(db_method, key, value)
    
    db.commit()
    db.refresh(db_method)
    return db_method

# DELETE: Borrar un método
@router.delete("/{method_id}")
def delete_payment_method(method_id: int, db: Session = Depends(get_db)):
    db_method = db.query(PaymentMethod).filter(PaymentMethod.id == method_id).first()
    if not db_method:
        raise HTTPException(status_code=404, detail="Método de pago no encontrado")
    
    # Lo borramos de la base de datos
    db.delete(db_method)
    db.commit()
    return {"message": "Método eliminado correctamente"}
