from backend.models.base import TimestampMixin
from backend.models.complex import Complex, ComplexStatus, ComplexClass
from backend.models.section import Section, SectionStatus
from backend.models.apartment import Apartment, ApartmentStatus, FinishingType
from backend.models.jbi_schedule import JBISchedule
from backend.models.material import Material
from backend.models.service import Service
from backend.models.discount_rule import DiscountRule
from backend.models.risk_rule import RiskRule

# Добавляем relationship в Complex после определения всех моделей
from sqlalchemy.orm import relationship
Complex.sections = relationship("Section", back_populates="complex")
