from datetime import datetime
from typing import Optional, List
import shutil
import os

from fastapi import APIRouter, Depends, HTTPException, Query, Form, File, UploadFile, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app import models

# 👇 IMPORTANTE: Importamos la seguridad para saber quién está logueado
# Asegúrate de que esta ruta sea correcta en tu proyecto (usualmente app.api.auth o app.core.security)
from app.api.auth import get_current_user 

router = APIRouter()

# ----------------- Schemas Pydantic ----------------- #

class PaymentReportRead(BaseModel):
    id: int
    user_id: int
    amount: float
    method: str
    status: str
    proof_url: Optional[str]
    note: Optional[str]
    created_at: datetime
    approved_by: Optional[int]
    approved_at: Optional[datetime]
    rejected_by: Optional[int]
    rejected_at: Optional[datetime]

    class Config:
        from_attributes = True

# ----------------- Helpers internos ----------------- #

def _load_report_or_404(db: Session, payment_id: int) -> models.PaymentReport:
    report = (
        db.query(models.PaymentReport)
        .filter(models.PaymentReport.id == payment_id)
        .first()
    )
    if not report:
        raise HTTPException(status_code=404, detail="Pago reportado no encontrado")
    return report

def _apply_wallet_deposit_from_report(db: Session, report: models.PaymentReport):
    user = db.query(models.User).filter(models.User.id == report.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    if user.balance is None:
        user.balance = 0.0

    user.balance += report.amount
    db.commit()
    db.refresh(user)

    tx = models.WalletTransaction(
        user_id=user.id,
        amount=report.amount,
        type="DEPOSIT",
        note=f"Recarga aprobada (Reporte #{report.id})",
    )
    db.add(tx)
    db.commit()
    db.refresh(tx)

# ----------------- Endpoints ----------------- #

@router.post("", response_model=PaymentReportRead)
def report_payment(
    method: str = Form(...),
    amount: float = Form(...),
    note: Optional[str] = Form(None),
    proof_url: Optional[UploadFile] = File(None, alias="proof_url"),
    db: Session = Depends(get_db),
    # Opcional: Si quieres forzar que el usuario esté logueado para reportar, descomenta la siguiente línea:
    current_user: models.User = Depends(get_current_user)
):
    """
    Crea un reporte de pago.
    """
    # Usamos el ID del usuario logueado. 
    # Si quieres permitir reportes anónimos (no recomendado), usa un ID fijo o maneja la excepción.
    user_id = current_user.id 
    
    # Manejo del Archivo
    file_location = None
    if proof_url:
        # Crea carpeta uploads si no existe
        os.makedirs("uploads", exist_ok=True)
        
        # Nombre único para evitar sobrescribir
        filename = f"pay_{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{proof_url.filename}"
        file_location = f"uploads/{filename}"
        
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(proof_url.file, buffer)

    report = models.PaymentReport(
        user_id=user_id,
        amount=amount,
        method=method,
        proof_url=file_location,
        note=note,
        status="PENDING",
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


@router.get("", response_model=List[PaymentReportRead])
def list_all_reports(
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user) # 🔒 Requiere Login
):
    """
    Lista los reportes.
    - Si es ADMIN/SUPERUSER: Ve todos.
    - Si es CLIENTE: Solo ve los suyos.
    """
    query = db.query(models.PaymentReport)

    # Si NO es admin, filtramos solo sus pagos
    if current_user.role not in ["SUPERUSER", "ADMIN"]:
        query = query.filter(models.PaymentReport.user_id == current_user.id)
    
    if status:
        query = query.filter(models.PaymentReport.status == status.upper())
        
    return query.order_by(models.PaymentReport.created_at.desc()).all()


# 👇👇👇 ZONA DE SEGURIDAD (ADMIN ONLY) 👇👇👇

@router.post("/{payment_id}/approve", response_model=PaymentReportRead)
def approve_report(
    payment_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user) # 1. Identificar quién llama
):
    """
    Aprueba un pago y carga saldo. SOLO SUPERUSER O ADMIN.
    """
    # 2. Verificar Permisos
    if current_user.role not in ["SUPERUSER", "ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="No tienes permisos para aprobar pagos."
        )

    report = _load_report_or_404(db, payment_id)

    if report.status != "PENDING":
        raise HTTPException(status_code=400, detail="Este pago ya fue procesado")

    report.status = "APPROVED"
    report.approved_at = datetime.utcnow()
    report.approved_by = current_user.id # 3. Guardar quién aprobó realmente

    db.commit()
    db.refresh(report)

    # Cargar saldo a la wallet
    _apply_wallet_deposit_from_report(db, report)

    return report


@router.post("/{payment_id}/reject", response_model=PaymentReportRead)
def reject_report(
    payment_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user) # 1. Identificar quién llama
):
    """
    Rechaza un pago. SOLO SUPERUSER O ADMIN.
    """
    # 2. Verificar Permisos
    if current_user.role not in ["SUPERUSER", "ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="No tienes permisos para rechazar pagos."
        )

    report = _load_report_or_404(db, payment_id)

    if report.status != "PENDING":
        raise HTTPException(status_code=400, detail="Este pago ya fue procesado")

    report.status = "REJECTED"
    report.rejected_at = datetime.utcnow()
    report.rejected_by = current_user.id # 3. Guardar quién rechazó

    db.commit()
    db.refresh(report)

    return report



