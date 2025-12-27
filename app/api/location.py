# app/api/location.py
#
# Localización básica (países y ciudades).
#
#   GET /api/v1/location/countries           -> todos los países
#   GET /api/v1/location/cities             -> todas las ciudades de todos los países
#   GET /api/v1/location/cities?country=CO
#   GET /api/v1/location/cities?country_code=CO

from typing import List, Dict, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

router = APIRouter()

# --------- Datos estáticos iniciales (puedes ampliar cuando quieras) --------- #

COUNTRIES = [
    {"code": "CO", "name": "Colombia"},
    {"code": "VE", "name": "Venezuela"},
    {"code": "MX", "name": "México"},
    {"code": "US", "name": "Estados Unidos"},
    {"code": "ES", "name": "España"},
]

CITIES_BY_COUNTRY: Dict[str, list[dict]] = {
    "CO": [
        {"name": "Bogotá", "code": "BOG"},
        {"name": "Medellín", "code": "MDE"},
        {"name": "Cali", "code": "CLO"},
        {"name": "Barranquilla", "code": "BAQ"},
    ],
    "VE": [
        {"name": "Caracas", "code": "CCS"},
        {"name": "Valencia", "code": "VLN"},
        {"name": "Maracaibo", "code": "MAR"},
    ],
    "MX": [
        {"name": "Ciudad de México", "code": "CDMX"},
        {"name": "Guadalajara", "code": "GDL"},
        {"name": "Monterrey", "code": "MTY"},
    ],
    "US": [
        {"name": "Miami", "code": "MIA"},
        {"name": "New York", "code": "NYC"},
        {"name": "Los Angeles", "code": "LAX"},
    ],
    "ES": [
        {"name": "Madrid", "code": "MAD"},
        {"name": "Barcelona", "code": "BCN"},
        {"name": "Valencia", "code": "VLC"},
    ],
}


# --------- Schemas Pydantic --------- #

class CountryView(BaseModel):
    code: str
    name: str


class CityView(BaseModel):
    code: str
    name: str
    country_code: str


# --------- Endpoints --------- #

@router.get("/countries", response_model=List[CountryView])
def list_countries():
    """
    Devuelve la lista de países disponibles.
    """
    return [CountryView(**c) for c in COUNTRIES]


@router.get("/cities", response_model=List[CityView])
def list_cities(
    country: Optional[str] = Query(
        default=None,
        description="Código de país (ej: CO, VE, MX)",
    ),
    country_code: Optional[str] = Query(
        default=None,
        description="Alias de country, por compatibilidad",
    ),
):
    """
    Devuelve la lista de ciudades.

    - Si envías country o country_code → solo ciudades de ese país.
    - Si NO envías nada → todas las ciudades de todos los países.
    """
    raw = country or country_code

    # Caso PRO: sin filtro → todas las ciudades
    if not raw:
        all_cities: List[CityView] = []
        for code, cities in CITIES_BY_COUNTRY.items():
            for city in cities:
                all_cities.append(
                    CityView(code=city["code"], name=city["name"], country_code=code)
                )
        return all_cities

    # Caso con filtro por país
    code = raw.strip().upper()
    if code not in CITIES_BY_COUNTRY:
        raise HTTPException(status_code=404, detail="País no soportado")

    cities = CITIES_BY_COUNTRY[code]
    return [
        CityView(code=city["code"], name=city["name"], country_code=code)
        for city in cities
    ]

