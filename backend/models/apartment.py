from sqlalchemy import Column, Integer, String, Float, ForeignKey, Enum
from sqlalchemy.orm import relationship
from backend.db.session import Base
from backend.models.base import TimestampMixin
import enum


class ApartmentStatus(str, enum.Enum):
    свободна = "свободна"
    бронь = "бронь"
    продана = "продана"


class FinishingType(str, enum.Enum):
    без_отделки = "без отделки"
    предчистовая = "предчистовая"
    чистовая = "чистовая"


class Apartment(Base, TimestampMixin):
    __tablename__ = "apartments"

    id = Column(Integer, primary_key=True, index=True)
    section_id = Column(Integer, ForeignKey("sections.id"), nullable=False)
    floor = Column(Integer, nullable=False)
    floor_total = Column(Integer, nullable=False)
    rooms = Column(Integer, nullable=False)
    room_type = Column(String(10), nullable=False)  # "1", "2", "3+"
    area = Column(Float, nullable=False)
    price_per_m2 = Column(Integer, nullable=False)
    status = Column(Enum(ApartmentStatus), default=ApartmentStatus.свободна)
    finishing = Column(Enum(FinishingType), default=FinishingType.без_отделки)
    floor_plan = Column(String(500), default="Гостиная 32 м², Спальня 18 м², Кухня 9 м² — ИТОГО: ~58 м²")  # SQLite not migrated

    section = relationship("Section", back_populates="apartments")
