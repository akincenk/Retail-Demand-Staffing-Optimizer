#!/usr/bin/env bash
set -euo pipefail

echo "[1/5] Launching stack..."
docker compose -f infra/docker-compose.yml up -d --build

echo "[2/5] Running migrations..."
docker compose -f infra/docker-compose.yml exec api alembic upgrade head

echo "[3/5] Seeding demo data..."
docker compose -f infra/docker-compose.yml exec api python -m app.seed.seed_demo

echo "[4/5] Forecast (STORE-001 / SKU-COFFEE)"
curl -s "http://localhost:8000/api/v1/forecast/run?store_code=STORE-001&sku_code=SKU-COFFEE&window=7&horizon=7" | jq . || true

echo "[5/5] Staffing plan (STORE-001)"
curl -s "http://localhost:8000/api/v1/staffing/plan?store_code=STORE-001&service_minutes_per_unit=0.5&shift_hours=8&min_staff=2&max_staff=12" | jq . || true

echo "Open API docs: http://localhost:8000/docs"
