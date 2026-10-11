from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.staffing import staffing_from_forecast
from app.schemas.staffing import StaffingOut

router = APIRouter()

@router.get("/plan", response_model=list[StaffingOut])
def plan_staffing(
    store_code: str = Query(...),
    service_minutes_per_unit: float = Query(0.5, gt=0.0),
    shift_hours: float = Query(8.0, gt=0.0),
    min_staff: int = Query(2, ge=1),
    max_staff: int = Query(20, ge=1),
    db: Session = Depends(get_db),
):
    try:
        plans = staffing_from_forecast(db, store_code, service_minutes_per_unit, shift_hours, min_staff, max_staff)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return plans
