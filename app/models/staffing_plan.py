from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class StaffingPlan(Base):
    __tablename__ = "staffing_plans"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    store_id: Mapped[int] = mapped_column(ForeignKey("stores.id", ondelete="CASCADE"), index=True, nullable=False)
    d: Mapped[date] = mapped_column(Date, nullable=False)
    staff_required: Mapped[int] = mapped_column(Integer, nullable=False)
    min_staff: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    max_staff: Mapped[int] = mapped_column(Integer, nullable=False, default=20, server_default="20")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
