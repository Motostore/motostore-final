import json
import time
import os
from pathlib import Path
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# ⚠️ IMPORTANTE: Sin prefix aquí, lo pone el main.py
router = APIRouter()

# ==========================================
# 1. CONFIGURACIÓN DE GUARDADO (JSON)
# ==========================================
# Usamos un archivo para que los datos sobrevivan al reinicio del servidor
DATA_FILE = Path("streaming_db.json")

def load_db() -> List[Dict]:
    """Lee el archivo JSON y devuelve la lista de cuentas."""
    if not DATA_FILE.exists():
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def save_db(data: List[Dict]):
    """Guarda la lista de cuentas en el archivo JSON."""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

# ==========================================
# 2. MODELOS DE DATOS (Sincronizado con Frontend)
# ==========================================

class StreamingProfileCreate(BaseModel):
    category: str       # Video, Musica, IPTV
    provider: str       # Netflix, Disney...
    type: str           # Perfil, Cuenta Completa...
    user: str           # Email
    key: str            # Contraseña
    
    # 🔥 AQUI ESTÁ EL AJUSTE IMPORTANTE:
    # Aceptamos las fechas dobles que envía tu nuevo formulario
    dueDate: Optional[str] = None         # Fecha general
    clientDueDate: Optional[str] = None   # Fecha corte Cliente
    providerDueDate: Optional[str] = None # Fecha corte Proveedor (Tu pago)
    
    cost: float = 0.0         # Precio compra
    price: float = 0.0        # Precio venta
    status: bool = True
    busy: bool = True

# Modelo completo con ID (puede ser cualquier tipo, aquí usaremos int)
class StreamingProfile(StreamingProfileCreate):
    id: Any 

# ==========================================
# 3. ENDPOINTS
# ==========================================

# 🔥 RUTA: GET /api/v1/streaming (Obtener todas)
@router.get("/")
@router.get("/profile") # Alias por si acaso
def get_all_streaming():
    data = load_db()
    return {
        "content": data,
        "totalPages": 1,
        "totalElements": len(data)
    }

# 🔥 RUTA: POST /api/v1/streaming (Guardar nueva)
@router.post("/")
def create_streaming_profile(profile: StreamingProfileCreate):
    try:
        # 1. Cargar datos actuales
        current_db = load_db()

        # 2. Crear ID único (Timestamp)
        new_id = int(time.time() * 1000)
        
        # 3. Convertir modelo a diccionario y asignar ID
        new_profile_dict = profile.dict()
        new_profile_dict["id"] = new_id
        
        # 4. Guardar al inicio de la lista (para que salga primero)
        current_db.insert(0, new_profile_dict)
        save_db(current_db)
        
        print(f"✅ Guardado perfil: {new_profile_dict['provider']} - {new_profile_dict['user']}")
        return new_profile_dict
        
    except Exception as e:
        print(f"❌ Error al guardar: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 🔥 RUTA: GET /api/v1/streaming/client (Vista cliente)
@router.get("/client")
@router.get("/profile/client") # Alias por compatibilidad
def get_client_streaming():
    # En el futuro aquí filtrarás: [x for x in data if x['user'] == user_email]
    data = load_db()
    return {
        "content": data,
        "totalPages": 1
    }

# 🔥 RUTA: DELETE /api/v1/streaming/profile/{id} (Borrar)
@router.delete("/profile/{profile_id}")
@router.delete("/{profile_id}")
def delete_streaming_profile(profile_id: str):
    current_db = load_db()
    
    # Filtramos para quitar el ID
    # Convertimos a string para asegurar comparación
    new_db = [d for d in current_db if str(d.get("id")) != str(profile_id)]
    
    if len(new_db) == len(current_db):
        raise HTTPException(status_code=404, detail="Perfil no encontrado")
        
    save_db(new_db)
    return {"status": "deleted", "id": profile_id}