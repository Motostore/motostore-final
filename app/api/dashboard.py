# app/api/dashboard.py
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Query
from pydantic import BaseModel

# 🔥 CONEXIÓN CLAVE: Importamos la función para leer los datos reales
try:
    from app.api.announcements import load_announcement
except ImportError:
    # Fallback por si acaso hay problemas de importación circular
    def load_announcement():
        return {}

router = APIRouter()

class Announcement(BaseModel):
    id: int
    title: str
    message: str
    level: str  # INFO, WARNING, DANGER, SUCCESS
    role: Optional[str] = None
    created_at: datetime

@router.get("/dashboard/announcements", response_model=List[Announcement])
def get_dashboard_announcements(
    role: Optional[str] = Query(None, description="Rol del usuario (SUPERUSER, ADMIN, etc.)"),
):
    """
    GET /api/v1/dashboard/announcements
    Devuelve los anuncios reales gestionados desde el panel de administración.
    """
    
    final_list = []

    # ---------------------------------------------------------
    # 1. BUSCAR EL ANUNCIO REAL (El que guardaste en el Admin)
    # ---------------------------------------------------------
    try:
        real_data = load_announcement()
        
        # Solo lo mostramos si está activo y tiene mensaje
        if real_data.get("active", True) and real_data.get("message"):
            
            # Traducir los colores del frontend a niveles del dashboard
            variant = real_data.get("variant", "info")
            level_map = {
                "info": "INFO",
                "success": "SUCCESS",
                "warning": "WARNING",
                "error": "DANGER",
                "neutral": "INFO"
            }
            
            real_announcement = Announcement(
                id=999,  # ID fijo alto para que destaque
                title="Aviso del Sistema", # Título genérico
                message=real_data.get("message"),
                level=level_map.get(variant, "INFO"),
                role=None, # NULL significa "Para todos los roles"
                created_at=datetime.utcnow()
            )
            
            # Agregamos el anuncio real a la lista
            final_list.append(real_announcement)

    except Exception as e:
        print(f"Error leyendo anuncio real: {e}")

    # ---------------------------------------------------------
    # 2. (OPCIONAL) ANUNCIOS FIJOS DE RESPALDO
    # Si no hay anuncio real, mostramos uno de bienvenida
    # ---------------------------------------------------------
    if not final_list:
        final_list.append(
            Announcement(
                id=1,
                title="Bienvenido al Sistema",
                message="Sistema operativo. No hay anuncios nuevos por el momento.",
                level="INFO",
                role=None,
                created_at=datetime.utcnow(),
            )
        )

    # Filtrado por rol (si el frontend lo pide)
    if role:
        role_upper = role.upper()
        return [
            a for a in final_list
            if a.role is None or (a.role and a.role.upper() == role_upper)
        ]
    
    return final_list