from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import get_db
from app import models
from app.api.auth import get_current_user

router = APIRouter()

@router.get("/summary")
def get_stats_summary(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if hasattr(current_user, "role") and current_user.role not in ["SUPERUSER", "ADMIN"]:
        raise HTTPException(status_code=403, detail="Acceso denegado")

    try:
        users_count = db.query(models.User).count()
        orders_count = db.query(models.Order).count()
        
        # Sumamos ventas completadas
        total_sales = db.query(func.sum(models.Order.total_amount))\
            .filter(models.Order.status.in_(["COMPLETED", "PAID", "succeeded"]))\
            .scalar() or 0.0

        return {
            "total_users": users_count,
            "total_orders": orders_count,
            "total_sales": float(total_sales),
            "growth": 0
        }
    except Exception as e:
        print(f"Error Stats Summary: {e}")
        return {"total_users": 0, "total_orders": 0, "total_sales": 0.0, "growth": 0}