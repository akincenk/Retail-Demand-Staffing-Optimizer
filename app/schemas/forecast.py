from datetime import date

from pydantic import BaseModel, ConfigDict


class ForecastOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    store_id: int
    sku_id: int
    d: date
    units: int
    method: str
