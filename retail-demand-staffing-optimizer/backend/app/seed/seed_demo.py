from datetime import date, timedelta
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models import Store, SKU, Sale

def run():
    db: Session = SessionLocal()
    try:
        s1 = Store(code="STORE-001", name="Downtown")
        s2 = Store(code="STORE-002", name="Airport")
        db.add_all([s1, s2])

        k1 = SKU(code="SKU-COFFEE", name="Drip Coffee 12oz", category="beverage")
        k2 = SKU(code="SKU-SAND", name="Turkey Sandwich", category="deli")
        db.add_all([k1, k2])
        db.commit()

        start = date.today() - timedelta(days=30)
        for i in range(30):
            d = start + timedelta(days=i)
            coffee = 80 + (i % 7) * 5
            sand = 40 + ((i+3) % 7) * 3
            db.add(Sale(store_id=1, sku_id=1, d=d, units=coffee))
            db.add(Sale(store_id=1, sku_id=2, d=d, units=sand))
        db.commit()
        print("Seed completed.")
    finally:
        db.close()

if __name__ == "__main__":
    run()
