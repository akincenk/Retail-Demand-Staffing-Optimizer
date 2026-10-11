import secrets

from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader

from app.core.settings import Settings, settings

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def check_auth_config(cfg: Settings = settings) -> None:
    """Refuse to start without an API key unless ALLOW_NO_AUTH=true is set explicitly."""
    if not cfg.api_key and not cfg.allow_no_auth:
        raise RuntimeError("API_KEY is not set. Set it, or set ALLOW_NO_AUTH=true for local development only.")


def require_api_key(key: str | None = Security(_api_key_header)) -> None:
    if not settings.api_key:  # only reachable with ALLOW_NO_AUTH=true (see check_auth_config)
        return
    if key is None or not secrets.compare_digest(key.encode(), settings.api_key.encode()):
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
