from sqlalchemy import Column, Integer, String, Float, Date, Enum
from backend.db.session import Base
from backend.models.base import TimestampMixin
import enum


class ComplexStatus(str, enum.Enum):
    строится = "строится"
    скоро_сдача = "скоро сдача"
    сдан = "сдан"
    заморожен = "заморожен"


class ComplexClass(str, enum.Enum):
    комфорт = "комфорт"
    бизнес = "бизнес"


class Complex(Base, TimestampMixin):
    __tablename__ = "complexes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    address = Column(String(255), nullable=False)
    district = Column(String(100))
    completion_date = Column(Date, nullable=False)
    status = Column(Enum(ComplexStatus), default=ComplexStatus.строится)
    class_ = Column("class", Enum(ComplexClass), default=ComplexClass.комфорт)
    price_per_m2_base = Column(Integer, default=220000)
    description = Column(String(500))
