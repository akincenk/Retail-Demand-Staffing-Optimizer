from datetime import date, timedelta
from uuid import uuid4

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models import Forecast, Sale


def moving_average(daily_units: dict[date, int], window: int) -> float:
    """Mean daily units over the last `window` calendar days of history.

    Days without sales inside the window count as zero. If the history is
    shorter than the window, only the days since the first sale are used.
    """
    if not daily_units:
        raise ValueError("No sales history")
    last, first = max(daily_units), min(daily_units)
    start = max(first, last - timedelta(days=window - 1))
    days = (last - start).days + 1
    return sum(u for d, u in daily_units.items() if d >= start) / days


def moving_average_forecast(db: Session, store_id: int, sku_id: int, window: int = 7, horizon: int = 7) -> list[Forecast]:
    """Flat moving-average forecast for the `horizon` days after the last sale.

    All rows of one call share a new run_id. Re-running replaces earlier forecasts for the same store, SKU and
    dates; staffing only ever reads the latest run per SKU, so older rows for other dates are ignored.
    """
    rows = db.execute(select(Sale.d, Sale.units).where(Sale.store_id == store_id, Sale.sku_id == sku_id)).all()
    daily: dict[date, int] = {}
    for d, units in rows:
        daily[d] = daily.get(d, 0) + units
    avg = round(moving_average(daily, window))

    last = max(daily)
    days = [last + timedelta(days=i) for i in range(1, horizon + 1)]
    db.execute(delete(Forecast).where(Forecast.store_id == store_id, Forecast.sku_id == sku_id, Forecast.d.in_(days)))
    run_id = str(uuid4())
    created = [Forecast(store_id=store_id, sku_id=sku_id, d=d, units=avg, method="ma", run_id=run_id) for d in days]
    db.add_all(created)
    db.commit()
    return created
