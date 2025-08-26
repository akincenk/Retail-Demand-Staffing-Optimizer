from pydantic import BaseModel, Field

class SKUBase(BaseModel):
    code: str = Field(..., max_length=64)
    name: str = Field(..., max_length=255)
    category: str | None = None

class SKUCreate(SKUBase):
    pass

class SKUOut(SKUBase):
    id: int
    class Config:
        from_attributes = True
