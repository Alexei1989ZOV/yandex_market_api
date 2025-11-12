from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer, Date, DateTime
from typing import Optional
from datetime import datetime

class GoodsMovement(Base):
    __tablename__ = 'goods_movement'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    report_date: Mapped[datetime] = mapped_column(Date, nullable=False) # Дата отчета
    shop_sku: Mapped[str] = mapped_column(String(10), nullable=False) # SKU
    shipments_income: Mapped[int] = mapped_column(Integer, default=0) # Поставки
    returns_income: Mapped[int] = mapped_column(Integer, default=0) # Возвраты
    inventory_surplus: Mapped[int] = mapped_column(Integer, default=0) # Излишки при инвентаризации
    orders_outcome: Mapped[int] = mapped_column(Integer, default=0) # Заказы
    warehouse_withdrawal: Mapped[int] = mapped_column(Integer, default=0) # Вывоз со склада
    recycling: Mapped[int] = mapped_column(Integer, default=0) # Утилизация
    inventory_shortage: Mapped[int] = mapped_column(Integer, default=0) #
    warehouse: Mapped[Optional[str]] = mapped_column(String(255), nullable=True) # Недостача при инвентаризации
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


    def __repr__(self):
        return f"SKU: {self.shop_sku} | Дата: {self.report_date} | Заказы: {self.orders_outcome} шт"






