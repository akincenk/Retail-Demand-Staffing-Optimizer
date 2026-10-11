"""Load two stores, two SKUs and 30 days of synthetic sales (2025-01-01 to 2025-01-30). Run once on an empty database."""
from datetime import date, timedelta

from app.db.session import SessionLocal
from app.models import SKU, Sale, Store


def run():
    with SessionLocal() as db:
        store = Store(code="STORE-001", name="Downtown")
        db.add_all([store, Store(code="STORE-002", name="Airport")])
        coffee = SKU(code="SKU-COFFEE", name="Drip Coffee 12oz", category="beverage")
        sandwich = SKU(code="SKU-SAND", name="Turkey Sandwich", category="deli")
        db.add_all([coffee, sandwich])
        db.flush()

        start = date(2025, 1, 1)  # fixed dates keep the README examples reproducible
        for i in range(30):
            d = start + timedelta(days=i)
            db.add(Sale(store_id=store.id, sku_id=coffee.id, d=d, units=80 + (i % 7) * 5))
            db.add(Sale(store_id=store.id, sku_id=sandwich.id, d=d, units=40 + ((i + 3) % 7) * 3))
        db.commit()
        print("Seed completed.")


if __name__ == "__main__":
    run()
