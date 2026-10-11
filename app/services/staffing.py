from math import ceil
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models import Store, Forecast, StaffingPlan

def staffing_from_forecast(db: Session, store_code: str, service_minutes_per_unit: float, shift_hours: float, min_staff: int, max_staff: int) -> list[StaffingPlan]:
    store = db.execute(select(Store).where(Store.code == store_code)).scalar_one()

    rows = db.execute(select(Forecast.d, Forecast.units).where(Forecast.store_id == store.id)).all()
    if not rows:
        return []

    daily = {}
    for d, units in rows:
        daily[d] = daily.get(d, 0) + int(units)

    plans = []
    minutes_per_shift = shift_hours * 60.0
    for d, units in sorted(daily.items()):
        minutes_required = units * service_minutes_per_unit
        staff = ceil(max(minutes_required, 0.0) / minutes_per_shift)
        staff = max(min_staff, min(max_staff, staff))
        plan = StaffingPlan(store_id=store.id, d=d, staff_required=staff, min_staff=min_staff, max_staff=max_staff)
        db.add(plan); plans.append(plan)
    db.commit()
    return plans
