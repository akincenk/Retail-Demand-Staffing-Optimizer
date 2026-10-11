from datetime import date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import select, func, and_
from app.models import Sale, Store, SKU, Forecast

def moving_average_forecast(db: Session, store_code: str, sku_code: str, window: int = 7, horizon: int = 7) -> list[Forecast]:
    store = db.execute(select(Store).where(Store.code == store_code)).scalar_one()
    sku = db.execute(select(SKU).where(SKU.code == sku_code)).scalar_one()

    max_date = db.execute(select(func.max(Sale.d)).where(and_(Sale.store_id==store.id, Sale.sku_id==sku.id))).scalar()
    if max_date is None:
        raise ValueError("No sales for given store/sku")

    created = []
    for i in range(1, horizon+1):
        target_day = max_date + timedelta(days=i)
        start_day = target_day - timedelta(days=window)
        avg_units = db.execute(
            select(func.coalesce(func.round(func.avg(Sale.units)), 0))
            .where(and_(Sale.store_id==store.id, Sale.sku_id==sku.id, Sale.d > start_day, Sale.d <= max_date))
        ).scalar() or 0
        f = Forecast(store_id=store.id, sku_id=sku.id, d=target_day, units=int(avg_units), method="ma")
        db.add(f); created.append(f)
    db.commit()
    return created
