from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.lookup import get_store
from app.db.session import get_db
from app.schemas.staffing import StaffingOut
from app.services.staffing import MissingForecasts, staffing_from_forecast

router = APIRouter()

MAX_RANGE_DAYS = 92


@router.post("/plan", response_model=list[StaffingOut])
def plan_staffing(
    store_code: str = Query(...),
    start: date = Query(..., description="First day to plan (inclusive)"),
    end: date = Query(..., description="Last day to plan (inclusive)"),
    service_minutes_per_unit: float = Query(0.5, gt=0.0),
    shift_hours: float = Query(8.0, gt=0.0, le=24.0),
    min_staff: int = Query(2, ge=0),
    max_staff: int = Query(20, ge=1),
    db: Session = Depends(get_db),
):
    if min_staff > max_staff:
        raise HTTPException(status_code=400, detail="min_staff cannot exceed max_staff")
    if end < start or (end - start).days >= MAX_RANGE_DAYS:
        raise HTTPException(status_code=400, detail=f"end must be on or after start, at most {MAX_RANGE_DAYS} days")
    store = get_store(db, store_code)
    try:
        return staffing_from_forecast(db, store.id, start, end, service_minutes_per_unit, shift_hours, min_staff, max_staff)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except MissingForecasts as e:
        detail = {"message": "Run a forecast covering the whole range for these SKUs first", "missing_skus": e.sku_codes}
        raise HTTPException(status_code=409, detail=detail) from e
