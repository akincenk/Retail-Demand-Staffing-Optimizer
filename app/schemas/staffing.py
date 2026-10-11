from datetime import date

from pydantic import BaseModel, ConfigDict


class StaffingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    store_id: int
    d: date
    staff_required: int
    min_staff: int
    max_staff: int
