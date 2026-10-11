from pydantic import BaseModel, Field
from datetime import date

class SaleIn(BaseModel):
    store_code: str
    sku_code: str
    d: date
    units: int = Field(ge=0)

class SaleIngest(BaseModel):
    items: list[SaleIn]
