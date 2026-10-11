from datetime import date, timedelta
from math import ceil

from sqlalchemy import delete, func, select, tuple_
from sqlalchemy.orm import Session

from app.models import SKU, Forecast, Sale, StaffingPlan


class MissingForecasts(Exception):
    """Some SKUs sold in the store have no forecast covering every day of the requested range."""

    def __init__(self, sku_codes: list[str]):
        super().__init__(f"Missing forecasts for SKUs: {', '.join(sku_codes)}")
        self.sku_codes = sku_codes


def staff_needed(units: int, service_minutes_per_unit: float, shift_hours: float, min_staff: int, max_staff: int) -> int:
    """Shifts needed to serve `units` (units x minutes per unit / shift minutes, rounded up), clamped to [min, max]."""
    staff = ceil(units * service_minutes_per_unit / (shift_hours * 60))
    return max(min_staff, min(max_staff, staff))


def latest_forecasts(db: Session, store_id: int, start: date, end: date) -> dict[int, dict[date, int]]:
    """{sku_id: {day: units}} from the most recent forecast run of each SKU, limited to [start, end]."""
    # Rows of a run are inserted together, so the run holding the highest id is the latest one.
    newest_row = select(func.max(Forecast.id)).where(Forecast.store_id == store_id).group_by(Forecast.sku_id)
    latest_runs = select(Forecast.sku_id, Forecast.run_id).where(Forecast.id.in_(newest_row))
    rows = db.execute(
        select(Forecast.sku_id, Forecast.d, Forecast.units).where(
            Forecast.store_id == store_id,
            tuple_(Forecast.sku_id, Forecast.run_id).in_(latest_runs),
            Forecast.d.between(start, end),
        )
    ).all()
    out: dict[int, dict[date, int]] = {}
    for sku_id, d, units in rows:
        out.setdefault(sku_id, {})[d] = units
    return out


def staffing_from_forecast(
    db: Session,
    store_id: int,
    start: date,
    end: date,
    service_minutes_per_unit: float,
    shift_hours: float,
    min_staff: int,
    max_staff: int,
) -> list[StaffingPlan]:
    """One plan per day in [start, end], from the summed latest forecasts of every SKU sold in the store.

    Raises ValueError if the store has no sales, MissingForecasts if any of its SKUs is not forecast for
    every day of the range. Re-running replaces earlier plans for the same store and dates.
    """
    sku_codes = dict(
        db.execute(select(SKU.id, SKU.code).where(SKU.id.in_(select(Sale.sku_id).where(Sale.store_id == store_id)))).all()
    )
    if not sku_codes:
        raise ValueError("No sales history for this store")

    days = [start + timedelta(days=i) for i in range((end - start).days + 1)]
    forecasts = latest_forecasts(db, store_id, start, end)
    missing = sorted(code for sku_id, code in sku_codes.items() if len(forecasts.get(sku_id, {})) < len(days))
    if missing:
        raise MissingForecasts(missing)

    db.execute(delete(StaffingPlan).where(StaffingPlan.store_id == store_id, StaffingPlan.d.in_(days)))
    plans = [
        StaffingPlan(
            store_id=store_id,
            d=d,
            staff_required=staff_needed(
                sum(f[d] for f in forecasts.values()), service_minutes_per_unit, shift_hours, min_staff, max_staff
            ),
            min_staff=min_staff,
            max_staff=max_staff,
        )
        for d in days
    ]
    db.add_all(plans)
    db.commit()
    return plans
