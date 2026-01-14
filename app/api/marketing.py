# app/api/marketing.py
from typing import Any, Dict, List, Optional
import requests
import os

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app import models
from app.api.auth import get_current_active_user # Importamos seguridad

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
        from_attributes = True


def build_page(
    items: List[models.Marketing],
    page: int,
    elements: int,
    total: int,
) -> Dict[str, Any]:
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

# 🔥 1. ENDPOINT DE SALDO EXTERNO (LEGION)
# IMPORTANTE: Debe ir ANTES de /{id} para evitar conflictos de rutas
@router.get("/marketing/balance")
def get_marketing_external_balance(current_user: dict = Depends(get_current_active_user)):
    """
    Consulta el saldo real en la API de Legion/SMM.
    """
    # 1. Seguridad: Solo Admin/Superuser
    if current_user.get("role") not in ["SUPERUSER", "ADMIN"]:
        raise HTTPException(status_code=403, detail="No autorizado")

    try:
        # 2. Credenciales
        api_url = os.getenv("LEGION_URL", "https://legion-smm.com/api/v2")
        api_key = os.getenv("LEGION_API_KEY")

        if not api_key:
            return {"balance": 0.00, "currency": "USD", "error": "Falta API Key"}

        # 3. Petición a Legion
        payload = {
            "key": api_key,
            "action": "balance"
        }
        
        # Timeout de 10s para no colgar el server
        response = requests.post(api_url, json=payload, timeout=10)

        if response.status_code == 200:
            data = response.json()
            saldo = data.get("balance") or 0.00
            return {"balance": float(saldo), "currency": "USD"}
        
        return {"balance": 0.00, "currency": "USD", "error": f"Status {response.status_code}"}

    except Exception as e:
        print(f"Error Marketing External: {e}")
        return {"balance": 0.00, "currency": "USD", "error": "Error de conexión"}


# 🔥 2. ENDPOINTS LOCALES (DB)

@router.get("/marketing")
def get_all_marketing(
    query: str = Query("", description="texto de búsqueda"),
    page: int = Query(0, ge=0),
    elements: int = Query(10, ge=1),
    db: Session = Depends(get_db),
):
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
    q = db.query(models.Marketing)

    if query:
        like = f"%{query}%"
        q = q.filter(
            (models.Marketing.name.ilike(like)) |
            (models.Marketing.description.ilike(like))
        )

    items = q.order_by(models.Marketing.id.desc()).all()
    total = len(items)
    # Ajuste para evitar división por cero en build_page si elements es 0
    size = total if total > 0 else 10
    return build_page(items, page=0, elements=size, total=total)


@router.get("/marketing/{id}", response_model=MarketingView)
def get_marketing_by_id(id: int, db: Session = Depends(get_db)):
    obj = db.query(models.Marketing).filter(models.Marketing.id == id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Marketing no encontrado")
    return obj


@router.post("/marketing", response_model=MarketingView)
def create_marketing(body: MarketingCreate, db: Session = Depends(get_db)):
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
    obj = db.query(models.Marketing).filter(models.Marketing.id == id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Marketing no encontrado")

    db.delete(obj)
    db.commit()
    return {"detail": "Marketing eliminado correctamente"}

