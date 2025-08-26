from pydantic import BaseModel, Field

class StoreBase(BaseModel):
    code: str = Field(..., max_length=64)
    name: str = Field(..., max_length=255)

class StoreCreate(StoreBase):
    pass

class StoreOut(StoreBase):
    id: int
    class Config:
        from_attributes = True
