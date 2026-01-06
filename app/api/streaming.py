# app/api/streaming.py

from typing import List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import time

# ⚠️ IMPORTANTE: Aquí NO ponemos prefix, porque ya lo pone el main.py
router = APIRouter()

# ==========================================
# 1. MODELOS DE DATOS (Coinciden con React)
# ==========================================

class StreamingProfileCreate(BaseModel):
    category: str       # Video, Musica, IPTV
    provider: str       # Netflix, Disney...
    type: str           # Perfil, Cuenta Completa...
    user: str           # Email
    key: str            # Contraseña
    dueDate: str        # Fecha
    cost: float         # Precio compra
    price: float        # Precio venta
    status: bool = True
    busy: bool = True

class StreamingProfile(StreamingProfileCreate):
    id: int

# ==========================================
# 2. BASE DE DATOS EN MEMORIA (RAM)
# ==========================================
# Esta lista se reinicia si apagas el servidor.
# En producción real usarás PostgreSQL.
_memory_db: List[StreamingProfile] = []

# Dato de prueba
_memory_db.append(StreamingProfile(
    id=101, category="Video", provider="Netflix Demo", type="Perfil",
    user="demo@netflix.com", key="1234", dueDate="2025-12-31",
    cost=3.0, price=5.0, status=True, busy=True
))

# ==========================================
# 3. ENDPOINTS
# ==========================================

# 🔥 RUTA: GET /api/v1/streaming
@router.get("/") 
def get_all_streaming():
    return {
        "content": _memory_db,
        "totalPages": 1,
        "totalElements": len(_memory_db)
    }

# 🔥 RUTA: POST /api/v1/streaming (La que usa el botón Guardar)
@router.post("/")
def create_streaming_profile(profile: StreamingProfileCreate):
    try:
        # 1. Crear ID
        new_id = int(time.time() * 1000)
        
        # 2. Crear Objeto
        new_profile = StreamingProfile(id=new_id, **profile.dict())
        
        # 3. Guardar al inicio de la lista
        _memory_db.insert(0, new_profile)
        
        print(f"✅ Guardado perfil: {new_profile.provider} - {new_profile.user}")
        return new_profile
        
    except Exception as e:
        print(f"❌ Error al guardar: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 🔥 RUTA: GET /api/v1/streaming/client (Para el panel de cliente)
@router.get("/client")
def get_client_streaming():
    # Aquí en el futuro filtrarás por usuario: if item.user == current_user.email
    return {
        "content": _memory_db,
        "totalPages": 1
    }