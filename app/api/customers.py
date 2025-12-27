# app/api/customers.py
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from sqlalchemy.orm import Session

from app.core.database import get_db
from app import models

router = APIRouter()


# ---------- Esquemas Pydantic ---------- #

class CustomerBase(BaseModel):
    name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    document_id: Optional[str] = None
    address: Optional[str] = None
    active: bool = True


class CustomerCreate(CustomerBase):
    pass


class CustomerUpdate(CustomerBase):
    pass


class CustomerRead(CustomerBase):
    id: int

    class Config:
        from_attributes = True


# ---------- Endpoints ---------- #

# GET /api/v1/customers
@router.get("", response_model=List[CustomerRead])
def list_customers(db: Session = Depends(get_db)):
    return db.query(models.Customer).all()


# GET /api/v1/customers/{customer_id}
@router.get("/{customer_id}", response_model=CustomerRead)
def get_customer(customer_id: int, db: Session = Depends(get_db)):
    customer = (
        db.query(models.Customer)
        .filter(models.Customer.id == customer_id)
        .first()
    )
    if not customer:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return customer


# POST /api/v1/customers
@router.post("", response_model=CustomerRead)
def create_customer(customer_in: CustomerCreate, db: Session = Depends(get_db)):
    customer = models.Customer(**customer_in.dict())
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


# PUT /api/v1/customers/{customer_id}
@router.put("/{customer_id}", response_model=CustomerRead)
def update_customer(
    customer_id: int,
    customer_in: CustomerUpdate,
    db: Session = Depends(get_db),
):
    customer = (
        db.query(models.Customer)
        .filter(models.Customer.id == customer_id)
        .first()
    )
    if not customer:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    for field, value in customer_in.dict().items():
        setattr(customer, field, value)

    db.commit()
    db.refresh(customer)
    return customer


# DELETE /api/v1/customers/{customer_id}
@router.delete("/{customer_id}")
def delete_customer(customer_id: int, db: Session = Depends(get_db)):
    customer = (
        db.query(models.Customer)
        .filter(models.Customer.id == customer_id)
        .first()
    )
    if not customer:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    db.delete(customer)
    db.commit()
    return {"message": "Cliente eliminado"}
