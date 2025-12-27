# app/api/addresses.py
#
# Direcciones de los usuarios.
#
#   GET /api/v1/addresses?user_id=1

from typing import List, Optional
from fastapi import APIRouter, Query
from pydantic import BaseModel

router = APIRouter()


class AddressRead(BaseModel):
    id: int
    user_id: int
    line1: str
    city: str
    country: str


@router.get("", response_model=List[AddressRead])
def list_addresses(
    user_id: Optional[int] = Query(None, description="ID del usuario"),
):
    # Stub, sin DB aún
    return []
