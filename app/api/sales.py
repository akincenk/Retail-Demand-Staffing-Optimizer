from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import SKU, Sale, Store
from app.schemas.sale import SaleIngest

router = APIRouter()


@router.post("/ingest", status_code=201)
def ingest_sales(payload: SaleIngest, db: Session = Depends(get_db)):
    """All-or-nothing: if any item references an unknown store or SKU, nothing is saved."""
    stores = dict(db.execute(select(Store.code, Store.id)).all())
    skus = dict(db.execute(select(SKU.code, SKU.id)).all())
    for i, item in enumerate(payload.items):
        if item.store_code not in stores or item.sku_code not in skus:
            raise HTTPException(status_code=400, detail=f"items[{i}]: unknown store_code or sku_code")
    db.add_all(
        Sale(store_id=stores[it.store_code], sku_id=skus[it.sku_code], d=it.d, units=it.units) for it in payload.items
    )
    db.commit()
    return {"status": "ok", "count": len(payload.items)}
