from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.db.session import get_db
from app.models.sku import SKU
from app.schemas.sku import SKUCreate, SKUOut

router = APIRouter()

@router.get("", response_model=list[SKUOut])
def list_skus(db: Session = Depends(get_db)):
    return list(db.execute(select(SKU).order_by(SKU.id)).scalars().all())

@router.post("", response_model=SKUOut, status_code=201)
def create_sku(payload: SKUCreate, db: Session = Depends(get_db)):
    exists = db.execute(select(SKU).where(SKU.code == payload.code)).scalar()
    if exists:
        raise HTTPException(status_code=409, detail="SKU code exists")
    sku = SKU(code=payload.code, name=payload.name, category=payload.category)
    db.add(sku); db.commit(); db.refresh(sku)
    return sku
