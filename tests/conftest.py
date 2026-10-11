import os

# Tests run against DATABASE_URL (PostgreSQL in CI). Without it, fall back to a local SQLite file.
os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import event  # noqa: E402

import app.models  # noqa: E402, F401
from app.db.session import Base, engine  # noqa: E402
from app.main import app  # noqa: E402

if engine.dialect.name == "sqlite":
    @event.listens_for(engine, "connect")
    def _enable_sqlite_fks(dbapi_conn, _):
        dbapi_conn.execute("PRAGMA foreign_keys=ON")

# No-op when Alembic has already created the schema (CI); creates it for SQLite runs.
Base.metadata.create_all(engine)


@pytest.fixture(autouse=True)
def _clean_tables():
    yield
    with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def seeded(client):
    """One store, one SKU and 14 days of sales: 10 units/day for week 1, 20 units/day for week 2."""
    client.post("/api/v1/stores", json={"code": "S1", "name": "Downtown"})
    client.post("/api/v1/skus", json={"code": "COFFEE", "name": "Coffee"})
    items = [
        {"store_code": "S1", "sku_code": "COFFEE", "d": f"2025-01-{day:02d}", "units": 10 if day <= 7 else 20}
        for day in range(1, 15)
    ]
    assert client.post("/api/v1/sales/ingest", json={"items": items}).status_code == 201
