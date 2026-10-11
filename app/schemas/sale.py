from datetime import date

from pydantic import BaseModel, Field


class SaleIn(BaseModel):
    store_code: str
    sku_code: str
    d: date
    units: int = Field(ge=0)


class SaleIngest(BaseModel):
    items: list[SaleIn] = Field(min_length=1, max_length=10_000)
