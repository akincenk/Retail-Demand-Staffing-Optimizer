from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class Forecast(Base):
    __tablename__ = "forecasts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    store_id: Mapped[int] = mapped_column(ForeignKey("stores.id", ondelete="CASCADE"), index=True, nullable=False)
    sku_id: Mapped[int] = mapped_column(ForeignKey("skus.id", ondelete="CASCADE"), index=True, nullable=False)
    d: Mapped[date] = mapped_column(Date, nullable=False)
    units: Mapped[int] = mapped_column(Integer, nullable=False)
    # Every row written by one POST /forecast/run shares a run_id; staffing reads only the latest run per SKU.
    run_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    method: Mapped[str] = mapped_column(String(32), nullable=False, default="ma", server_default="ma")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
