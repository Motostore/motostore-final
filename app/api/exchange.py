import json
import os
from typing import Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

# Archivo donde se guardan los datos
DB_FILE = "tasas_db.json"

# --- MODELOS ---
class RateItem(BaseModel):
    code: str
    rate: float
    isManual: bool
    label: Optional[str] = None

class TreasuryConfig(BaseModel):
    rates: List[RateItem]
    profit: float

# --- VALORES POR DEFECTO (Solo si falla la lectura) ---
DEFAULT_CONFIG = {
    "rates": [
        {"code": "VE", "rate": 54.00, "isManual": True, "label": "Tasa USDT"},
        {"code": "CO", "rate": 4100.00, "isManual": False, "label": "Colombia"},
        {"code": "PE", "rate": 3.80, "isManual": False, "label": "Perú"},
        {"code": "CL", "rate": 980.00, "isManual": False, "label": "Chile"}
    ],
    "profit": 5.00
}

# --- RUTAS ---

@router.get("/config", response_model=TreasuryConfig)
def get_config():
    # Intentamos leer el archivo REAL
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                print("✅ LECTURA EXITOSA DE JSON:", data) # Log para depurar
                return data
        except Exception as e:
            print("❌ ERROR LEYENDO ARCHIVO:", e)
    
    # Si no existe archivo, devolvemos default
    print("⚠️ ARCHIVO NO EXISTE, USANDO DEFAULT")
    return DEFAULT_CONFIG

@router.post("/config")
def save_config(config: TreasuryConfig):
    try:
        # Forzamos la escritura
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(config.dict(), f, indent=4)
        print("💾 GUARDADO EXITOSO EN:", os.path.abspath(DB_FILE))
        return {"status": "ok", "message": "Guardado correctamente"}
    except Exception as e:
        print("🔥 ERROR GUARDANDO:", e)
        raise HTTPException(status_code=500, detail=str(e))