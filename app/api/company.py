# app/api/company.py
#
# Información de la compañía.
#
#   GET /api/v1/company

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class CompanyView(BaseModel):
    name: str
    nit: str
    address: str
    phone: str
    email: str
    website: str
    logo_url: str | None = None


@router.get("", response_model=CompanyView)
def get_company():
    """
    De momento devolvemos datos estáticos.
    Más adelante puedes mover esto a BD si quieres.
    """
    return CompanyView(
        name="Moto Store LLC | Soluciones Digitales 24/7",
        nit="NIT / RUT PENDIENTE",
        address="Remoto / Online",
        phone="+57 000 000 0000",
        email="soporte@motostore.com",
        website="https://motostore.com",
        logo_url="https://motostore.com/logo.png",  # pon aquí la URL real si la tienes
    )
