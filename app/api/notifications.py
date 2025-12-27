# app/api/notifications.py
#
# Notificaciones simples para el dashboard.
#
#   GET /api/v1/notifications

from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter()


class NotificationView(BaseModel):
    id: int
    title: str
    message: str
    level: str = Field(
        "info",
        description="Nivel: info | success | warning | danger",
    )
    created_at: datetime


@router.get("", response_model=List[NotificationView])
def list_notifications():
    """
    De momento devolvemos una lista fija en memoria.
    Si quieres, luego las guardamos en BD.
    """
    now = datetime.now(timezone.utc)

    return [
        NotificationView(
            id=1,
            title="Bienvenido a Moto Store",
            message="Tu panel está listo. Configura tus métodos de pago y comienza a vender.",
            level="success",
            created_at=now,
        ),
        NotificationView(
            id=2,
            title="Recarga de saldo",
            message="Recuerda aprobar los pagos reportados por tus clientes.",
            level="warning",
            created_at=now,
        ),
    ]
