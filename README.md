# Retail Demand & Staffing Optimizer

[![CI](https://github.com/akincenk/Retail-Demand-Staffing-Optimizer/actions/workflows/ci.yml/badge.svg)](https://github.com/akincenk/Retail-Demand-Staffing-Optimizer/actions/workflows/ci.yml)

A REST API that turns daily sales per store and SKU into a moving-average demand forecast, then into a daily
staffing plan for each store.

## What it does

1. **Ingest sales**: daily units per store and SKU, in bulk (`POST /api/v1/sales/ingest`). A batch is
   all-or-nothing: one unknown store or SKU code rejects the whole batch.
2. **Forecast** (`POST /api/v1/forecast/run`): a **simple moving average**, not a statistical or ML model. It averages
   daily units over the last `window` calendar days of history (days with no sales count as zero) and repeats that
   value for each of the next `horizon` days after the last sale. Trend, weekly seasonality, holidays and promotions
   are not modelled.
3. **Staffing plan** (`POST /api/v1/staffing/plan`): for each forecast day, sums forecast units across all SKUs in the
   store and computes

   ```
   staff = ceil(units * service_minutes_per_unit / (shift_hours * 60)), clamped to [min_staff, max_staff]
   ```

   This is a capacity rule of thumb, not an optimizer: one number per day, no hourly split, no shift scheduling.

Re-running a forecast or a plan replaces the earlier rows for the same dates instead of duplicating them.

## Stack

FastAPI, Pydantic v2, SQLAlchemy 2.0, Alembic, PostgreSQL 16, Docker Compose, pytest, ruff, GitHub Actions.

```
app/
  main.py             FastAPI app, /health
  api/                routers: stores, skus, sales, forecast, staffing, util (/ping)
  services/           forecasting.py (moving average), staffing.py (staff formula)
  models/, schemas/   SQLAlchemy models, Pydantic request/response models
  db/                 engine/session, Alembic migrations
  seed/seed_demo.py   2 stores, 2 SKUs, 30 days of synthetic sales
tests/                unit tests for the math, API tests via TestClient
docs/postman_collection.json
```

```mermaid
flowchart LR
  Sales[POST /sales/ingest] --> DB[(PostgreSQL)]
  DB --> F[moving-average forecast] --> DB
  DB --> S[staffing formula] --> DB
```

## Quickstart

### Docker Compose

```bash
docker compose up -d --build                              # Postgres + migrations + API on :8000
docker compose exec api python -m app.seed.seed_demo      # demo data (run once)
curl -X POST "localhost:8000/api/v1/forecast/run?store_code=STORE-001&sku_code=SKU-COFFEE&window=7&horizon=7"
curl -X POST "localhost:8000/api/v1/forecast/run?store_code=STORE-001&sku_code=SKU-SAND&window=7&horizon=7"
curl -X POST "localhost:8000/api/v1/staffing/plan?store_code=STORE-001&service_minutes_per_unit=0.5&shift_hours=8&min_staff=2&max_staff=12"
open http://localhost:8000/docs
docker compose down -v
```

Database credentials default to dev-only `postgres/postgres`; override with `POSTGRES_USER`, `POSTGRES_PASSWORD`,
`POSTGRES_DB` in a `.env` file (see `.env.example`).

### Local (Python 3.11+)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
export DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/retail
alembic upgrade head
python -m app.seed.seed_demo
uvicorn app.main:app --reload
```

## Configuration

| Variable       | Default (dev only)                                             |
|----------------|----------------------------------------------------------------|
| `DATABASE_URL` | `postgresql+psycopg://postgres:postgres@localhost:5432/retail` |

## API overview

All under `/api/v1`; full schemas at `/docs`. A Postman collection is in `docs/`.

| Method | Path | Notes |
|---|---|---|
| GET | `/health`, `/api/v1/ping` | liveness |
| GET, POST | `/stores`, `/skus` | `409` on duplicate `code` |
| POST | `/sales/ingest` | `{"items":[{"store_code","sku_code","d","units"}]}`, 1 to 10,000 items; `400` on unknown codes |
| POST | `/forecast/run` | query: `store_code`, `sku_code`, `window` (1-60), `horizon` (1-30); `404` unknown code, `400` no sales |
| POST | `/staffing/plan` | query: `store_code`, `service_minutes_per_unit`, `shift_hours`, `min_staff`, `max_staff`; `400` if min > max |

## Tests

```bash
pytest
```

Unit tests cover the moving average (window, gaps, short history) and the staffing formula (rounding, clamping); API
tests cover ingest validation and atomicity, forecast values, staffing output, reruns and error codes. Without
`DATABASE_URL` tests use a local SQLite file. CI runs ruff, `alembic upgrade head`, `alembic check` (models vs.
migrations) and pytest against PostgreSQL 16 on Python 3.11 and 3.12, and builds the Docker image.

## Limitations and next steps

- Forecasting is a flat moving average. Next: weekday seasonality, then a proper model (e.g. ETS or gradient
  boosting with calendar/promo features) evaluated against the moving average as a baseline.
- Staffing is a daily headcount formula. Next: hourly demand curves and shift scheduling (e.g. an ILP with OR-Tools).
- No authentication, pagination, or update/delete endpoints for stores and SKUs.
- No endpoint to read stored forecasts or plans other than the response of the run.

## License

MIT, see [LICENSE](LICENSE).
