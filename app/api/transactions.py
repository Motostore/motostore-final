# app/api/transactions.py (COMPLETO Y SEGURO)

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session, aliased
from app.core.database import get_db
from app import models
# 👇 Importamos la seguridad estándar
from app.api.auth import get_current_user 

router = APIRouter()

# ==========================================
# 1. SCHEMAS
# ==========================================

class TransactionView(BaseModel):
    id: int
    user_id: int               # ID del dueño de la transacción
    username: Optional[str]    # Nombre del dueño (solo para reportes globales)
    type: str                  # deposit / withdraw / purchase / order / payment-xxx
    amount: float
    note: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ==========================================
# 2. HELPERS
# ==========================================

def _collect_transactions_for_user(db: Session, user: models.User) -> List[TransactionView]:
    out: List[TransactionView] = []
    
    user_id = user.id
    username = user.username

    # ---- WALLET ----
    wallet_tx = (
        db.query(models.WalletTransaction)
        .filter(models.WalletTransaction.user_id == user_id)
        .all()
    )

    for tx in wallet_tx:
        out.append(
            TransactionView(
                id=tx.id,
                user_id=user_id,
                username=username,
                type=(tx.type or "").lower(),
                amount=tx.amount,
                note=tx.note,
                created_at=tx.created_at or datetime.utcnow(),
            )
        )

    # ---- ORDERS ----
    orders = (
        db.query(models.Order)
        .filter(models.Order.user_id == user_id)
        .all()
    )

    for o in orders:
        out.append(
            TransactionView(
                id=o.id,
                user_id=user_id,
                username=username,
                type="order",
                amount=o.total_amount,
                note=o.note,
                created_at=o.created_at or datetime.utcnow(),
            )
        )

    # ---- PAYMENT REPORTS (Solicitudes de Recarga) ----
    reports = (
        db.query(models.PaymentReport)
        .filter(models.PaymentReport.user_id == user_id)
        .all()
    )

    for r in reports:
        out.append(
            TransactionView(
                id=r.id,
                user_id=user_id,
                username=username,
                type=f"payment-{(r.status or '').lower()}", # payment-pending, payment-approved...
                amount=r.amount,
                note=r.note,
                created_at=r.created_at or datetime.utcnow(),
            )
        )

    return out


# ==========================================
# 3. ENDPOINTS
# ==========================================

@router.get("", response_model=List[TransactionView])
def get_my_transactions(
    db: Session = Depends(get_db),
    # 🔒 OBTENEMOS EL USUARIO DESDE EL TOKEN (Seguro)
    current_user: models.User = Depends(get_current_user) 
):
    """
    Devuelve TODOS los movimientos financieros del usuario LOGUEADO.
    (Sustituye la funcionalidad insegura de consultar por user_id).
    """
    out = _collect_transactions_for_user(db, current_user)

    # Ordenar descendente por fecha
    out.sort(key=lambda x: x.created_at, reverse=True)
    return out


@router.get("/all", response_model=List[TransactionView])
def get_all_transactions(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user), # 🔒 Actor que consulta
    q: Optional[str] = Query(None, description="Filtro de texto (tipo/nota)"),
):
    """
    Transacciones de TODOS los usuarios.
    Solo para SUPERUSER / ADMIN.
    """
    # 🔒 VERIFICACIÓN DE ROL
    if current_user.role not in {"SUPERUSER", "ADMIN"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para ver transacciones globales",
        )

    out: List[TransactionView] = []

    # Juntamos de todos los usuarios
    users = db.query(models.User).all()
    for u in users:
        out.extend(_collect_transactions_for_user(db, u))

    # Filtro q simple
    if q:
        s = q.strip().lower()
        out = [
            tx
            for tx in out
            if s in tx.type.lower()
            or (tx.note or "").lower().find(s) != -1
            or (tx.username or "").lower().find(s) != -1 # Permitir buscar por username
        ]

    # Ordenar descendente por fecha
    out.sort(key=lambda x: x.created_at, reverse=True)
    return out

