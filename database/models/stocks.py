from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, DateTime, Integer, DECIMAL, Date
from .base import Base
from datetime import datetime, date
from decimal import Decimal
from typing import Optional

class Stocks(Base):
    __tablename__ = 'stocks'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    report_date: Mapped[date] = mapped_column(Date, nullable=False)
    shop_sku: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    article: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    market_sku: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    product_name: Mapped[Optional[str]] = mapped_column(String(250), nullable=True)
    valid: Mapped[int] = mapped_column(Integer, default=0)
    reserved: Mapped[int] = mapped_column(Integer, default=0)
    available_for_order: Mapped[int] = mapped_column(Integer, default=0)
    quarantine: Mapped[int] = mapped_column(Integer, default=0)
    utilization: Mapped[int] = mapped_column(Integer, default=0)
    defect: Mapped[int] = mapped_column(Integer, default=0)
    expired: Mapped[int] = mapped_column(Integer, default=0)
    length: Mapped[Optional[int]] = mapped_column(Integer,nullable=True)
    width: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    height: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    weight: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(10, 3), nullable=True)
    warehouse: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    selling_status: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    recommendations: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    turnover: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"sku: {self.shop_sku} | Годный: {self.valid} | Доступно для заказа: {self.available_for_order}"













