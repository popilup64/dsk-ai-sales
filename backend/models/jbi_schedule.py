from sqlalchemy import Column, Integer, String, Date, Boolean, ForeignKey
from backend.db.session import Base
from backend.models.base import TimestampMixin


class JBISchedule(Base, TimestampMixin):
    __tablename__ = "jbi_schedules"

    id = Column(Integer, primary_key=True, index=True)
    complex_id = Column(Integer, ForeignKey("complexes.id"), nullable=False)
    section_id = Column(Integer, ForeignKey("sections.id"), nullable=True)
    material = Column(String(100), nullable=False)
    planned_date = Column(Date, nullable=False)
    actual_date = Column(Date, nullable=True)
    delay_days = Column(Integer, default=0)
    status = Column(String(20), default="не начато")  # не начато / в работе / выполнено
    critical = Column(Boolean, default=False)
