# app/api/streaming.py
#
# Endpoints "fake" para streaming, para que el panel deje de mostrar 404.
#
# En los logs vimos llamadas tipo:
#   /api/v1/streaming
#   /api/v1/streaming/providers
#   /api/v1/streaming_provider
#
# Aquí devolvemos datos en memoria (sin DB) suficientes para que el frontend pinte tablas/listas.

from typing import List

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


# ---------- MODELOS Pydantic ---------- #

class StreamingProvider(BaseModel):
    id: int
    name: str
    country: str
    active: bool = True


class StreamingPlan(BaseModel):
    id: int
    provider_id: int
    name: str
    price: float
    resolution: str  # "HD", "4K", etc.
    screens: int
    active: bool = True


# 🔹 Datos de ejemplo (en memoria, sin DB)

_fake_providers: List[StreamingProvider] = [
    StreamingProvider(id=1, name="Netflix", country="Global", active=True),
    StreamingProvider(id=2, name="Disney+", country="Global", active=True),
    StreamingProvider(id=3, name="HBO Max", country="Global", active=True),
]

_fake_plans: List[StreamingPlan] = [
    StreamingPlan(id=1, provider_id=1, name="Básico", price=6.99, resolution="HD", screens=1, active=True),
    StreamingPlan(id=2, provider_id=1, name="Estándar", price=10.99, resolution="Full HD", screens=2, active=True),
    StreamingPlan(id=3, provider_id=2, name="Estándar Disney", price=9.99, resolution="HD", screens=4, active=True),
]


# ---------- ENDPOINTS ---------- #

@router.get("/streaming")
def get_all_streaming():
    """
    GET /api/v1/streaming

    Podemos devolver un combo de providers + plans,
    o solo planes según lo que el frontend espere.
    Para simplificar devolvemos un objeto con ambos.
    """
    return {
        "providers": _fake_providers,
        "plans": _fake_plans,
    }


@router.get("/streaming/providers", response_model=List[StreamingProvider])
def get_streaming_providers():
    """
    GET /api/v1/streaming/providers
    """
    return _fake_providers


@router.get("/streaming_provider")
def get_streaming_providers_alias():
    """
    GET /api/v1/streaming_provider
    Alias por si el frontend usa esta ruta.
    """
    return _fake_providers
