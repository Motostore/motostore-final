from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.core.database import get_db
from app import models
from app.api.auth import get_current_user

router = APIRouter()

# --- Schemas ---
class WithdrawalRead(BaseModel):
    id: int
    user_id: int
    user_name: str
    amount: float # Vendrá negativo en BD, lo mostraremos positivo
    note: str
    created_at: datetime
    status: str # PENDING, DONE, REJECTED (Derivado del tipo de transacción)

    class Config:
        from_attributes = True

# --- Endpoints ---

@router.get("/pending", response_model=List[WithdrawalRead])
def get_pending_withdrawals(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Lista todas las solicitudes de retiro pendientes (Type = WITHDRAW_REQUEST).
    Solo Admin/Superuser.
    """
    if current_user.role not in ["SUPERUSER", "ADMIN"]:
        raise HTTPException(status_code=403, detail="Acceso denegado")

    # Buscamos transacciones tipo "WITHDRAW_REQUEST"
    txs = (
        db.query(models.WalletTransaction, models.User.username)
        .join(models.User, models.WalletTransaction.user_id == models.User.id)
        .filter(models.WalletTransaction.type == "WITHDRAW_REQUEST")
        .order_by(models.WalletTransaction.created_at.asc())
        .all()
    )

    results = []
    for tx, username in txs:
        results.append({
            "id": tx.id,
            "user_id": tx.user_id,
            "user_name": username,
            "amount": abs(tx.amount), # Mostramos positivo visualmente
            "note": tx.note,
            "created_at": tx.created_at,
            "status": "PENDING"
        })
    
    return results

@router.post("/{tx_id}/approve")
def approve_withdrawal(
    tx_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Aprueba el retiro. 
    Cambia el tipo de transacción de 'WITHDRAW_REQUEST' a 'WITHDRAW' (Confirmado).
    El saldo ya se descontó al solicitar, así que solo confirmamos el estado.
    """
    if current_user.role not in ["SUPERUSER", "ADMIN"]:
        raise HTTPException(status_code=403, detail="Acceso denegado")

    tx = db.query(models.WalletTransaction).filter(models.WalletTransaction.id == tx_id).first()
    
    if not tx or tx.type != "WITHDRAW_REQUEST":
        raise HTTPException(status_code=404, detail="Solicitud no encontrada o ya procesada")

    # Confirmamos el retiro
    tx.type = "WITHDRAW" 
    tx.note = f"{tx.note} (APROBADO por {current_user.username})"
    
    db.commit()
    return {"message": "Retiro marcado como pagado"}

@router.post("/{tx_id}/reject")
def reject_withdrawal(
    tx_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Rechaza el retiro y DEVUELVE el dinero al usuario.
    """
    if current_user.role not in ["SUPERUSER", "ADMIN"]:
        raise HTTPException(status_code=403, detail="Acceso denegado")

    tx = db.query(models.WalletTransaction).filter(models.WalletTransaction.id == tx_id).first()
    
    if not tx or tx.type != "WITHDRAW_REQUEST":
        raise HTTPException(status_code=404, detail="Solicitud no encontrada o ya procesada")

    # 1. Cambiamos estado a REJECTED (para historial) o lo borramos?
    # Mejor: Creamos una contra-transacción de reembolso para que quede registro
    amount_to_refund = abs(tx.amount)
    user = db.query(models.User).filter(models.User.id == tx.user_id).first()
    
    if user:
        user.balance += amount_to_refund
    
    # Marcamos la original como rechazada
    tx.type = "WITHDRAW_REJECTED"
    tx.note = f"{tx.note} (RECHAZADO por {current_user.username})"

    # Creamos el registro del reembolso
    refund_tx = models.WalletTransaction(
        user_id=tx.user_id,
        amount=amount_to_refund,
        type="REFUND",
        note=f"Reembolso de retiro #{tx.id}"
    )
    
    db.add(refund_tx)
    db.commit()
    
    return {"message": "Retiro rechazado y dinero devuelto al usuario"}