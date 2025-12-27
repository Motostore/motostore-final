# app/api/recharges.py
#
# Recharges conectadas a DB.
# Basado en RechargeController.java (@RequestMapping("/api/v1/recharge"))
#
# Endpoints (con prefix="/api/v1" en main.py):
#   GET    /recharge
#   GET    /recharge/{id}
#   POST   /recharge
#   PUT    /recharge/{id}
#   DELETE /recharge/{id}
#
#   GET    /recharges        (alias para frontend)
#   GET    /recharges/all    (alias para frontend)

from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app import models

router = APIRouter()


# ---------- ESQUEMAS Pydantic ---------- #

class RechargeBase(BaseModel):
    name: str
    amount: float
    active: bool = True


class RechargeCreate(RechargeBase):
    pass


class RechargeUpdate(RechargeBase):
    pass


class RechargeView(RechargeBase):
    id: int

    class Config:
        from_attributes = True


def build_page(
    items: List[models.Recharge],
    page: int,
    elements: int,
    total: int,
) -> Dict[str, Any]:
    total_pages = 0
    if elements > 0:
        total_pages = (total + elements - 1) // elements

    content = [RechargeView.model_validate(r) for r in items]

    return {
        "content": content,
        "number": page,
        "size": elements,
        "totalElements": total,
        "totalPages": total_pages,
        "empty": len(content) == 0,
    }


# ---------- ENDPOINTS BASE: /recharge ---------- #

@router.get("/recharge")
def get_all_recharge(
    query: str = Query("", description="texto de búsqueda"),
    page: int = Query(0, ge=0),
    elements: int = Query(10, ge=1),
    db: Session = Depends(get_db),
):
    """
    GET /api/v1/recharge
    """
    q = db.query(models.Recharge)

    if query:
        like = f"%{query}%"
        q = q.filter(models.Recharge.name.ilike(like))

    total = q.with_entities(func.count(models.Recharge.id)).scalar() or 0

    items = (
        q.order_by(models.Recharge.id.desc())
        .offset(page * elements)
        .limit(elements)
        .all()
    )

    return build_page(items, page, elements, total)


@router.get("/recharge/{id}", response_model=RechargeView)
def get_recharge_by_id(id: int, db: Session = Depends(get_db)):
    """
    GET /api/v1/recharge/{id}
    """
    obj = db.query(models.Recharge).filter(models.Recharge.id == id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Recarga no encontrada")
    return obj


@router.post("/recharge", response_model=RechargeView)
def create_recharge(body: RechargeCreate, db: Session = Depends(get_db)):
    """
    POST /api/v1/recharge
    """
    obj = models.Recharge(
        name=body.name,
        amount=body.amount,
        active=body.active,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.put("/recharge/{id}", response_model=RechargeView)
def update_recharge(
    id: int,
    body: RechargeUpdate,
    db: Session = Depends(get_db),
):
    """
    PUT /api/v1/recharge/{id}
    """
    obj = db.query(models.Recharge).filter(models.Recharge.id == id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Recarga no encontrada")

    obj.name = body.name
    obj.amount = body.amount
    obj.active = body.active

    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/recharge/{id}")
def delete_recharge(id: int, db: Session = Depends(get_db)):
    """
    DELETE /api/v1/recharge/{id}
    """
    obj = db.query(models.Recharge).filter(models.Recharge.id == id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Recarga no encontrada")

    db.delete(obj)
    db.commit()
    return {"detail": "Recarga eliminada correctamente"}


# ---------- ALIAS PARA EL FRONTEND: /recharges ---------- #

@router.get("/recharges")
def get_all_recharges_alias(
    query: str = Query("", description="texto de búsqueda"),
    page: int = Query(0, ge=0),
    elements: int = Query(10, ge=1),
    db: Session = Depends(get_db),
):
    """
    GET /api/v1/recharges
    Alias de /recharge
    """
    return get_all_recharge(query=query, page=page, elements=elements, db=db)


@router.get("/recharges/all")
def get_all_recharges_all_alias(
    query: str = Query("", description="texto de búsqueda"),
    db: Session = Depends(get_db),
):
    """
    GET /api/v1/recharges/all
    """
    q = db.query(models.Recharge)

    if query:
        like = f"%{query}%"
        q = q.filter(models.Recharge.name.ilike(like))

    items = q.order_by(models.Recharge.id.desc()).all()
    total = len(items)
    return build_page(items, page=0, elements=total if total > 0 else 10, total=total)



