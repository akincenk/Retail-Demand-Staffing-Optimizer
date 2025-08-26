from pydantic import BaseModel
from datetime import date

class StaffingOut(BaseModel):
    store_id: int
    d: date
    staff_required: int
    min_staff: int
    max_staff: int

    class Config:
        from_attributes = True
