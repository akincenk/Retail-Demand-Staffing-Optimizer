import os

from pydantic import BaseModel


class Settings(BaseModel):
    # Default is a local dev database; set DATABASE_URL in any real environment.
    database_url: str = os.getenv("DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/retail")

settings = Settings()
