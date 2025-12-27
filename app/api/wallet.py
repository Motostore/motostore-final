# app/api/wallet.py

from typing import Optional, List
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app import models
# 👇 Importamos seguridad para las funciones nuevas
from app.api.auth import get_current_user 

router = APIRouter()

# ==========================================
# 1. SCHEMAS (Modelos de datos)
# ==========================================

# --- Del código original (MANTENIDOS) ---
class WalletBalance(BaseModel):
    balance: float
    profit: float
    currency: str

class AddFundsReq(BaseModel):
    userId: Optional[int] = None
    amount: Optional[float] = None
    note: Optional[str] = None

class AddFundsResponse(BaseModel):
    userId: int
    amount: float
    balance: float
    currency: str

class WalletTransactionView(BaseModel):
    id: int
    amount: float
    type: str
    note: Optional[str]
    created_at: Optional[str] # String ISO

    class Config:
        from_attributes = True

# --- Nuevos para Retiros y "Mi Wallet" (AGREGADOS) ---
class WithdrawRequest(BaseModel):
    amount: float
    bank_info: str 

class MyWalletResponse(BaseModel):
    balance: float
    currency: str
    history: List[WalletTransactionView]

# ==========================================
# 2. HELPERS (Lógica interna MANTENIDA)
# ==========================================

def find_balance(db: Session, user_id: int) -> float:
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user or user.balance is None:
        return 0.0
    return float(user.balance)

def resolve_currency(user_id: int) -> str:
    return "USD"

def balance_payload(user_id: int, balance: float) -> WalletBalance:
    return WalletBalance(
        balance=balance,
        profit=0.0,
        currency=resolve_currency(user_id),
    )

def register_transaction(
    db: Session, user_id: int, amount: float, note: Optional[str], tx_type: str = "DEPOSIT"
) -> models.WalletTransaction:
    log = models.WalletTransaction(
        user_id=user_id,
        amount=amount,
        type=tx_type,
        note=note or "Transacción",
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log

def apply_deposit(db: Session, user_id: int, amount: float, note: Optional[str]) -> models.User:
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=400, detail=f"Usuario no encontrado: {user_id}")

    if user.balance is None:
        user.balance = 0.0

    user.balance += float(amount)
    db.commit()
    db.refresh(user)
    register_transaction(db, user_id, amount, note, "DEPOSIT")
    return user

def resolve_user_or_superuser(user_id: Optional[int], db: Session) -> int:
    if user_id is not None:
        return user_id
    superuser = db.query(models.User).filter(models.User.is_superuser == True).order_by(models.User.id.asc()).first()
    if not superuser:
        raise HTTPException(status_code=404, detail="No hay SUPERUSER para resolver balance")
    return superuser.id

# ==========================================
# 3. ENDPOINTS NUEVOS (Para el Frontend) 🆕
# ==========================================

@router.get("/me", response_model=MyWalletResponse)
def get_my_wallet(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Obtiene saldo e historial del usuario logueado (Seguro).
    """
    logs = (
        db.query(models.WalletTransaction)
        .filter(models.WalletTransaction.user_id == current_user.id)
        .order_by(models.WalletTransaction.created_at.desc())
        .limit(50)
        .all()
    )
    
    # Convertir a View
    history_view = []
    for t in logs:
        history_view.append(WalletTransactionView(
            id=t.id, 
            amount=t.amount, 
            type=t.type, 
            note=t.note, 
            created_at=t.created_at.isoformat() if t.created_at else None
        ))

    return {
        "balance": current_user.balance or 0.0,
        "currency": "USD",
        "history": history_view
    }

@router.post("/withdraw")
def request_withdrawal(
    req: WithdrawRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Solicitar retiro de dinero (Resta del saldo).
    """
    if (current_user.balance or 0.0) < req.amount:
        raise HTTPException(status_code=400, detail="Saldo insuficiente")
    
    if req.amount <= 0:
        raise HTTPException(status_code=400, detail="Monto inválido")

    # 1. Descontar saldo
    current_user.balance -= req.amount
    
    # 2. Registrar movimiento (Negativo)
    register_transaction(db, current_user.id, -req.amount, f"Retiro a: {req.bank_info}", "WITHDRAW_REQUEST")
    
    return {
        "message": "Retiro solicitado correctamente", 
        "new_balance": current_user.balance
    }

# ==========================================
# 4. ENDPOINTS ORIGINALES (Compatibilidad) ♻️
# ==========================================

@router.get("/balance/{userId}", response_model=WalletBalance)
def balance_by_path(userId: int, db: Session = Depends(get_db)):
    balance = find_balance(db, userId)
    return balance_payload(userId, balance)

@router.get("/balance", response_model=WalletBalance)
def balance_by_query(
    userId: Optional[int] = Query(None, alias="userId"),
    db: Session = Depends(get_db),
):
    effective_user_id = resolve_user_or_superuser(userId, db)
    balance = find_balance(db, effective_user_id)
    return balance_payload(effective_user_id, balance)

@router.post("/add-funds", response_model=AddFundsResponse)
def add_funds(req: AddFundsReq, db: Session = Depends(get_db)):
    if req.userId is None or req.amount is None:
        raise HTTPException(status_code=400, detail="userId y amount requeridos")
    if req.amount <= 0:
        raise HTTPException(status_code=400, detail="Monto debe ser positivo")

    apply_deposit(db, req.userId, req.amount, req.note)
    new_balance = find_balance(db, req.userId)

    return AddFundsResponse(
        userId=req.userId,
        amount=req.amount,
        balance=new_balance,
        currency=resolve_currency(req.userId),
    )

@router.post("/{userId}/add-funds", response_model=AddFundsResponse)
def add_funds_path(userId: int, req: AddFundsReq, db: Session = Depends(get_db)):
    amount = req.amount or 0.0
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Monto debe ser positivo")

    apply_deposit(db, userId, amount, req.note)
    new_balance = find_balance(db, userId)

    return AddFundsResponse(
        userId=userId,
        amount=amount,
        balance=new_balance,
        currency=resolve_currency(userId),
    )

@router.get("/transactions/{userId}", response_model=List[WalletTransactionView])
def get_transactions(userId: int, db: Session = Depends(get_db)):
    logs = (
        db.query(models.WalletTransaction)
        .filter(models.WalletTransaction.user_id == userId)
        .order_by(models.WalletTransaction.created_at.desc())
        .all()
    )
    result = []
    for t in logs:
        result.append(WalletTransactionView(
            id=t.id,
            amount=t.amount,
            type=t.type,
            note=t.note,
            created_at=t.created_at.isoformat() if t.created_at else None,
        ))
    return result



