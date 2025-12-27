# app/api/announcements.py
import json
from pathlib import Path
from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict

# Inicialización del Router
router = APIRouter()

# --- CONFIGURACIÓN DE PERSISTENCIA CON ARCHIVO JSON ---
DATA_FILE = Path("announcement_data.json")

DEFAULT_ANNOUNCEMENT_DATA: Dict[str, Any] = {
    # 🛑 ESTE ES EL MENSAJE INICIAL POR DEFECTO 🛑
    "id": 1,
    "message": "🚀 SISTEMA ACTIVO: Las recargas de Movistar y Digitel están funcionando al 100% ✦ TASA BCV: Actualizada ✦ SOPORTE: Activo 24/7 para distribuidores.",
    "variant": "success",
    "active": True,
    "dismissible": False,
    "linkUrl": None,
    "audience": "ALL",
    "includeDescendants": True,
    "ownerScope": "ALL",
    "ownerId": "SYSTEM_INIT",
    "startsAt": None,
    "endsAt": None,
}

# --- Funciones de Persistencia ---

def load_announcement() -> Dict[str, Any]:
    """Carga los datos del anuncio desde el archivo JSON, o usa los valores por defecto si falla."""
    if not DATA_FILE.exists():
        # Si el archivo no existe (primera vez), lo creamos.
        save_announcement(DEFAULT_ANNOUNCEMENT_DATA)
        return DEFAULT_ANNOUNCEMENT_DATA
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        # Si el archivo está corrupto o no se puede leer, reiniciamos el estado.
        save_announcement(DEFAULT_ANNOUNCEMENT_DATA)
        return DEFAULT_ANNOUNCEMENT_DATA

def save_announcement(data: Dict[str, Any]):
    """Guarda los datos del anuncio en el archivo JSON."""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

# --- MODELO PYDANTIC (Validation Schema) ---
class AnnouncementModel(BaseModel):
    # Definición precisa del esquema que el frontend envía
    id: Optional[int] = Field(None)
    message: str = Field(..., max_length=500)
    variant: str
    active: bool
    dismissible: bool
    linkUrl: Optional[str] = None
    audience: List[str] | str
    includeDescendants: bool
    ownerScope: str
    ownerId: Optional[str] = None
    startsAt: Optional[str] = None
    endsAt: Optional[str] = None

# -----------------------------------------------
# 🛑 RUTAS DEFINIDAS PARA LA BARRA DE ANUNCIOS 🛑
# -----------------------------------------------

# Endpoint GET: Obtener el anuncio actual
@router.get("/users/announcement-bar", tags=["announcements"])
@router.get("/announcement-bar", tags=["announcements"])
@router.get("/admin/announcement", tags=["announcements"])
@router.get("/settings/announcement", tags=["announcements"])
async def get_current_announcement():
    """Devuelve la configuración del anuncio global, leyendo desde el archivo."""
    # 🛑 LA PERSISTENCIA ESTÁ AQUÍ 🛑: Lee el archivo en cada petición GET
    return load_announcement()

# Endpoint POST: Publicar o actualizar el anuncio
@router.post("/users/announcement-bar", tags=["announcements"])
@router.post("/announcement-bar", tags=["announcements"])
@router.post("/admin/announcement", tags=["announcements"])
@router.post("/settings/announcement", tags=["announcements"])
async def update_announcement(announcement: AnnouncementModel):
    """Actualiza la configuración del anuncio global y la guarda en el archivo."""
    
    # 1. Convertir el modelo validado a un diccionario
    data = announcement.model_dump(exclude_none=True)
    
    # 2. Mantener el ID original (lo cargamos del archivo)
    current_data = load_announcement()
    if current_data.get("id"):
        data["id"] = current_data["id"]
        
    # 3. Guardar los datos actualizados
    # 🛑 LA PERSISTENCIA ESTÁ AQUÍ 🛑: Escribe en el archivo
    save_announcement(data)
    
    # 4. Devolver la respuesta
    return data