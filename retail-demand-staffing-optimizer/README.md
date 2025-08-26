# Retail Demand & Staffing Optimizer (v1)
[![CI](https://img.shields.io/badge/CI-passing-brightgreen)](#)
[![Stack](https://img.shields.io/badge/Stack-FastAPI%20%7C%20Postgres%20%7C%20SQLAlchemy-blue)](#)
[![License](https://img.shields.io/badge/License-MIT-lightgrey)](#)

Production-grade API that forecasts daily demand per store x SKU and produces staffing plans to hit service-level targets.

- Stack: FastAPI + SQLAlchemy 2.0 + Alembic + PostgreSQL + Docker Compose
- Features: CRUD for Stores/SKUs, ingest Sales, Moving-Average forecasting baseline, Staffing plan generator with constraints
- Quality: CI (pytest), Makefile, Postman collection, ASCII-safe docs
- Live Docs: `http://localhost:8000/docs` (after launch)

---

## Architecture (Mermaid)
```mermaid
flowchart LR
  Client[CLI / Postman / Frontend] --> API[FastAPI]
  API --> DB[(PostgreSQL)]
  API --> SvcForecast[Forecast Service]
  API --> SvcStaff[Staffing Service]
  subgraph Infra
    API --- DB
  end
```

---

## Domain Model
```mermaid
erDiagram
  Store ||--o{ Sale : has
  SKU ||--o{ Sale : sold_as
  Store ||--o{ Forecast : has
  SKU ||--o{ Forecast : forecasted_as
  Store ||--o{ StaffingPlan : planned_for

  Store {
    int id PK
    string code
    string name
  }
  SKU {
    int id PK
    string code
    string name
    string category
  }
  Sale {
    int id PK
    int store_id FK
    int sku_id FK
    date d
    int units
  }
  Forecast {
    int id PK
    int store_id FK
    int sku_id FK
    date d
    int units
    string method
  }
  StaffingPlan {
    int id PK
    int store_id FK
    date d
    int staff_required
    int min_staff
    int max_staff
  }
```

---

## Quickstart
```bash
# 0) Prepare env
cp backend/.env.example backend/.env

# 1) Run stack
docker compose -f infra/docker-compose.yml up -d --build

# 2) Init DB
docker compose -f infra/docker-compose.yml exec api alembic upgrade head

# 3) Seed demo data
docker compose -f infra/docker-compose.yml exec api python -m app.seed.seed_demo

# 4) Verify
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/stores
curl "http://localhost:8000/api/v1/forecast/run?store_code=STORE-001&sku_code=SKU-COFFEE&window=7&horizon=7"
curl "http://localhost:8000/api/v1/staffing/plan?store_code=STORE-001&service_minutes_per_unit=0.5&shift_hours=8&min_staff=2&max_staff=12"
```

OpenAPI: `http://localhost:8000/docs`

---

## API Overview
- Data
  - `GET /api/v1/stores`, `POST /api/v1/stores`
  - `GET /api/v1/skus`, `POST /api/v1/skus`
  - `POST /api/v1/sales/ingest` (bulk JSON array of sales)
- Forecasting
  - `POST /api/v1/forecast/run?store_code=...&sku_code=...&window=7`
- Staffing
  - `GET /api/v1/staffing/plan?store_code=...&service_minutes_per_unit=0.5&shift_hours=8&min_staff=2&max_staff=12`

See `docs/postman_collection.json` for ready-to-run requests.

---

## Demo Preview
> Add these files into `docs/screenshots/` and they will appear here on GitHub.

![Docs](docs/screenshots/fastapi_docs.png)
![Forecast](docs/screenshots/forecast_sample.png)
![Staffing](docs/screenshots/staffing_sample.png)
![Postman](docs/screenshots/postman_requests.png)

---

## Roadmap
- v1 (this): moving-average baseline + staffing heuristic
- v2: exogenous features (promo/holiday), store hours by weekday, hourly staffing split
- v3: ILP optimizer (OR-Tools) and ML forecasting baselines

---

## License
MIT
