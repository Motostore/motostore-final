# app/api/streaming.py

from typing import List, Optional
from fastapi import APIRouter, Body, HTTPException
from pydantic import BaseModel
import random
import time

router = APIRouter()

# ==========================================
# 1. MODELOS DE DATOS (Coinciden con React)
# ==========================================

# Lo que llega desde el Frontend al crear
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

# Lo que devolvemos al Frontend (incluye ID)
class StreamingProfile(StreamingProfileCreate):
    id: int

# ==========================================
# 2. BASE DE DATOS EN MEMORIA (RAM)
# ==========================================
# ⚠️ ADVERTENCIA: Esta lista se borra si reinicias el servidor.
# Para producción, aquí debes guardar en PostgreSQL/MySQL.
_memory_db: List[StreamingProfile] = []

# Datos de prueba iniciales para que no se vea vacío
_memory_db.append(StreamingProfile(
    id=101, category="Video", provider="Netflix Demo", type="Perfil",
    user="demo@netflix.com", key="1234", dueDate="2025-12-31",
    cost=3.0, price=5.0, status=True, busy=True
))

# ==========================================
# 3. ENDPOINTS
# ==========================================

@router.get("/streaming")
def get_all_streaming():
    """
    GET /api/v1/streaming
    Devuelve la lista de cuentas para la tabla del Admin y Cliente.
    """
    # Devolvemos un objeto con "content" porque así lo espera tu frontend:
    # setItems(res?.content ?? [])
    return {
        "content": _memory_db,
        "totalElements": len(_memory_db)
    }

@router.post("/streaming")
def create_streaming_profile(profile: StreamingProfileCreate):
    """
    POST /api/v1/streaming
    Recibe los datos del formulario React y los guarda en la lista.
    """
    try:
        # 1. Generamos un ID único (simulado con timestamp)
        new_id = int(time.time() * 1000)
        
        # 2. Creamos el objeto completo
        new_profile = StreamingProfile(id=new_id, **profile.dict())
        
        # 3. Guardamos en la "Base de Datos" (Insertamos al principio)
        _memory_db.insert(0, new_profile)
        
        print(f"✅ Guardado perfil: {new_profile.provider} - {new_profile.user}")
        
        # 4. Devolvemos el objeto creado (importante para que React actualice la UI)
        return new_profile
        
    except Exception as e:
        print(f"❌ Error al guardar: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# --- Endpoints Legacy (Opcionales, por si algo más los llama) ---

@router.get("/streaming/providers")
def get_providers_legacy():
    return []