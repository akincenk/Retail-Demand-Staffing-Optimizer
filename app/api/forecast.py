from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.lookup import get_sku, get_store
from app.db.session import get_db
from app.schemas.forecast import ForecastOut
from app.services.forecasting import moving_average_forecast

router = APIRouter()


@router.post("/run", response_model=list[ForecastOut])
def run_forecast(
    store_code: str = Query(...),
    sku_code: str = Query(...),
    window: int = Query(7, ge=1, le=60),
    horizon: int = Query(7, ge=1, le=30),
    db: Session = Depends(get_db),
):
    store, sku = get_store(db, store_code), get_sku(db, sku_code)
    try:
        return moving_average_forecast(db, store.id, sku.id, window=window, horizon=horizon)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"{e} for this store/SKU") from e
