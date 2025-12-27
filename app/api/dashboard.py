# app/api/dashboard.py
#
# Endpoints para el dashboard.
# En el frontend están llamando:
#   GET /api/v1/dashboard/announcements?role=SUPERUSER
#
# Aquí devolvemos una lista de anuncios "fake" (en memoria),
# solo para que el panel cargue sin errores y muestre algo.

from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Query
from pydantic import BaseModel

router = APIRouter()


class Announcement(BaseModel):
    id: int
    title: str
    message: str
    level: str  # INFO, WARNING, DANGER, SUCCESS
    role: Optional[str] = None  # SUPERUSER / ADMIN / DISTRIBUTOR / CLIENT etc.
    created_at: datetime


# 🔹 Datos de ejemplo (no usan DB, solo memoria)
_fake_announcements: List[Announcement] = [
    Announcement(
        id=1,
        title="Bienvenido a Motostore Python",
        message="Este es tu nuevo backend migrado a Python. 🎉",
        level="INFO",
        role=None,
        created_at=datetime.utcnow() - timedelta(days=1),
    ),
    Announcement(
        id=2,
        title="Recargas activas",
        message="Ya puedes gestionar productos de recarga, licencias y marketing desde el panel.",
        level="SUCCESS",
        role="SUPERUSER",
        created_at=datetime.utcnow() - timedelta(hours=5),
    ),
    Announcement(
        id=3,
        title="Recordatorio de seguridad",
        message="No compartas tu contraseña con nadie. Próximamente: login con tokens.",
        level="WARNING",
        role=None,
        created_at=datetime.utcnow() - timedelta(hours=2),
    ),
]


@router.get("/dashboard/announcements", response_model=List[Announcement])
def get_dashboard_announcements(
    role: Optional[str] = Query(None, description="Rol del usuario (SUPERUSER, ADMIN, etc.)"),
):
    """
    GET /api/v1/dashboard/announcements?role=SUPERUSER

    Por ahora:
    - Si llega role => filtramos anuncios específicos de ese rol + generales.
    - Si no llega role => devolvemos todos.
    """
    if role:
        role_upper = role.upper()
        return [
            a for a in _fake_announcements
            if a.role is None or a.role.upper() == role_upper
        ]
    return _fake_announcements
