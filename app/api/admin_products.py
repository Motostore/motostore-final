# app/api/admin_products.py
#
# Productos para la vista de administrador.
# El frontend llama:
#   GET /api/v1/admin/products
#
# Devolvemos todos los productos (activos e inactivos)
# con estructura tipo Page<>.

from typing import Any, Dict, List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app import models

router = APIRouter()


def build_page(
    items: List[models.Product],
    page: int,
    elements: int,
    total: int,
) -> Dict[str, Any]:
    total_pages = 0
    if elements > 0:
        total_pages = (total + elements - 1) // elements

    content = [
        {
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "price": p.price,
            "active": p.active,
            "category_id": p.category_id,
        }
        for p in items
    ]

    return {
        "content": content,
        "number": page,
        "size": elements,
        "totalElements": total,
        "totalPages": total_pages,
        "empty": len(content) == 0,
    }


@router.get("/admin/products")
def get_admin_products(
    query: str = Query("", description="texto de búsqueda"),
    db: Session = Depends(get_db),
):
    """
    GET /api/v1/admin/products
    Devuelve todos los productos (activos o no),
    para que el administrador pueda ver/editar todo.
    """
    q = db.query(models.Product)

    if query:
        like = f"%{query}%"
        q = q.filter(
            (models.Product.name.ilike(like)) |
            (models.Product.description.ilike(like))
        )

    items = q.order_by(models.Product.id.desc()).all()
    total = len(items)
    elements = total if total > 0 else 10

    return build_page(items, page=0, elements=elements, total=total)
