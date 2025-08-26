from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.db.session import get_db
from app.models import Store, SKU, Sale
from app.schemas.sale import SaleIngest

router = APIRouter()

@router.post("/ingest", status_code=201)
def ingest_sales(payload: SaleIngest, db: Session = Depends(get_db)):
    for item in payload.items:
        store = db.execute(select(Store).where(Store.code == item.store_code)).scalar()
        sku = db.execute(select(SKU).where(SKU.code == item.sku_code)).scalar()
        if not store or not sku:
            raise HTTPException(status_code=400, detail="Invalid store_code or sku_code")
        db.add(Sale(store_id=store.id, sku_id=sku.id, d=item.d, units=item.units))
    db.commit()
    return {"status": "ok", "count": len(payload.items)}
