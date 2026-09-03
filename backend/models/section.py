from sqlalchemy import Column, Integer, String, Float, ForeignKey, Enum
from sqlalchemy.orm import relationship
from backend.db.session import Base
from backend.models.base import TimestampMixin
import enum


class SectionStatus(str, enum.Enum):
    строится = "строится"
    скоро_сдача = "скоро сдача"
    сдан = "сдан"
    заморожен = "заморожен"


class Section(Base, TimestampMixin):
    __tablename__ = "sections"

    id = Column(Integer, primary_key=True, index=True)
    complex_id = Column(Integer, ForeignKey("complexes.id"), nullable=False)
    section_number = Column(Integer, nullable=False)
    floors = Column(Integer, nullable=False)
    progress = Column(Float, default=0.0)  # 0-100
    status = Column(Enum(SectionStatus), default=SectionStatus.строится)

    complex = relationship("Complex", back_populates="sections")
    apartments = relationship("Apartment", back_populates="section")
