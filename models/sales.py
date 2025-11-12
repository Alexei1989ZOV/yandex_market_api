from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer, DECIMAL, Date
from .base import Base
from datetime import datetime


class Sales(Base):
    __tablename__ = 'sales'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    date: Mapped[datetime] = mapped_column(Date, nullable=False)
    offer_id: Mapped[str] = mapped_column(String(10), nullable=False)
    by_msku_shows: Mapped[int] = mapped_column(Integer, default=0)
    shows: Mapped[int] = mapped_column(Integer, default=0)
    to_cart: Mapped[int] = mapped_column(Integer, default=0)
    order_items: Mapped[int] = mapped_column(Integer, default=0)
    order_items_total_amount: Mapped[int] = mapped_column(Integer, default=0)
    order_items_share: Mapped[float] = mapped_column(DECIMAL(5,3), default=0)
    order_items_delivered_count: Mapped[int] = mapped_column(Integer, default=0)
    order_items_delivered_total_amount: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"SKU: {self.offer_id}| Date: {self.date}| Заказано: {self.order_items} шт на сумму: {self.order_items_total_amount} руб"


