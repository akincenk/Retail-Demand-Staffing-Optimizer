from pydantic import BaseModel, ConfigDict, Field


class StoreBase(BaseModel):
    code: str = Field(..., min_length=1, max_length=64)
    name: str = Field(..., min_length=1, max_length=255)


class StoreCreate(StoreBase):
    pass


class StoreOut(StoreBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
