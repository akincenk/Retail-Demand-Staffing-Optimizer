from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.dialects import postgresql, sqlite
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import SKU, Sale, Store
from app.schemas.sale import SaleIngest

router = APIRouter()

_CHUNK = 1000  # keeps each statement under SQLite's bound-parameter limit


@router.post("/ingest", status_code=201)
def ingest_sales(payload: SaleIngest, db: Session = Depends(get_db)):
    """Upsert daily units per (store, SKU, day); re-sending a batch is idempotent.

    All-or-nothing: if any item references an unknown store or SKU, or repeats a (store, SKU, day) already in the
    batch, nothing is saved. An existing row for the same key gets the new units value.
    """
    stores = dict(db.execute(select(Store.code, Store.id)).all())
    skus = dict(db.execute(select(SKU.code, SKU.id)).all())
    rows, seen = [], set()
    for i, item in enumerate(payload.items):
        if item.store_code not in stores or item.sku_code not in skus:
            raise HTTPException(status_code=400, detail=f"items[{i}]: unknown store_code or sku_code")
        key = (stores[item.store_code], skus[item.sku_code], item.d)
        if key in seen:
            raise HTTPException(status_code=400, detail=f"items[{i}]: duplicate store_code/sku_code/d in batch")
        seen.add(key)
        rows.append({"store_id": key[0], "sku_id": key[1], "d": key[2], "units": item.units})

    insert = postgresql.insert if db.get_bind().dialect.name == "postgresql" else sqlite.insert
    for i in range(0, len(rows), _CHUNK):
        stmt = insert(Sale).values(rows[i : i + _CHUNK])
        db.execute(
            stmt.on_conflict_do_update(index_elements=["store_id", "sku_id", "d"], set_={"units": stmt.excluded.units})
        )
    db.commit()
    return {"status": "ok", "count": len(rows)}
