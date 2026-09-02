from sqlalchemy import Column, Integer, DateTime, func
from backend.db.session import Base


class TimestampMixin:
    """Миксин для created_at / updated_at"""
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
