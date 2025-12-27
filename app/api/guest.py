# app/api/guest.py
#
# Catálogo público (guest).
# El frontend llama:
#   GET /api/v1/guest/products
#
# Devolvemos productos ACTIVOS con estructura tipo Page<> (compatible con el frontend).

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app import models
from pydantic import BaseModel

router = APIRouter()


# ---------- Esquema público de producto ---------- #

class GuestProductRead(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    price: float
    active: bool
    category_id: Optional[int] = None

    class Config:
        from_attributes = True  # Pydantic v2


# ---------- Helper tipo Page<> ---------- #

def build_page(
    items: List[models.Product],
    page: int,
    elements: int,
    total: int,
) -> Dict[str, Any]:
    """
    Estructura similar a Page<> de Spring:

    {
      "content": [...],
      "number": 0,
      "size": N,
      "totalElements": N,
      "totalPages": 1,
      "empty": false
    }
    """
    total_pages = 0
    if elements > 0:
        total_pages = (total + elements - 1) // elements

    content = [GuestProductRead.model_validate(p) for p in items]

    return {
        "content": content,
        "number": page,
        "size": elements,
        "totalElements": total,
        "totalPages": total_pages,
        "empty": len(content) == 0,
    }


# ---------- Endpoint público ---------- #

# GET /api/v1/guest/products?q=...
@router.get("/products")
def list_guest_products(
    q: Optional[str] = Query(default=None, description="Texto de búsqueda público"),
    db: Session = Depends(get_db),
):
    """
    Lista de productos PÚBLICOS (solo activos), con estructura tipo Page<>.

    - Filtra por 'q' en nombre o descripción (case-insensitive).
    - Solo muestra productos con active == True.
    """
    query_db = db.query(models.Product).filter(models.Product.active == True)  # noqa: E712

    if q:
        like = f"%{q}%"
        query_db = query_db.filter(
            (models.Product.name.ilike(like))
            | (models.Product.description.ilike(like))
        )

    items = query_db.order_by(models.Product.id.desc()).all()
    total = len(items)
    elements = total if total > 0 else 10

    return build_page(items, page=0, elements=elements, total=total)

