from pydantic import BaseModel
from typing import Optional


class ServiceResponse(BaseModel):
    id: int
    name: str
    price: Optional[int] = None
    price_per_m2: Optional[int] = None
    unit: str
    category: str
    description: Optional[str] = None

    class Config:
        from_attributes = True
