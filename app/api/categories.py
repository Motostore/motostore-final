from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy.orm import Session

from app.core.database import get_db
from app import models

router = APIRouter()


# --------- Esquemas Pydantic ---------

class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(CategoryBase):
    pass


class CategoryRead(CategoryBase):
    id: int

    class Config:
        from_attributes = True


# --------- Endpoints ---------

# GET /api/v1/categories
@router.get("", response_model=List[CategoryRead])
def list_categories(db: Session = Depends(get_db)):
    return db.query(models.Category).all()


# GET /api/v1/categories/{category_id}
@router.get("/{category_id}", response_model=CategoryRead)
def get_category(category_id: int, db: Session = Depends(get_db)):
    category = (
        db.query(models.Category)
        .filter(models.Category.id == category_id)
        .first()
    )
    if not category:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    return category


# POST /api/v1/categories
@router.post("", response_model=CategoryRead)
def create_category(category_in: CategoryCreate, db: Session = Depends(get_db)):
    category = models.Category(**category_in.dict())
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


# PUT /api/v1/categories/{category_id}
@router.put("/{category_id}", response_model=CategoryRead)
def update_category(
    category_id: int, category_in: CategoryUpdate, db: Session = Depends(get_db)
):
    category = (
        db.query(models.Category)
        .filter(models.Category.id == category_id)
        .first()
    )
    if not category:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")

    for field, value in category_in.dict().items():
        setattr(category, field, value)

    db.commit()
    db.refresh(category)
    return category


# DELETE /api/v1/categories/{category_id}
@router.delete("/{category_id}")
def delete_category(category_id: int, db: Session = Depends(get_db)):
    category = (
        db.query(models.Category)
        .filter(models.Category.id == category_id)
        .first()
    )
    if not category:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")

    db.delete(category)
    db.commit()
    return {"message": "Categoría eliminada"}
