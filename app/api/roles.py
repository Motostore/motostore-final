# app/api/roles.py
#
# Roles disponibles en el sistema.
#
#   GET /api/v1/roles
#
# Debe coincidir con src/app/lib/roles.ts:
#   SUPERUSER, ADMIN, DISTRIBUTOR, RESELLER, TAQUILLA, CLIENT

from typing import List
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class RoleRead(BaseModel):
    code: str
    name: str
    description: str


@router.get("", response_model=List[RoleRead])
def list_roles():
    """
    Devuelve la lista de roles que el frontend conoce.
    IMPORTANTE: códigos deben coincidir con ROLE_DEF en roles.ts
    """
    return [
        RoleRead(
            code="SUPERUSER",
            name="Superuser",
            description="Control total del sistema",
        ),
        RoleRead(
            code="ADMIN",
            name="Administrador",
            description="Control operativo debajo de Superuser",
        ),
        RoleRead(
            code="DISTRIBUTOR",
            name="Distribuidor",
            description="Puede gestionar su red de distribuidores, taquillas y clientes",
        ),
        RoleRead(
            code="RESELLER",
            name="Reseller",
            description="Puede gestionar taquillas y clientes en su rama",
        ),
        RoleRead(
            code="TAQUILLA",
            name="Taquilla",
            description="Puede crear y gestionar clientes asignados",
        ),
        RoleRead(
            code="CLIENT",
            name="Cliente",
            description="Cliente final, sin permisos de gestión",
        ),
    ]

