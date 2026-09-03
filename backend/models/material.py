from sqlalchemy import Column, Integer, String, Float, ForeignKey, Date
from backend.db.session import Base
from backend.models.base import TimestampMixin


class Material(Base, TimestampMixin):
    __tablename__ = "materials"

    id = Column(Integer, primary_key=True, index=True)
    complex_id = Column(Integer, ForeignKey("complexes.id"), nullable=False)
    material_name = Column(String(100), nullable=False)
    quantity = Column(Float, nullable=False)
    unit = Column(String(20), nullable=False)
    min_required = Column(Float, nullable=False)
    critical_threshold = Column(Float, nullable=False)
    expected_delivery = Column(Date, nullable=True)
    status = Column(String(30), default="достаточно")  # достаточно / дефицит / критический дефицит
