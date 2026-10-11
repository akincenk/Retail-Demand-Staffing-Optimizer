from datetime import date
from math import ceil

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models import Forecast, StaffingPlan


def staff_needed(units: int, service_minutes_per_unit: float, shift_hours: float, min_staff: int, max_staff: int) -> int:
    """Shifts needed to serve `units` (units x minutes per unit / shift minutes, rounded up), clamped to [min, max]."""
    staff = ceil(units * service_minutes_per_unit / (shift_hours * 60))
    return max(min_staff, min(max_staff, staff))


def staffing_from_forecast(
    db: Session, store_id: int, service_minutes_per_unit: float, shift_hours: float, min_staff: int, max_staff: int
) -> list[StaffingPlan]:
    """One plan per forecast day, using the summed forecast units of all SKUs in the store.

    Re-running replaces earlier plans for the same store and dates.
    """
    rows = db.execute(select(Forecast.d, Forecast.units).where(Forecast.store_id == store_id)).all()
    daily: dict[date, int] = {}
    for d, units in rows:
        daily[d] = daily.get(d, 0) + units
    if not daily:
        return []

    db.execute(delete(StaffingPlan).where(StaffingPlan.store_id == store_id, StaffingPlan.d.in_(list(daily))))
    plans = [
        StaffingPlan(
            store_id=store_id,
            d=d,
            staff_required=staff_needed(units, service_minutes_per_unit, shift_hours, min_staff, max_staff),
            min_staff=min_staff,
            max_staff=max_staff,
        )
        for d, units in sorted(daily.items())
    ]
    db.add_all(plans)
    db.commit()
    return plans
