from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.core.database import get_db
from app import models
# Importamos seguridad para proteger el reporte
from app.api.auth import get_current_user

router = APIRouter()

# ==========================================
# 1. REPORTE GENERAL (Para el Dashboard Visual)
# ==========================================
@router.get("/general")
def get_general_report(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Data para el Dashboard Principal (Frontend).
    Retorna métricas de Ventas, Compras, Usuarios y Conversión.
    """

    # 🔒 SEGURIDAD: Solo Admin/Superuser puede ver esto
    if current_user.role not in ["SUPERUSER", "ADMIN"]:
        raise HTTPException(status_code=403, detail="Acceso denegado.")

    try:
        # A. Ventas Totales (Suma de órdenes completadas/pagadas)
        total_sales = db.query(func.sum(models.Order.total_amount)) \
            .filter(models.Order.status == "PAID").scalar() or 0.0

        # B. Costos (Si implementaste la columna cost_amount)
        total_costs = db.query(func.sum(models.Order.cost_amount)) \
            .filter(models.Order.status == "PAID").scalar() or 0.0

        # C. Utilidad Neta
        utilities = total_sales - total_costs

        # D. Usuarios Activos
        active_users = db.query(models.User).filter(models.User.is_active == True).count()

        # E. Métricas Derivadas
        total_orders = db.query(models.Order).count()

        ticket_promedio = 0.0
        if total_orders > 0:
            ticket_promedio = total_sales / total_orders

        # F. Tasa de Conversión (Simulada: Órdenes / Usuarios activos)
        tasa_conversion = 0.0
        if active_users > 0:
            tasa_conversion = round((total_orders / active_users) * 100, 2)

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
        return {
            "ventas": 0.0, "compras": 0.0, "utilidades": 0.0,
            "usuariosActivos": 0, "ticketPromedio": 0.0,
            "totalOrdenes": 0, "tasaConversion": 0.0
        }


# ==========================================
# 2. REPORTE DE UTILIDADES (Tu lógica financiera)
# ==========================================
@router.get("/utilities")
def get_utilities_report(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Reporte Financiero de Wallet (Entradas vs Salidas).
    """

    if current_user.role not in ["SUPERUSER", "ADMIN"]:
        raise HTTPException(status_code=403, detail="Acceso denegado.")

    # 1. Total Dinero Entrado (DEPOSIT)
    total_in = db.query(func.sum(models.WalletTransaction.amount)) \
        .filter(models.WalletTransaction.type == "DEPOSIT").scalar() or 0.0

    # 2. Total Retiros (WITHDRAW) - Sumamos negativos
    total_out_negative = db.query(func.sum(models.WalletTransaction.amount)) \
        .filter(models.WalletTransaction.type.in_(["WITHDRAW", "WITHDRAW_REQUEST"])).scalar() or 0.0

    total_out = abs(total_out_negative)

    # 3. Dinero Neto en Wallets
    net_system_balance = total_in + total_out_negative

    return {
        "total_income": float(total_in),
        "total_withdrawn": float(total_out),
        "net_system_balance": float(net_system_balance),
        "currency": "USD",
        "generated_at": str(func.now())
    }


# ==========================================
# 3. REPORTE DE MOVIMIENTOS (LISTA REAL)
# ==========================================
@router.get("/movimiento")
def get_movimientos_report(
    q: str | None = None,
    limit: int = 200,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Lista movimientos desde WalletTransaction.
    Endpoint final:
      /api/v1/reports/movimiento?q=...&limit=200
    """

    if current_user.role not in ["SUPERUSER", "ADMIN"]:
        raise HTTPException(status_code=403, detail="Acceso denegado.")

    # límite seguro
    if limit < 1:
        limit = 1
    if limit > 500:
        limit = 500

    try:
        query = db.query(models.WalletTransaction)

        # Filtro simple por tipo (DEPOSIT/WITHDRAW/etc)
        if q:
            w = f"%{q.strip()}%"
            query = query.filter(models.WalletTransaction.type.ilike(w))

        # Orden: más reciente primero
        if hasattr(models.WalletTransaction, "created_at"):
            query = query.order_by(models.WalletTransaction.created_at.desc())
        else:
            query = query.order_by(models.WalletTransaction.id.desc())

        items = query.limit(limit).all()

        out = []
        for t in items:
            # Fecha
            if hasattr(t, "created_at") and t.created_at:
                fecha = t.created_at.isoformat()
            else:
                fecha = ""

            # Usuario (si existe relación user)
            usuario = ""
            if hasattr(t, "user") and t.user:
                if hasattr(t.user, "username") and t.user.username:
                    usuario = t.user.username
                elif hasattr(t.user, "email") and t.user.email:
                    usuario = t.user.email
                else:
                    usuario = str(getattr(t, "user_id", "")) or ""
            else:
                usuario = str(getattr(t, "user_id", "")) or ""

            # Estado: si tu modelo no tiene status, ponemos OK
            estado = "OK"
            if hasattr(t, "status") and getattr(t, "status"):
                estado = str(getattr(t, "status"))

            out.append({
                "id": getattr(t, "id", ""),
                "fecha": fecha,
                "tipo": str(getattr(t, "type", "")),
                "usuario": usuario,
                "monto": float(getattr(t, "amount", 0.0) or 0.0),
                "estado": estado
            })

        return {"items": out}

    except Exception as e:
        print(f"❌ Error en Reporte Movimientos: {e}")
        raise HTTPException(status_code=500, detail="Error generando reporte de movimientos.")
