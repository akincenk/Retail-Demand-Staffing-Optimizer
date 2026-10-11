from sqlalchemy import Integer, ForeignKey, Date, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from app.db.session import Base

class StaffingPlan(Base):
    __tablename__ = "staffing_plans"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    store_id: Mapped[int] = mapped_column(ForeignKey("stores.id", ondelete="CASCADE"), index=True, nullable=False)
    d: Mapped = mapped_column(Date, nullable=False)
    staff_required: Mapped[int] = mapped_column(Integer, nullable=False)
    min_staff: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    max_staff: Mapped[int] = mapped_column(Integer, nullable=False, default=20)
    created_at: Mapped = mapped_column(DateTime(timezone=True), server_default=func.now())
