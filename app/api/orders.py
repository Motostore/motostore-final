# app/api/orders.py
#
# ÓRDENES pagadas con la wallet.
# Regla clave:
#   - Si el usuario NO tiene saldo suficiente -> 400 "Saldo insuficiente en la wallet"
#   - Si tiene saldo suficiente -> se descuenta y se crea la orden

from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app import models

router = APIRouter()


# ----------------- Schemas Pydantic ----------------- #

class OrderCreate(BaseModel):
    user_id: int = Field(..., description="ID del usuario que compra")
    total_amount: float = Field(..., gt=0, description="Total a cobrar de la wallet")
    note: Optional[str] = Field(None, description="Nota opcional sobre la orden")


class OrderRead(BaseModel):
    id: int
    user_id: int
    total_amount: float
    status: str
    note: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True  # Pydantic v2


# ----------------- Endpoints ----------------- #

@router.post("", response_model=OrderRead)
def create_order(order_in: OrderCreate, db: Session = Depends(get_db)):
    """
    Crea una orden de compra pagada con la wallet.

    Lógica:
      - Busca al usuario
      - Si no existe -> 404
      - Si balance < total_amount -> 400 "Saldo insuficiente en la wallet"
      - Si balance >= total_amount:
          - Descuenta el saldo
          - Crea Order
          - Registra WalletTransaction de tipo PURCHASE
    """
    user = db.query(models.User).filter(models.User.id == order_in.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    if user.balance is None:
        user.balance = 0.0

    if user.balance < order_in.total_amount:
        raise HTTPException(status_code=400, detail="Saldo insuficiente en la wallet")

    # 1) Descontar saldo
    user.balance -= order_in.total_amount
    db.commit()
    db.refresh(user)

    # 2) Crear la orden
    order = models.Order(
        user_id=order_in.user_id,
        total_amount=order_in.total_amount,
        status="PAID",
        note=order_in.note,
    )
    db.add(order)
    db.commit()
    db.refresh(order)

    # 3) Registrar el movimiento en la wallet
    tx = models.WalletTransaction(
        user_id=order_in.user_id,
        amount=-order_in.total_amount,  # negativo porque es salida
        type="PURCHASE",
        note=f"Compra (order #{order.id})",
    )
    db.add(tx)
    db.commit()
    db.refresh(tx)

    return order


@router.get("", response_model=List[OrderRead])
def list_orders(
    user_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """
    Lista órdenes.
    - Si envías ?user_id=... filtra por usuario.
    - Si no, devuelve todas.
    """
    query = db.query(models.Order)
    if user_id is not None:
        query = query.filter(models.Order.user_id == user_id)

    return query.order_by(models.Order.created_at.desc()).all()


