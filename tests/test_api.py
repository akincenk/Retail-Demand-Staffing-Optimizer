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
    assert f == [{"store_id": f[0]["store_id"], "sku_id": f[0]["sku_id"], "d": "2025-01-15", "units": 20, "method": "ma"}]


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
    params = {"store_code": "S1", "service_minutes_per_unit": 30, "shift_hours": 4, "min_staff": 1, "max_staff": 10}
    r = client.post("/api/v1/staffing/plan", params=params)
    assert r.status_code == 200
    assert [(p["d"], p["staff_required"]) for p in r.json()] == [("2025-01-15", 3), ("2025-01-16", 3)]


def test_reruns_replace_instead_of_double_counting(client, seeded):
    fparams = {"store_code": "S1", "sku_code": "COFFEE", "window": 7, "horizon": 1}
    client.post("/api/v1/forecast/run", params=fparams)
    client.post("/api/v1/forecast/run", params=fparams)
    params = {"store_code": "S1", "service_minutes_per_unit": 30, "shift_hours": 4, "min_staff": 0, "max_staff": 100}
    first = client.post("/api/v1/staffing/plan", params=params).json()
    second = client.post("/api/v1/staffing/plan", params=params).json()
    assert [p["staff_required"] for p in first] == [p["staff_required"] for p in second] == [3]


def test_staffing_errors(client, seeded):
    plan = "/api/v1/staffing/plan"
    assert client.post(plan, params={"store_code": "X"}).status_code == 404
    assert client.post(plan, params={"store_code": "S1", "min_staff": 5, "max_staff": 2}).status_code == 400
    assert client.post(plan, params={"store_code": "S1", "shift_hours": 0}).status_code == 422
    assert client.post(plan, params={"store_code": "S1"}).json() == []  # no forecasts yet
