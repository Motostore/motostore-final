from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.core.database import get_db
from app import models

# --- IMPORTACIÓN CORREGIDA ---
# Ahora apuntamos al archivo correcto que nos mostró el grep
from app.api.auth import get_current_user

router = APIRouter()

# ==========================================
# 1. REPORTE GENERAL (Dashboard)
# ==========================================
@router.get("/general")
def get_general_report(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if hasattr(current_user, "role") and current_user.role not in ["SUPERUSER", "ADMIN"]:
        raise HTTPException(status_code=403, detail="Acceso denegado.")

    try:
        valid_statuses = ["completed", "COMPLETED", "PAID", "paid", "succeeded"]

        total_sales = (
            db.query(func.sum(models.Order.total_amount))
            .filter(models.Order.status.in_(valid_statuses))
            .scalar() or 0.0
        )

        total_costs = (
            db.query(func.sum(models.Order.cost_amount))
            .filter(models.Order.status.in_(valid_statuses))
            .scalar() or 0.0
        )

        utilities = total_sales - total_costs
        active_users = db.query(models.User).filter(models.User.is_active == True).count()
        total_orders = db.query(models.Order).count()

        ticket_promedio = 0.0
        successful_orders_count = (
            db.query(models.Order)
            .filter(models.Order.status.in_(valid_statuses))
            .count()
        )

        if successful_orders_count > 0:
            ticket_promedio = total_sales / successful_orders_count

        tasa_conversion = 0.0
        if active_users > 0:
            compradores = (
                db.query(models.Order.user_id)
                .filter(models.Order.status.in_(valid_statuses))
                .distinct()
                .count()
            )
            tasa_conversion = round((compradores / active_users) * 100, 2)

        return {
            "ventas": float(total_sales),
            "compras": float(total_costs),
            "utilidades": float(utilities),
            "usuariosActivos": int(active_users),
            "ticketPromedio": float(ticket_promedio),
            "totalOrdenes": int(total_orders),
            "tasaConversion": float(tasa_conversion)
        }

    except Exception as e:
        print(f"Error Reporte General: {e}")
        return {
            "ventas": 0.0, "compras": 0.0, "utilidades": 0.0,
            "usuariosActivos": 0, "ticketPromedio": 0.0,
            "totalOrdenes": 0, "tasaConversion": 0.0
        }

# ==========================================
# 2. REPORTE WALLET (Utilities)
# ==========================================
@router.get("/utilities")
def get_utilities_report(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if hasattr(current_user, "role") and current_user.role not in ["SUPERUSER", "ADMIN"]:
        raise HTTPException(status_code=403, detail="Acceso denegado.")

    try:
        total_in = (
            db.query(func.sum(models.WalletTransaction.amount))
            .filter(models.WalletTransaction.type == "DEPOSIT")
            .scalar() or 0.0
        )

        total_out_negative = (
            db.query(func.sum(models.WalletTransaction.amount))
            .filter(models.WalletTransaction.type.in_(["WITHDRAW", "WITHDRAW_REQUEST"]))
            .scalar() or 0.0
        )

        total_out = abs(total_out_negative)
        net_system_balance = total_in + total_out_negative

        return {
            "total_income": float(total_in),
            "total_withdrawn": float(total_out),
            "net_system_balance": float(net_system_balance),
            "currency": "USD"
        }

    except Exception as e:
        print(f"Error Reporte Utilities: {e}")
        return {
            "total_income": 0.0,
            "total_withdrawn": 0.0,
            "net_system_balance": 0.0,
            "currency": "USD"
        }
