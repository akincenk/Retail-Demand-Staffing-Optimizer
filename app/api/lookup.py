from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import SKU, Store


def get_store(db: Session, code: str) -> Store:
    store = db.execute(select(Store).where(Store.code == code)).scalar()
    if store is None:
        raise HTTPException(status_code=404, detail=f"Store '{code}' not found")
    return store


def get_sku(db: Session, code: str) -> SKU:
    sku = db.execute(select(SKU).where(SKU.code == code)).scalar()
    if sku is None:
        raise HTTPException(status_code=404, detail=f"SKU '{code}' not found")
    return sku
