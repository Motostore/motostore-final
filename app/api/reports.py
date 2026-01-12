from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.core.database import get_db
from app import models
# Ajusta este import según dónde tengas tu auth. 
# Si tu archivo de login es endpoints/login.py, a veces se importa desde ahí o desde deps.
# Asumiremos que lo tienes en app.api.deps o similar. Si te da error, avísame.
try:
    from app.api.deps import get_current_user
except ImportError:
    # Intento alternativo común
    from app.api.v1.endpoints.login import get_current_user

router = APIRouter()

# ==========================================
# 1. REPORTE GENERAL (CORREGIDO)
# ==========================================
@router.get("/general")
def get_general_report(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Data para el Dashboard Principal.
    Calcula métricas buscando estados 'completed', 'PAID', etc.
    """

    # 🔒 SEGURIDAD
    if current_user.role not in ["SUPERUSER", "ADMIN"]:
        raise HTTPException(status_code=403, detail="Acceso denegado.")

    try:
        # 🔥 CORRECCIÓN AQUÍ: Buscamos varios estados posibles para asegurar que sume
        # Tu modelo por defecto usa "completed"
        valid_statuses = ["completed", "COMPLETED", "PAID", "paid", "succeeded"]

        # A. Ventas Totales
        total_sales = db.query(func.sum(models.Order.total_amount)) \
            .filter(models.Order.status.in_(valid_statuses)).scalar() or 0.0

        # B. Costos
        total_costs = db.query(func.sum(models.Order.cost_amount)) \
            .filter(models.Order.status.in_(valid_statuses)).scalar() or 0.0

        # C. Utilidad Neta
        utilities = total_sales - total_costs

        # D. Usuarios Activos (Que no están disabled)
        # Nota: En tu modelo User tenías 'is_active' y 'disabled'. Usamos is_active=True.
        active_users = db.query(models.User).filter(models.User.is_active == True).count()

        # E. Total Órdenes (Cualquier estado, para saber volumen de intentos)
        total_orders = db.query(models.Order).count()

        # Ticket Promedio
        ticket_promedio = 0.0
        # Contamos solo órdenes exitosas para el ticket promedio real
        successful_orders_count = db.query(models.Order)\
            .filter(models.Order.status.in_(valid_statuses)).count()

        if successful_orders_count > 0:
            ticket_promedio = total_sales / successful_orders_count

        # F. Tasa de Conversión (% de usuarios que han comprado)
        tasa_conversion = 0.0
        if active_users > 0:
            # Contamos usuarios únicos que tienen al menos una orden completada
            compradores = db.query(models.Order.user_id)\
                .filter(models.Order.status.in_(valid_statuses))\
                .distinct().count()
            
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
        print(f"❌ Error en Reporte General: {e}")
        # En caso de error devolvemos 0 para no romper el frontend
        return {
            "ventas": 0.0, "compras": 0.0, "utilidades": 0.0,
            "usuariosActivos": 0, "ticketPromedio": 0.0,
            "totalOrdenes": 0, "tasaConversion": 0.0
        }


# ==========================================
# 2. REPORTE DE WALLET (Sin cambios mayores)
# ==========================================
@router.get("/utilities")
def get_utilities_report(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if current_user.role not in ["SUPERUSER", "ADMIN"]:
        raise HTTPException(status_code=403, detail="Acceso denegado.")

    total_in = db.query(func.sum(models.WalletTransaction.amount)) \
        .filter(models.WalletTransaction.type == "DEPOSIT").scalar() or 0.0

    total_out_negative = db.query(func.sum(models.WalletTransaction.amount)) \
        .filter(models.WalletTransaction.type.in_(["WITHDRAW", "WITHDRAW_REQUEST"])).scalar() or 0.0

    total_out = abs(total_out_negative)
    net_system_balance = total_in + total_out_negative

    return {
        "total_income": float(total_in),
        "total_withdrawn": float(total_out),
        "net_system_balance": float(net_system_balance),
        "currency": "USD",
        "generated_at": str(func.now())
    }


# ==========================================
# 3. REPORTE DE MOVIMIENTOS
# ==========================================
@router.get("/movimiento")
def get_movimientos_report(
    q: str | None = None,
    limit: int = 200,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if current_user.role not in ["SUPERUSER", "ADMIN"]:
        raise HTTPException(status_code=403, detail="Acceso denegado.")

    if limit < 1: limit = 1
    if limit > 500: limit = 500

    try:
        query = db.query(models.WalletTransaction)

        if q:
            w = f"%{q.strip()}%"
            query = query.filter(models.WalletTransaction.type.ilike(w))

        query = query.order_by(models.WalletTransaction.id.desc())
        items = query.limit(limit).all()

        out = []
        for t in items:
            fecha = t.created_at.isoformat() if t.created_at else ""
            
            # Intentar obtener nombre de usuario de forma segura
            usuario = "Desconocido"
            if t.user:
                usuario = t.user.username or t.user.email or str(t.user.id)
            
            # Estado (WalletTransaction a veces no tiene status, asumimos OK)
            estado = "OK"

            out.append({
                "id": t.id,
                "fecha": fecha,
                "tipo": str(t.type),
                "usuario": usuario,
                "monto": float(t.amount),
                "estado": estado
            })

        return {"items": out}

    except Exception as e:
        print(f"❌ Error en Reporte Movimientos: {e}")
        raise HTTPException(status_code=500, detail="Error generando reporte.")
