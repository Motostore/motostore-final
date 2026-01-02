from datetime import datetime
from typing import Optional, List
import shutil
import os

from fastapi import APIRouter, Depends, HTTPException, Query, Form, File, UploadFile, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app import models
from app.api.auth import get_current_user 

# 🟢 1. IMPORTAMOS LA TESORERÍA PARA CONOCER LAS TASAS DEL DÍA
from app.api.exchange import get_dynamic_rates_dict

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

# 🟢 ESTA ES LA FUNCIÓN QUE MODIFICAMOS (La Calculadora)
def _apply_wallet_deposit_from_report(db: Session, report: models.PaymentReport):
    user = db.query(models.User).filter(models.User.id == report.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # A. OBTENEMOS LAS TASAS ACTUALES
    rates = get_dynamic_rates_dict()
    
    # B. DETECTAMOS LA MONEDA (Asumimos que el 'method' es COP, CLP, PEN o USD)
    # Limpiamos el texto por si viene con espacios (ej: " COP ")
    currency_code = report.method.upper().strip() 
    
    # C. BUSCAMOS LA TASA (Si no existe, usamos 1.0)
    tasa = rates.get(currency_code, 1.0)
    
    # D. HACEMOS LA CONVERSIÓN (MATEMÁTICA PURA)
    # Si reportaron 100.000 COP y la tasa es 4.100 -> 100.000 / 4.100 = 24.39 USD
    monto_final_usd = report.amount
    
    if tasa > 1.0:
        monto_final_usd = report.amount / tasa
    
    # Redondeamos a 2 decimales (Dinero real)
    monto_final_usd = round(monto_final_usd, 2)

    # E. CARGAMOS EL SALDO AL USUARIO
    if user.balance is None:
        user.balance = 0.0

    user.balance += monto_final_usd
    db.commit()
    db.refresh(user)

    # F. CREAMOS EL REGISTRO EN EL HISTORIAL (WALLET)
    # Nota inteligente: Guardamos la evidencia de la conversión
    nota_transaccion = f"Recarga Aprobada (#{report.id})"
    if tasa > 1.0:
        nota_transaccion += f" [{report.amount} {currency_code} @ {tasa} = {monto_final_usd} USD]"

    tx = models.WalletTransaction(
        user_id=user.id,
        amount=monto_final_usd, # <-- AQUÍ GUARDAMOS DÓLARES
        type="DEPOSIT",
        note=nota_transaccion,
    )
    db.add(tx)
    db.commit()
    db.refresh(tx)

# ----------------- Endpoints ----------------- #

@router.post("", response_model=PaymentReportRead)
def report_payment(
    method: str = Form(..., description="Moneda de pago: COP, CLP, PEN, VES, USD"), # Exigimos el código de moneda
    amount: float = Form(...),
    note: Optional[str] = Form(None),
    proof_url: Optional[UploadFile] = File(None, alias="proof_url"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Crea un reporte de pago.
    IMPORTANTE: En 'method' el Frontend debe enviar la moneda (COP, CLP, PEN).
    """
    user_id = current_user.id 
    
    # Manejo del Archivo
    file_location = None
    if proof_url:
        os.makedirs("uploads", exist_ok=True)
        filename = f"pay_{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{proof_url.filename}"
        file_location = f"uploads/{filename}"
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(proof_url.file, buffer)

    report = models.PaymentReport(
        user_id=user_id,
        amount=amount,
        method=method.upper(), # Guardamos siempre en mayúsculas (COP, CLP...)
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
    current_user: models.User = Depends(get_current_user)
):
    """
    Lista los reportes.
    """
    query = db.query(models.PaymentReport)

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
    current_user: models.User = Depends(get_current_user)
):
    """
    Aprueba un pago y carga saldo CONVERTIDO A DÓLARES.
    """
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
    report.approved_by = current_user.id

    db.commit()
    db.refresh(report)

    # 🟢 AQUÍ OCURRE LA CONVERSIÓN Y DEPOSITO
    _apply_wallet_deposit_from_report(db, report)

    return report


@router.post("/{payment_id}/reject", response_model=PaymentReportRead)
def reject_report(
    payment_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Rechaza un pago.
    """
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
    report.rejected_by = current_user.id

    db.commit()
    db.refresh(report)

    return report
