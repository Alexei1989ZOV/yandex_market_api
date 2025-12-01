from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer, DECIMAL, Date, DateTime
from .base import Base
from datetime import date, datetime
from decimal import Decimal


class Sales(Base):
    __tablename__ = 'sales'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    report_date: Mapped[date] = mapped_column(Date, nullable=False)
    shop_sku: Mapped[str] = mapped_column(String(20), nullable=False)
    shows: Mapped[int] = mapped_column(Integer, default=0)
    to_cart: Mapped[int] = mapped_column(Integer, default=0)
    order_items: Mapped[int] = mapped_column(Integer, default=0)
    order_items_total_amount: Mapped[int] = mapped_column(Integer, default=0)
    order_items_share: Mapped[Decimal] = mapped_column(DECIMAL(10,3), default=0)
    order_items_delivered_count: Mapped[int] = mapped_column(Integer, default=0)
    order_items_delivered_total_amount: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now())

    def __repr__(self):
        return f"SKU: {self.shop_sku}| Date: {self.report_date}| Заказано: {self.order_items} шт на сумму: {self.order_items_total_amount} руб"


