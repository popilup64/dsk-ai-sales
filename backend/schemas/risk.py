from pydantic import BaseModel
from typing import List


class RiskResponse(BaseModel):
    apartment_id: int
    risks: List[dict]
    overall_level: str
    total_critical: int
    total_warning: int
