from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.forecasting import moving_average_forecast
from app.schemas.forecast import ForecastOut

router = APIRouter()

@router.post("/run", response_model=list[ForecastOut])
def run_forecast(
    store_code: str = Query(...),
    sku_code: str = Query(...),
    window: int = Query(7, ge=1, le=60),
    horizon: int = Query(7, ge=1, le=30),
    db: Session = Depends(get_db),
):
    try:
        created = moving_average_forecast(db, store_code, sku_code, window=window, horizon=horizon)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return created
