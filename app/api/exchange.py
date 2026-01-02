import json
import os
from typing import Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

router = APIRouter()

# ---------- SISTEMA DE PERSISTENCIA (JSON) ---------- #
# Esto actuará como tu base de datos para las tasas
DB_FILE = "rates_config.json"

# Configuración por defecto (si el archivo no existe)
DEFAULT_CONFIG = {
    "rates": [
        {"code": "VE", "rate": 54.00, "isManual": True, "label": "Tasa USDT"},
        {"code": "CO", "rate": 4100.00, "isManual": False, "label": "Tasa COP"},
        {"code": "PE", "rate": 3.80, "isManual": False, "label": "Tasa PEN"},
        {"code": "CL", "rate": 980.00, "isManual": False, "label": "Tasa CLP"}
    ],
    "profit": 5.00
}

# Mapa para traducir Código de País (Frontend) a Moneda (Backend)
COUNTRY_TO_CURRENCY = {
    "VE": "VES",
    "CO": "COP",
    "PE": "PEN",
    "CL": "CLP",
    "US": "USD"
}

# ---------- MODELOS DE DATOS (Pydantic) ---------- #

# Modelo de cada item que envía el Frontend
class RateItem(BaseModel):
    code: str
    rate: float
    isManual: bool
    label: Optional[str] = None

# Modelo completo de la configuración
class TreasuryConfig(BaseModel):
    rates: List[RateItem]
    profit: float

class ConvertResult(BaseModel):
    from_currency: str
    to_currency: str
    amount: float
    rate_used: float
    result: float

# ---------- FUNCIONES DE CARGA Y GUARDADO ---------- #

def load_config() -> dict:
    """Carga la configuración desde el archivo JSON o usa la default."""
    if not os.path.exists(DB_FILE):
        return DEFAULT_CONFIG
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error cargando DB: {e}")
        return DEFAULT_CONFIG

def save_config(data: TreasuryConfig):
    """Guarda la configuración en el archivo JSON."""
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data.dict(), f, indent=4)

def get_dynamic_rates_dict() -> Dict[str, float]:
    """
    Convierte la lista del frontend en el diccionario simple
    que usa tu sistema de conversión (ej: 'COP': 4100.0)
    """
    config = load_config()
    rates_map = {"USD": 1.0}
    
    for item in config.get("rates", []):
        # Traducimos el código de país (CO) a moneda (COP)
        currency_code = COUNTRY_TO_CURRENCY.get(item["code"], item["code"])
        rates_map[currency_code] = float(item["rate"])
    
    return rates_map

# ---------- ENDPOINTS PARA EL DASHBOARD (TESORERÍA) ---------- #

@router.get("/config", response_model=TreasuryConfig)
def get_treasury_config():
    """
    Endpoint que usa el Frontend (Next.js) para leer las tasas actuales
    y pintarlas en el formulario.
    """
    data = load_config()
    return data

@router.post("/config")
def update_treasury_config(config: TreasuryConfig):
    """
    Endpoint que usa el botón 'GUARDAR' del Frontend.
    Escribe los cambios en el disco.
    """
    try:
        save_config(config)
        return {"status": "success", "message": "Tasas guardadas correctamente", "data": config}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------- ENDPOINTS DE CONVERSIÓN (SISTEMA ANTIGUO) ---------- #

@router.get("", response_model=Dict[str, float])
def get_simple_rates():
    """Devuelve las tasas en formato simple para otros sistemas."""
    return get_dynamic_rates_dict()

@router.get("/convert", response_model=ConvertResult)
def convert_currency(
    from_currency: str = Query(..., description="Moneda origen, ej: USD"),
    to_currency: str = Query(..., description="Moneda destino, ej: VES"),
    amount: float = Query(..., gt=0, description="Cantidad a convertir"),
):
    """
    Convierte usando las tasas ACTUALIZADAS desde el archivo JSON.
    """
    f = from_currency.strip().upper()
    t = to_currency.strip().upper()
    
    # Cargamos las tasas frescas del archivo
    current_rates = get_dynamic_rates_dict()

    if f not in current_rates:
        raise HTTPException(status_code=400, detail=f"Moneda origen no soportada: {f}")
    if t not in current_rates:
        raise HTTPException(status_code=400, detail=f"Moneda destino no soportada: {t}")

    # Lógica de conversión
    # 1. Pasar a USD
    amount_in_usd = amount / current_rates[f]

    # 2. De USD a Destino
    result_amount = amount_in_usd * current_rates[t]

    rate_from_to = current_rates[t] / current_rates[f]

    return ConvertResult(
        from_currency=f,
        to_currency=t,
        amount=amount,
        rate_used=rate_from_to,
        result=result_amount,
    )