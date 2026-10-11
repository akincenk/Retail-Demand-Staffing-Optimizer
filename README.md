# Retail Demand & Staffing Optimizer

[![CI](https://github.com/akincenk/Retail-Demand-Staffing-Optimizer/actions/workflows/ci.yml/badge.svg)](https://github.com/akincenk/Retail-Demand-Staffing-Optimizer/actions/workflows/ci.yml)

A REST API that turns daily sales per store and SKU into a moving-average demand forecast, then into a daily
staffing plan for each store.

## What it does

1. **Ingest sales**: daily units per store and SKU, in bulk (`POST /api/v1/sales/ingest`). There is one row per
   store, SKU and day (database unique constraint); ingest is an upsert, so re-sending a batch is idempotent and a
   new value for an existing day replaces the old one. A batch is all-or-nothing: an unknown store or SKU code, or the
   same store/SKU/day twice in one batch, rejects the whole batch.
2. **Forecast** (`POST /api/v1/forecast/run`): a **simple moving average**, not a statistical or ML model. It averages
   daily units over the last `window` calendar days of history (days with no sales count as zero) and repeats that
   value for each of the next `horizon` days after the last sale. Trend, weekly seasonality, holidays and promotions
   are not modelled. Every run gets a `run_id`.
3. **Staffing plan** (`POST /api/v1/staffing/plan`): for each day in an explicit `start`..`end` range, sums the
   forecast units of every SKU the store has sold, taking each SKU's values from its **latest forecast run only**
   (older runs are ignored even if they cover other dates). If any of those SKUs has no latest-run forecast for every
   day of the range, the request fails with `409` and lists the `missing_skus`. Per day it computes

   ```
   staff = ceil(units * service_minutes_per_unit / (shift_hours * 60)), clamped to [min_staff, max_staff]
   ```

   This is a capacity rule of thumb, not a mathematical optimizer (despite the repository name): one number per day,
   no hourly split, no shift scheduling.

Re-running a forecast or a plan replaces the earlier rows for the same dates instead of duplicating them.

## Stack

FastAPI, Pydantic v2, SQLAlchemy 2.0, Alembic, PostgreSQL 16, Docker Compose, pytest, ruff, GitHub Actions.

```
app/
  main.py             FastAPI app, /health
  api/                routers: stores, skus, sales, forecast, staffing, util (/ping)
  core/               settings from environment, X-API-Key check
  services/           forecasting.py (moving average), staffing.py (latest-run selection, staff formula)
  models/, schemas/   SQLAlchemy models, Pydantic request/response models
  db/                 engine/session, Alembic migrations
  seed/seed_demo.py   2 stores, 2 SKUs, synthetic sales for 2025-01-01..2025-01-30
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
cp .env.example .env                                      # then set API_KEY (and real DB credentials)
docker compose up -d --build                              # Postgres + migrations + API on :8000
docker compose exec api python -m app.seed.seed_demo      # demo data (run once)
H="X-API-Key: $(grep ^API_KEY= .env | cut -d= -f2)"
curl -H "$H" -X POST "localhost:8000/api/v1/forecast/run?store_code=STORE-001&sku_code=SKU-COFFEE&window=7&horizon=7"
curl -H "$H" -X POST "localhost:8000/api/v1/forecast/run?store_code=STORE-001&sku_code=SKU-SAND&window=7&horizon=7"
curl -H "$H" -X POST "localhost:8000/api/v1/staffing/plan?store_code=STORE-001&start=2025-01-31&end=2025-02-06&service_minutes_per_unit=0.5&shift_hours=8&min_staff=2&max_staff=12"
open http://localhost:8000/docs
docker compose down -v
```

Database credentials default to dev-only `postgres/postgres`; override with `POSTGRES_USER`, `POSTGRES_PASSWORD`,
`POSTGRES_DB` in `.env`. Postgres is not published to the host; only the `api` container can reach it.

### Local (Python 3.11+)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
export DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/retail
export API_KEY=dev-key        # or ALLOW_NO_AUTH=true for local experiments only
alembic upgrade head
python -m app.seed.seed_demo
uvicorn app.main:app --reload
```

## Configuration

| Variable       | Default (dev only)                                             |
|----------------|----------------------------------------------------------------|
| `DATABASE_URL` | `postgresql+psycopg://postgres:postgres@localhost:5432/retail` |
| `API_KEY`      | none; required unless `ALLOW_NO_AUTH=true`                     |
| `ALLOW_NO_AUTH`| `false`; `true` disables the API-key check (local dev only)    |

The app refuses to start if `API_KEY` is empty and `ALLOW_NO_AUTH` is not `true`.

## API overview

All under `/api/v1`; full schemas at `/docs`. Every route except `/health` and `/api/v1/ping` requires the
`X-API-Key` header (`401` otherwise). A Postman collection is in `docs/` (set its `api_key` variable).

| Method | Path | Notes |
|---|---|---|
| GET | `/health`, `/api/v1/ping` | liveness |
| GET, POST | `/stores`, `/skus` | `409` on duplicate `code` (also under concurrent inserts) |
| POST | `/sales/ingest` | `{"items":[{"store_code","sku_code","d","units"}]}`, 1 to 10,000 items, upsert; `400` on unknown codes or in-batch duplicates |
| POST | `/forecast/run` | query: `store_code`, `sku_code`, `window` (1-60), `horizon` (1-30); `404` unknown code, `400` no sales |
| POST | `/staffing/plan` | query: `store_code`, `start`, `end` (at most 92 days), `service_minutes_per_unit`, `shift_hours`, `min_staff`, `max_staff`; `400` bad range / min > max / no sales, `409` with `missing_skus` |

## Tests

```bash
pytest
```

Unit tests cover the moving average (window, gaps, short history) and the staffing formula (rounding, clamping); API
tests cover auth (`401`), ingest validation, atomicity and idempotent upsert, forecast values, latest-run selection,
missing-SKU coverage, staffing output, reruns, the duplicate-insert race and error codes. Pytest treats warnings as
errors. Without `DATABASE_URL` tests use a local SQLite file. CI runs ruff, `pip-audit`, `alembic upgrade head`,
`alembic check` (models vs. migrations) and pytest against PostgreSQL 16 on Python 3.11 and 3.12, and builds the
Docker image. Dependabot proposes weekly pip and Actions updates.

## Design decisions

- **Formula over optimizer.** A daily capacity formula is transparent and easy to test; a real optimizer only pays
  off with hourly demand and shift constraints (see next steps).
- **Forecast runs are explicit.** Each run has a `run_id`; staffing reads the latest run per SKU, so a stale run can
  never be mixed into a plan, and an incomplete forecast is reported (`missing_skus`) rather than silently treated as
  zero demand.
- **Idempotent ingest.** A unique constraint on (store, SKU, day) plus `INSERT ... ON CONFLICT DO UPDATE` makes
  retries safe. Migration `0002` merges any pre-existing duplicate rows by summing them before adding the constraint.
- **Synchronous SQLAlchemy in plain `def` handlers**, which FastAPI runs in its threadpool.
- **Runtime dependencies pinned exactly** in `pyproject.toml`; test and lint tools in the `dev` extra.

## Security

- Single shared API key (`X-API-Key`), compared in constant time; the app will not start without one unless
  `ALLOW_NO_AUTH=true` is set explicitly.
- Configuration from environment variables; `.env.example` holds dev-only values, no secrets are committed.
- Docker image runs as a non-root user; Compose keeps Postgres inside its network.
- Request validation via Pydantic and query constraints (non-negative units, bounded batch size and date range).

## Limitations and next steps

- Forecasting is a flat moving average. Next: weekday seasonality, then a proper model (e.g. ETS or gradient
  boosting with calendar/promo features) evaluated against the moving average as a baseline.
- Staffing is a daily headcount formula. Next: hourly demand curves and shift scheduling (e.g. an ILP with OR-Tools).
- One shared API key, no per-user accounts or roles; no pagination or update/delete endpoints for stores and SKUs.
- No endpoint to read stored forecasts or plans other than the response of the run.

## License

MIT, see [LICENSE](LICENSE).
