def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}
    assert client.get("/api/v1/ping").json() == {"pong": True}


def test_create_and_list_stores_and_skus(client):
    r = client.post("/api/v1/stores", json={"code": "S1", "name": "Downtown"})
    assert r.status_code == 201 and r.json()["code"] == "S1"
    r = client.post("/api/v1/skus", json={"code": "K1", "name": "Coffee", "category": "beverage"})
    assert r.status_code == 201
    assert [s["code"] for s in client.get("/api/v1/stores").json()] == ["S1"]
    assert [s["category"] for s in client.get("/api/v1/skus").json()] == ["beverage"]


def test_duplicate_codes_conflict(client):
    client.post("/api/v1/stores", json={"code": "S1", "name": "A"})
    client.post("/api/v1/skus", json={"code": "K1", "name": "A"})
    assert client.post("/api/v1/stores", json={"code": "S1", "name": "B"}).status_code == 409
    assert client.post("/api/v1/skus", json={"code": "K1", "name": "B"}).status_code == 409


def test_validation_errors(client):
    assert client.post("/api/v1/stores", json={"code": "", "name": "x"}).status_code == 422
    assert client.post("/api/v1/sales/ingest", json={"items": []}).status_code == 422
    item = {"store_code": "S1", "sku_code": "K1", "d": "2025-01-01", "units": -1}
    assert client.post("/api/v1/sales/ingest", json={"items": [item]}).status_code == 422


def test_ingest_is_all_or_nothing(client, seeded):
    items = [
        {"store_code": "S1", "sku_code": "COFFEE", "d": "2025-01-15", "units": 999},
        {"store_code": "S1", "sku_code": "NOPE", "d": "2025-01-15", "units": 1},
    ]
    r = client.post("/api/v1/sales/ingest", json={"items": items})
    assert r.status_code == 400 and "items[1]" in r.json()["detail"]
    # The valid first item was not saved: forecast still starts on Jan 15 at the old average.
    f = client.post("/api/v1/forecast/run", params={"store_code": "S1", "sku_code": "COFFEE", "horizon": 1}).json()
    assert [(x["d"], x["units"], x["method"]) for x in f] == [("2025-01-15", 20, "ma")]


def test_forecast_is_flat_moving_average_after_last_sale(client, seeded):
    params = {"store_code": "S1", "sku_code": "COFFEE", "window": 14, "horizon": 3}
    r = client.post("/api/v1/forecast/run", params=params)
    assert r.status_code == 200
    assert [(f["d"], f["units"]) for f in r.json()] == [("2025-01-15", 15), ("2025-01-16", 15), ("2025-01-17", 15)]


def test_forecast_errors(client, seeded):
    run = "/api/v1/forecast/run"
    assert client.post(run, params={"store_code": "X", "sku_code": "COFFEE"}).status_code == 404
    assert client.post(run, params={"store_code": "S1", "sku_code": "X"}).status_code == 404
    client.post("/api/v1/skus", json={"code": "TEA", "name": "Tea"})
    assert client.post(run, params={"store_code": "S1", "sku_code": "TEA"}).status_code == 400  # no sales
    assert client.post(run, params={"store_code": "S1", "sku_code": "COFFEE", "window": 0}).status_code == 422


def test_staffing_plan_from_forecast(client, seeded):
    client.post("/api/v1/forecast/run", params={"store_code": "S1", "sku_code": "COFFEE", "window": 7, "horizon": 2})
    # 20 units/day x 30 min = 600 min; 4h shift = 240 min -> 3 people
    params = {"store_code": "S1", "service_minutes_per_unit": 30, "shift_hours": 4, "min_staff": 1, "max_staff": 10,
              "start": "2025-01-15", "end": "2025-01-16"}
    r = client.post("/api/v1/staffing/plan", params=params)
    assert r.status_code == 200
    assert [(p["d"], p["staff_required"]) for p in r.json()] == [("2025-01-15", 3), ("2025-01-16", 3)]


def test_reruns_replace_instead_of_double_counting(client, seeded):
    fparams = {"store_code": "S1", "sku_code": "COFFEE", "window": 7, "horizon": 1}
    client.post("/api/v1/forecast/run", params=fparams)
    client.post("/api/v1/forecast/run", params=fparams)
    params = {"store_code": "S1", "service_minutes_per_unit": 30, "shift_hours": 4, "min_staff": 0, "max_staff": 100,
              "start": "2025-01-15", "end": "2025-01-15"}
    first = client.post("/api/v1/staffing/plan", params=params).json()
    second = client.post("/api/v1/staffing/plan", params=params).json()
    assert [p["staff_required"] for p in first] == [p["staff_required"] for p in second] == [3]


RANGE = {"start": "2025-01-15", "end": "2025-01-16"}


def test_staffing_errors(client, seeded):
    plan = "/api/v1/staffing/plan"
    assert client.post(plan, params={"store_code": "X", **RANGE}).status_code == 404
    assert client.post(plan, params={"store_code": "S1", "min_staff": 5, "max_staff": 2, **RANGE}).status_code == 400
    assert client.post(plan, params={"store_code": "S1", "shift_hours": 0, **RANGE}).status_code == 422
    assert client.post(plan, params={"store_code": "S1"}).status_code == 422  # date range is required
    backwards = {"store_code": "S1", "start": "2025-01-16", "end": "2025-01-15"}
    assert client.post(plan, params=backwards).status_code == 400
    too_long = {"store_code": "S1", "start": "2025-01-01", "end": "2025-06-01"}
    assert client.post(plan, params=too_long).status_code == 400
    r = client.post(plan, params={"store_code": "S1", **RANGE})  # no forecasts yet
    assert r.status_code == 409 and r.json()["detail"]["missing_skus"] == ["COFFEE"]
    client.post("/api/v1/stores", json={"code": "EMPTY", "name": "No sales"})
    assert client.post(plan, params={"store_code": "EMPTY", **RANGE}).status_code == 400


def test_staffing_requires_every_sold_sku_to_be_forecast(client, seeded):
    client.post("/api/v1/skus", json={"code": "TEA", "name": "Tea"})
    client.post("/api/v1/sales/ingest", json={"items": [{"store_code": "S1", "sku_code": "TEA", "d": "2025-01-14", "units": 40}]})
    client.post("/api/v1/forecast/run", params={"store_code": "S1", "sku_code": "COFFEE", "window": 7, "horizon": 2})
    plan = "/api/v1/staffing/plan"
    params = {"store_code": "S1", "service_minutes_per_unit": 30, "shift_hours": 4, "min_staff": 0, "max_staff": 100, **RANGE}
    r = client.post(plan, params=params)
    assert r.status_code == 409 and r.json()["detail"]["missing_skus"] == ["TEA"]

    client.post("/api/v1/forecast/run", params={"store_code": "S1", "sku_code": "TEA", "window": 1, "horizon": 2})
    # (20 coffee + 40 tea) x 30 min = 1800 min / 240 min per shift -> 8 people
    r = client.post(plan, params=params)
    assert [(p["d"], p["staff_required"]) for p in r.json()] == [("2025-01-15", 8), ("2025-01-16", 8)]


def test_staffing_uses_only_latest_forecast_run(client, seeded):
    run = "/api/v1/forecast/run"
    client.post(run, params={"store_code": "S1", "sku_code": "COFFEE", "window": 7, "horizon": 5})  # Jan 15-19 at 20
    new_sales = [{"store_code": "S1", "sku_code": "COFFEE", "d": f"2025-01-{d}", "units": 80} for d in (15, 16)]
    client.post("/api/v1/sales/ingest", json={"items": new_sales})
    latest = client.post(run, params={"store_code": "S1", "sku_code": "COFFEE", "window": 2, "horizon": 2}).json()
    assert [(f["d"], f["units"]) for f in latest] == [("2025-01-17", 80), ("2025-01-18", 80)]

    plan = "/api/v1/staffing/plan"
    base = {"store_code": "S1", "service_minutes_per_unit": 3, "shift_hours": 4, "min_staff": 0, "max_staff": 100}
    # 80 units x 3 min = 240 min -> 1 person; the older run's 20/day for these dates is ignored.
    r = client.post(plan, params={**base, "start": "2025-01-17", "end": "2025-01-18"})
    assert [p["staff_required"] for p in r.json()] == [1, 1]
    # Jan 19 exists only in the superseded run, so it does not count as covered.
    r = client.post(plan, params={**base, "start": "2025-01-17", "end": "2025-01-19"})
    assert r.status_code == 409 and r.json()["detail"]["missing_skus"] == ["COFFEE"]


def test_ingest_is_idempotent_upsert(client, seeded):
    item = {"store_code": "S1", "sku_code": "COFFEE", "d": "2025-01-14", "units": 50}
    for _ in range(2):
        r = client.post("/api/v1/sales/ingest", json={"items": [item]})
        assert r.status_code == 201 and r.json() == {"status": "ok", "count": 1}
    # Jan 14 now holds 50 (replaced, not 20 + 50 + 50).
    f = client.post("/api/v1/forecast/run", params={"store_code": "S1", "sku_code": "COFFEE", "window": 1, "horizon": 1})
    assert f.json()[0]["units"] == 50


def test_ingest_rejects_duplicate_keys_in_one_batch(client, seeded):
    item = {"store_code": "S1", "sku_code": "COFFEE", "d": "2025-01-20", "units": 5}
    r = client.post("/api/v1/sales/ingest", json={"items": [item, {**item, "units": 7}]})
    assert r.status_code == 400 and "items[1]" in r.json()["detail"]


def test_ingest_large_batch_is_chunked(client, seeded):
    from datetime import date, timedelta

    items = [
        {"store_code": "S1", "sku_code": "COFFEE", "d": (date(2000, 1, 1) + timedelta(days=i)).isoformat(), "units": 1}
        for i in range(2500)
    ]
    assert client.post("/api/v1/sales/ingest", json={"items": items}).json()["count"] == 2500


def test_duplicate_insert_race_returns_409(client, monkeypatch):
    # Simulate a concurrent insert: the pre-check finds nothing, the unique constraint fires on commit.
    from sqlalchemy.engine import Result

    client.post("/api/v1/stores", json={"code": "S1", "name": "A"})
    client.post("/api/v1/skus", json={"code": "K1", "name": "A"})
    monkeypatch.setattr(Result, "scalar", lambda self: None)
    assert client.post("/api/v1/stores", json={"code": "S1", "name": "B"}).status_code == 409
    assert client.post("/api/v1/skus", json={"code": "K1", "name": "B"}).status_code == 409
