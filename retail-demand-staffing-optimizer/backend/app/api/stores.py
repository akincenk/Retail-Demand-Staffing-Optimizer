from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.db.session import get_db
from app.models.store import Store
from app.schemas.store import StoreCreate, StoreOut

router = APIRouter()

@router.get("", response_model=list[StoreOut])
def list_stores(db: Session = Depends(get_db)):
    return list(db.execute(select(Store).order_by(Store.id)).scalars().all())

@router.post("", response_model=StoreOut, status_code=201)
def create_store(payload: StoreCreate, db: Session = Depends(get_db)):
    exists = db.execute(select(Store).where(Store.code == payload.code)).scalar()
    if exists:
        raise HTTPException(status_code=409, detail="Store code exists")
    store = Store(code=payload.code, name=payload.name)
    db.add(store); db.commit(); db.refresh(store)
    return store
