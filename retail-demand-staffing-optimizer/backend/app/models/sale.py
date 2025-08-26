from sqlalchemy import Integer, ForeignKey, Date, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from app.db.session import Base

class Sale(Base):
    __tablename__ = "sales"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    store_id: Mapped[int] = mapped_column(ForeignKey("stores.id", ondelete="CASCADE"), index=True, nullable=False)
    sku_id: Mapped[int] = mapped_column(ForeignKey("skus.id", ondelete="CASCADE"), index=True, nullable=False)
    d: Mapped = mapped_column(Date, nullable=False)
    units: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped = mapped_column(DateTime(timezone=True), server_default=func.now())
