# app/api/marketing.py
#
# Marketing conectado a DB.
# Endpoints:
#   GET    /api/v1/marketing
#   GET    /api/v1/marketing/all
#   GET    /api/v1/marketing/{id}
#   POST   /api/v1/marketing
#   PUT    /api/v1/marketing/{id}
#   DELETE /api/v1/marketing/{id}
#
# En main.py ya tienes algo como:
#   app.include_router(marketing.router, prefix="/api/v1", tags=["marketing"])

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app import models

router = APIRouter()


# ---------- ESQUEMAS Pydantic ---------- #

class MarketingBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: Optional[float] = None
    active: bool = True


class MarketingCreate(MarketingBase):
    pass


class MarketingUpdate(MarketingBase):
    pass


class MarketingView(MarketingBase):
    id: int

    class Config:
        from_attributes = True  # Pydantic v2 (antes orm_mode=True)


def build_page(
    items: List[models.Marketing],
    page: int,
    elements: int,
    total: int,
) -> Dict[str, Any]:
    """
    Objeto tipo Page<> como en Spring:
    {
      "content": [...],
      "number": page,
      "size": elements,
      "totalElements": total,
      "totalPages": ...,
      "empty": bool
    }
    """
    total_pages = 0
    if elements > 0:
        total_pages = (total + elements - 1) // elements

    content = [MarketingView.model_validate(m) for m in items]

    return {
        "content": content,
        "number": page,
        "size": elements,
        "totalElements": total,
        "totalPages": total_pages,
        "empty": len(content) == 0,
    }


# ---------- ENDPOINTS ---------- #

@router.get("/marketing")
def get_all_marketing(
    query: str = Query("", description="texto de búsqueda"),
    page: int = Query(0, ge=0),
    elements: int = Query(10, ge=1),
    db: Session = Depends(get_db),
):
    """
    GET /api/v1/marketing?query=&page=0&elements=10

    Equivalente a marketingService.findAll(query, page, elements)
    """
    q = db.query(models.Marketing)

    if query:
        like = f"%{query}%"
        q = q.filter(
            (models.Marketing.name.ilike(like)) |
            (models.Marketing.description.ilike(like))
        )

    total = q.with_entities(func.count(models.Marketing.id)).scalar() or 0

    items = (
        q.order_by(models.Marketing.id.desc())
        .offset(page * elements)
        .limit(elements)
        .all()
    )

    return build_page(items, page, elements, total)


@router.get("/marketing/all")
def get_all_marketing_all(
    query: str = Query("", description="texto de búsqueda"),
    db: Session = Depends(get_db),
):
    """
    GET /api/v1/marketing/all
    Alias para el frontend (sin paginación dura).
    """
    q = db.query(models.Marketing)

    if query:
        like = f"%{query}%"
        q = q.filter(
            (models.Marketing.name.ilike(like)) |
            (models.Marketing.description.ilike(like))
        )

    items = q.order_by(models.Marketing.id.desc()).all()
    total = len(items)
    return build_page(items, page=0, elements=total if total > 0 else 10, total=total)


@router.get("/marketing/{id}", response_model=MarketingView)
def get_marketing_by_id(id: int, db: Session = Depends(get_db)):
    """
    GET /api/v1/marketing/{id}
    """
    obj = db.query(models.Marketing).filter(models.Marketing.id == id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Marketing no encontrado")
    return obj


@router.post("/marketing", response_model=MarketingView)
def create_marketing(body: MarketingCreate, db: Session = Depends(get_db)):
    """
    POST /api/v1/marketing
    Crea un registro real en la tabla marketing.
    """
    obj = models.Marketing(
        name=body.name,
        description=body.description,
        price=body.price,
        active=body.active,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.put("/marketing/{id}", response_model=MarketingView)
def update_marketing(
    id: int,
    body: MarketingUpdate,
    db: Session = Depends(get_db),
):
    """
    PUT /api/v1/marketing/{id}
    """
    obj = db.query(models.Marketing).filter(models.Marketing.id == id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Marketing no encontrado")

    obj.name = body.name
    obj.description = body.description
    obj.price = body.price
    obj.active = body.active

    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/marketing/{id}")
def delete_marketing(id: int, db: Session = Depends(get_db)):
    """
    DELETE /api/v1/marketing/{id}
    """
    obj = db.query(models.Marketing).filter(models.Marketing.id == id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Marketing no encontrado")

    db.delete(obj)
    db.commit()
    return {"detail": "Marketing eliminado correctamente"}

