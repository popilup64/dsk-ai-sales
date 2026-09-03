from sqlalchemy import Column, Integer, String, Float, Boolean
from backend.db.session import Base
from backend.models.base import TimestampMixin


class Service(Base, TimestampMixin):
    __tablename__ = "services"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    price = Column(Integer, nullable=True)  # фиксированная цена
    price_per_m2 = Column(Integer, nullable=True)  # цена за м²
    unit = Column(String(20), nullable=False)
    category = Column(String(30), nullable=False)
    applicable_to = Column(String(50), default="all")
    description = Column(String(300))
    available = Column(Boolean, default=True)
