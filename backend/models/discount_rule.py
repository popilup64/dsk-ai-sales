from sqlalchemy import Column, Integer, String, Float, Boolean
from backend.db.session import Base
from backend.models.base import TimestampMixin


class DiscountRule(Base, TimestampMixin):
    __tablename__ = "discount_rules"

    id = Column(Integer, primary_key=True, index=True)
    payment_type = Column(String(30), unique=True, nullable=False)
    discount_percent = Column(Float, default=0.0)
    max_discount_rub = Column(Integer, default=0)
    description = Column(String(200))
    conditions = Column(String(200))
    requires_approval = Column(Boolean, default=False)
