from pydantic import BaseModel, ConfigDict, Field


class SKUBase(BaseModel):
    code: str = Field(..., min_length=1, max_length=64)
    name: str = Field(..., min_length=1, max_length=255)
    category: str | None = Field(None, max_length=64)


class SKUCreate(SKUBase):
    pass


class SKUOut(SKUBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
