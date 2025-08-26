from pydantic import BaseModel
from datetime import date

class ForecastOut(BaseModel):
    store_id: int
    sku_id: int
    d: date
    units: int
    method: str

    class Config:
        from_attributes = True
