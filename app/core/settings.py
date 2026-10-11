import os

from pydantic import BaseModel


class Settings(BaseModel):
    # Default is a local dev database; set DATABASE_URL in any real environment.
    database_url: str = os.getenv("DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/retail")
    # Clients send this in the X-API-Key header. Empty means "not configured".
    api_key: str = os.getenv("API_KEY", "")
    # Local development escape hatch: run without an API key.
    allow_no_auth: bool = os.getenv("ALLOW_NO_AUTH", "").lower() == "true"

settings = Settings()
