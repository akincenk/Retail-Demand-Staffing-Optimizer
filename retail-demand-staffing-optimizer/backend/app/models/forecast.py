from sqlalchemy import Integer, ForeignKey, String, Date, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from app.db.session import Base

class Forecast(Base):
    __tablename__ = "forecasts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    store_id: Mapped[int] = mapped_column(ForeignKey("stores.id", ondelete="CASCADE"), index=True, nullable=False)
    sku_id: Mapped[int] = mapped_column(ForeignKey("skus.id", ondelete="CASCADE"), index=True, nullable=False)
    d: Mapped = mapped_column(Date, nullable=False)
    units: Mapped[int] = mapped_column(Integer, nullable=False)
    method: Mapped[str] = mapped_column(String(32), default="ma")
    created_at: Mapped = mapped_column(DateTime(timezone=True), server_default=func.now())
