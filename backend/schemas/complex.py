from pydantic import BaseModel
from datetime import date
from typing import Optional


class ComplexBase(BaseModel):
    name: str
    address: str
    district: Optional[str] = None
    completion_date: date
    status: str
    class_: str
    price_per_m2_base: int
    description: Optional[str] = None


class ComplexResponse(ComplexBase):
    id: int
    progress: Optional[float] = None  # вычисляемое поле

    class Config:
        from_attributes = True
