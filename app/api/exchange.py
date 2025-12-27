# app/api/exchange.py
#
# Tasas de cambio simples (versión estática).
#
#   GET /api/v1/exchange
#   GET /api/v1/exchange/convert?from=USD&to=VES&amount=100
#
# Más adelante, si quieres, esto se puede conectar a una API real.

from typing import Dict
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

router = APIRouter()

# ---------- Configuración estática de tasas ---------- #
# base_currency: USD
# rates: cuántas unidades de la otra moneda equivalen a 1 USD
#
# EJEMPLO:
#   1 USD = 4000 COP  → "COP": 4000.0

BASE_CURRENCY = "USD"

RATES: Dict[str, float] = {
    "USD": 1.0,
    "COP": 4000.0,   # ejemplo
    "VES": 40.0,     # ejemplo
    "MXN": 17.0,     # ejemplo
    "EUR": 0.9,      # ejemplo
}


# ---------- Schemas ---------- #

class ExchangeRatesView(BaseModel):
    base: str = Field(..., description="Moneda base de las tasas")
    rates: Dict[str, float] = Field(..., description="Tasas por moneda")


class ConvertResult(BaseModel):
    from_currency: str
    to_currency: str
    amount: float
    rate_used: float
    result: float


# ---------- Endpoints ---------- #

@router.get("", response_model=ExchangeRatesView)
def get_rates():
    """
    Devuelve las tasas configuradas de forma estática.

    GET /api/v1/exchange
    """
    return ExchangeRatesView(base=BASE_CURRENCY, rates=RATES)


@router.get("/convert", response_model=ConvertResult)
def convert_currency(
    from_currency: str = Query(..., description="Moneda origen, ej: USD"),
    to_currency: str = Query(..., description="Moneda destino, ej: VES"),
    amount: float = Query(..., gt=0, description="Cantidad a convertir"),
):
    """
    Convierte un monto entre dos monedas usando las tasas estáticas internas.

    Convierte en 2 pasos:
      - amount FROM -> USD
      - USD -> TO

    GET /api/v1/exchange/convert?from=USD&to=VES&amount=100
    """
    f = from_currency.strip().upper()
    t = to_currency.strip().upper()

    if f not in RATES:
        raise HTTPException(status_code=400, detail=f"Moneda origen no soportada: {f}")
    if t not in RATES:
        raise HTTPException(status_code=400, detail=f"Moneda destino no soportada: {t}")

    # 1) Pasar a USD
    #    Si 1 USD = RATES[f] unidades de FROM,
    #    entonces amount FROM = amount / RATES[f] USD
    amount_in_usd = amount / RATES[f]

    # 2) De USD a TO
    #    1 USD = RATES[t] unidades de TO
    result_amount = amount_in_usd * RATES[t]

    # Tasa efectiva FROM -> TO
    rate_from_to = RATES[t] / RATES[f]

    return ConvertResult(
        from_currency=f,
        to_currency=t,
        amount=amount,
        rate_used=rate_from_to,
        result=result_amount,
    )

