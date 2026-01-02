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

# --- VALORES POR DEFECTO ---
DEFAULT_CONFIG = {
    "rates": [
        {"code": "VE", "rate": 54.00, "isManual": True, "label": "Tasa USDT"},
        {"code": "CO", "rate": 4100.00, "isManual": False, "label": "Colombia"},
        {"code": "PE", "rate": 3.80, "isManual": False, "label": "Perú"},
        {"code": "CL", "rate": 980.00, "isManual": False, "label": "Chile"}
    ],
    "profit": 5.00
}

# 🟢 ESTA ES LA FUNCIÓN QUE FALTA Y QUE ARREGLA EL ERROR ROJO
def get_dynamic_rates_dict():
    """Esta función lee el archivo JSON y le da los precios al sistema de recargas"""
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Convertimos la lista de tasas en un diccionario fácil de leer
                return {item['code']: item['rate'] for item in data['rates']}
        except Exception:
            pass
    
    # Si falla o no existe, usa los valores por defecto
    return {item['code']: item['rate'] for item in DEFAULT_CONFIG['rates']}

# --- RUTAS ---

@router.get("/config", response_model=TreasuryConfig)
def get_config():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return DEFAULT_CONFIG

@router.post("/config")
def save_config(config: TreasuryConfig):
    try:
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(config.dict(), f, indent=4)
        return {"status": "ok", "message": "Guardado correctamente"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))