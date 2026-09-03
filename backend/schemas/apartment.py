from pydantic import BaseModel
from typing import Optional


class ApartmentBase(BaseModel):
    floor: int
    floor_total: int
    rooms: int
    room_type: str
    area: float
    price_per_m2: int
    status: str
    finishing: str


class ApartmentResponse(ApartmentBase):
    id: int
    section_id: int
    complex_name: Optional[str] = None
    complex_class: Optional[str] = None

    class Config:
        from_attributes = True


class ApartmentFilter(BaseModel):
    complex_id: Optional[int] = None
    rooms: Optional[str] = None
    status: Optional[str] = "свободна"
    min_price: Optional[int] = None
    max_price: Optional[int] = None
