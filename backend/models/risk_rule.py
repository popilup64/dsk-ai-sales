from sqlalchemy import Column, Integer, String, Float, Boolean
from backend.db.session import Base
from backend.models.base import TimestampMixin


class RiskRule(Base, TimestampMixin):
    __tablename__ = "risk_rules"

    id = Column(Integer, primary_key=True, index=True)
    rule_name = Column(String(100), nullable=False)
    condition_type = Column(String(50), nullable=False)
    threshold = Column(Integer, default=0)
    severity = Column(String(20), default="warning")  # warning / critical
    message_template = Column(String(500), nullable=False)
    affects_completion = Column(Boolean, default=True)
    estimated_delay_months = Column(Integer, default=0)
