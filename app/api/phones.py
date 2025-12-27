# app/api/phones.py
#
# Teléfonos de los usuarios.
#
#   GET /api/v1/phones?user_id=1

from typing import List, Optional
from fastapi import APIRouter, Query
from pydantic import BaseModel

router = APIRouter()


class PhoneRead(BaseModel):
    id: int
    user_id: int
    phone: str
    type: str  # MOBILE / HOME / WORK


@router.get("", response_model=List[PhoneRead])
def list_phones(
    user_id: Optional[int] = Query(None, description="ID del usuario"),
):
    # Stub por ahora
    return []
