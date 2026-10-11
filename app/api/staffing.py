from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.lookup import get_store
from app.db.session import get_db
from app.schemas.staffing import StaffingOut
from app.services.staffing import staffing_from_forecast

router = APIRouter()


@router.post("/plan", response_model=list[StaffingOut])
def plan_staffing(
    store_code: str = Query(...),
    service_minutes_per_unit: float = Query(0.5, gt=0.0),
    shift_hours: float = Query(8.0, gt=0.0, le=24.0),
    min_staff: int = Query(2, ge=0),
    max_staff: int = Query(20, ge=1),
    db: Session = Depends(get_db),
):
    if min_staff > max_staff:
        raise HTTPException(status_code=400, detail="min_staff cannot exceed max_staff")
    store = get_store(db, store_code)
    return staffing_from_forecast(db, store.id, service_minutes_per_unit, shift_hours, min_staff, max_staff)
