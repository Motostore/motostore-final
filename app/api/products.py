# app/api/products.py
#
# Rutas reales (porque en main.py usas prefix="/api/v1/products"):
#
#   GET    /api/v1/products               -> list_products
#   GET    /api/v1/products/all           -> list_products_all (tipo Page<>)
#   GET    /api/v1/products/{product_id}  -> get_product
#   POST   /api/v1/products               -> create_product
#   PUT    /api/v1/products/{product_id}  -> update_product
#   DELETE /api/v1/products/{product_id}  -> delete_product
#
# Esto evita el error 422 cuando el frontend llama a /api/v1/products/all
# porque ahora existe un endpoint específico /all que se define ANTES que /{product_id}.

from typing import Optional, List, Any, Dict

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app import models

router = APIRouter()


# --------- Esquemas Pydantic (entrada / salida) ---------

class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    active: bool = True
    category_id: Optional[int] = None  # id de la categoría


class ProductCreate(ProductBase):
    pass


class ProductUpdate(ProductBase):
    pass


class ProductRead(ProductBase):
    id: int

    class Config:
        from_attributes = True  # equivalente moderno a orm_mode=True


# --------- Helper para estructura tipo Page<> ---------

def build_page(
    items: List[models.Product],
    page: int,
    elements: int,
    total: int,
) -> Dict[str, Any]:
    total_pages = 0
    if elements > 0:
        total_pages = (total + elements - 1) // elements

    content = [ProductRead.model_validate(p) for p in items]

    return {
        "content": content,
        "number": page,
        "size": elements,
        "totalElements": total,
        "totalPages": total_pages,
        "empty": len(content) == 0,
    }


# --------- Endpoints ---------

# ⚠️ IMPORTANTE: /all VA ANTES QUE /{product_id}
# para que FastAPI no intente interpretar "all" como un product_id entero.

# GET /api/v1/products/all
@router.get("/all")
def list_products_all(
    q: Optional[str] = Query(default=None, description="Texto de búsqueda"),
    db: Session = Depends(get_db),
):
    """
    GET /api/v1/products/all

    Endpoint pensado para el frontend que espera una estructura tipo Page<>.
    No hacemos paginación real, pero devolvemos:

    {
      "content": [...],
      "number": 0,
      "size": N,
      "totalElements": N,
      "totalPages": 1,
      "empty": false
    }
    """
    query_db = db.query(models.Product)

    if q:
        like = f"%{q}%"
        query_db = query_db.filter(models.Product.name.ilike(like))

    items = query_db.order_by(models.Product.id.desc()).all()
    total = len(items)
    elements = total if total > 0 else 10

    return build_page(items, page=0, elements=elements, total=total)


# GET /api/v1/products?category_id=&q=
@router.get("", response_model=List[ProductRead])
def list_products(
    category_id: Optional[int] = Query(default=None),
    q: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    """
    Devuelve una lista simple de productos (sin estructura Page).
    Esta ruta ya la tenías y la dejamos igual para no romper el frontend.
    """
    query_db = db.query(models.Product)

    if category_id is not None:
        query_db = query_db.filter(models.Product.category_id == category_id)

    if q:
        like = f"%{q}%"
        query_db = query_db.filter(models.Product.name.ilike(like))

    return query_db.all()


# GET /api/v1/products/{product_id}
@router.get("/{product_id}", response_model=ProductRead)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = (
        db.query(models.Product)
        .filter(models.Product.id == product_id)
        .first()
    )
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return product


# POST /api/v1/products
@router.post("", response_model=ProductRead)
def create_product(product_in: ProductCreate, db: Session = Depends(get_db)):
    product = models.Product(**product_in.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


# PUT /api/v1/products/{product_id}
@router.put("/{product_id}", response_model=ProductRead)
def update_product(
    product_id: int, product_in: ProductUpdate, db: Session = Depends(get_db)
):
    product = (
        db.query(models.Product)
        .filter(models.Product.id == product_id)
        .first()
    )
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    for field, value in product_in.model_dump().items():
        setattr(product, field, value)

    db.commit()
    db.refresh(product)
    return product


# DELETE /api/v1/products/{product_id}
@router.delete("/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db)):
    product = (
        db.query(models.Product)
        .filter(models.Product.id == product_id)
        .first()
    )
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    db.delete(product)
    db.commit()
    return {"message": "Producto eliminado"}



