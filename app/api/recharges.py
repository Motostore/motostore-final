# app/api/recharges.py
#
# Recharges conectadas a DB y a la Tesorería (Exchange).
#
# Endpoints:
#   GET    /api/v1/recharge
#   POST   /api/v1/recharge
#   GET    /api/v1/recharge/calculate?amount=10&currency=COP  <-- NUEVO (Calculadora)

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app import models

# 1. IMPORTAMOS LA CONEXIÓN CON TESORERÍA (Exchange)
from app.api.exchange import get_dynamic_rates_dict

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
    
    # Campo extra para mostrar precio local (opcional)
    local_price_estimated: Optional[str] = None 

    class Config:
        from_attributes = True

# Esquema para la respuesta de la calculadora
class CalculatorResponse(BaseModel):
    amount_usd: float
    currency_requested: str
    rate_used: float
    local_amount: float


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
    Obtiene todas las opciones de recarga.
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


# ---------- 2. NUEVA CALCULADORA AUTOMÁTICA (EL CEREBRO) ---------- #
@router.get("/recharge/calculate", response_model=CalculatorResponse)
def calculate_local_price(
    amount_usd: float = Query(..., description="Monto en Dólares (ej: 10)"),
    currency: str = Query(..., description="Moneda local (ej: COP, CLP, PEN, VES)")
):
    """
    Calcula cuánto debe pagar el usuario en su moneda local
    basado en las tasas actuales de Tesorería.
    
    Uso: /api/v1/recharge/calculate?amount=10&currency=COP
    """
    # A. Leemos las tasas de Tesorería (El archivo JSON)
    rates = get_dynamic_rates_dict()
    
    # B. Buscamos la tasa (Si no existe, usamos 1.0)
    code = currency.upper().strip()
    rate = rates.get(code, 0)
    
    if rate == 0:
        # Si no encuentra la moneda, asumimos USD 1:1 o lanzamos error
        rate = 1.0
        
    # C. Hacemos la matemática (USD * Tasa)
    local_amount = amount_usd * rate
    
    # Redondeamos según la moneda (COP/CLP sin decimales, el resto con 2)
    if code in ['COP', 'CLP', 'VES']:
         local_amount = round(local_amount, 2)
    else:
         local_amount = round(local_amount, 2)

    return CalculatorResponse(
        amount_usd=amount_usd,
        currency_requested=code,
        rate_used=rate,
        local_amount=local_amount
    )


@router.get("/recharge/{id}", response_model=RechargeView)
def get_recharge_by_id(id: int, db: Session = Depends(get_db)):
    obj = db.query(models.Recharge).filter(models.Recharge.id == id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Recarga no encontrada")
    return obj


@router.post("/recharge", response_model=RechargeView)
def create_recharge(body: RechargeCreate, db: Session = Depends(get_db)):
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
    obj = db.query(models.Recharge).filter(models.Recharge.id == id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Recarga no encontrada")

    db.delete(obj)
    db.commit()
    return {"detail": "Recarga eliminada correctamente"}


# ---------- ALIAS PARA EL FRONTEND ---------- #

@router.get("/recharges")
def get_all_recharges_alias(
    query: str = Query("", description="texto de búsqueda"),
    page: int = Query(0, ge=0),
    elements: int = Query(10, ge=1),
    db: Session = Depends(get_db),
):
    return get_all_recharge(query=query, page=page, elements=elements, db=db)


@router.get("/recharges/all")
def get_all_recharges_all_alias(
    query: str = Query("", description="texto de búsqueda"),
    db: Session = Depends(get_db),
):
    q = db.query(models.Recharge)
    if query:
        like = f"%{query}%"
        q = q.filter(models.Recharge.name.ilike(like))
    items = q.order_by(models.Recharge.id.desc()).all()
    
    # Opcional: Podríamos inyectar precios estimados aquí si quisiéramos
    total = len(items)
    return build_page(items, page=0, elements=total if total > 0 else 10, total=total)

