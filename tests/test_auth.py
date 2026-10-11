import pytest

from app.core.auth import check_auth_config
from app.core.settings import Settings


def test_missing_or_wrong_key_is_rejected(client):
    for headers in ({"X-API-Key": ""}, {"X-API-Key": "wrong"}):
        assert client.get("/api/v1/skus", headers=headers).status_code == 401
        assert client.post("/api/v1/sales/ingest", json={"items": []}, headers=headers).status_code == 401
    del client.headers["X-API-Key"]
    assert client.post("/api/v1/staffing/plan").status_code == 401
    assert client.get("/api/v1/skus").json() == {"detail": "Invalid or missing API key"}


def test_health_and_ping_stay_public(client):
    del client.headers["X-API-Key"]
    assert client.get("/health").status_code == 200
    assert client.get("/api/v1/ping").status_code == 200


def test_app_refuses_to_start_without_key():
    with pytest.raises(RuntimeError, match="API_KEY"):
        check_auth_config(Settings(api_key="", allow_no_auth=False))
    check_auth_config(Settings(api_key="", allow_no_auth=True))
    check_auth_config(Settings(api_key="k", allow_no_auth=False))


def test_no_auth_mode_lets_requests_through(client, monkeypatch):
    from app.core import auth

    monkeypatch.setattr(auth.settings, "api_key", "")
    del client.headers["X-API-Key"]
    assert client.get("/api/v1/skus").status_code == 200
