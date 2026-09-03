from pydantic import BaseModel
from typing import List, Optional


class ServiceItem(BaseModel):
    service_id: int
    name: str
    category: str
    cost: float
    unit: str
    description: Optional[str] = None


class RiskItem(BaseModel):
    rule_id: int
    severity: str
    title: str
    message: str
    affects_completion: bool
    estimated_delay_months: int


class KPRequest(BaseModel):
    apartment_id: int
    payment_type: str
    selected_services: List[int] = []
    client_name: Optional[str] = ""


class KPResponse(BaseModel):
    kp_id: str
    complex_name: str
    complex_class: str
    address: str
    apartment_info: str
    area: float
    floor: str
    finishing: str
    price_per_m2: int
    base_price: float
    discount_percent: float
    discount_amount: float
    price_after_discount: float
    services_total: float
    services_breakdown: List[ServiceItem]
    final_price: float
    risks: List[RiskItem]
    risk_level: str
    requires_approval: bool
    completion_date: str
    progress: float
    kp_text: Optional[str] = None       # ← Текст от GigaChat / fallback
    kp_source: str = "fallback"         # ← gigachat | fallback
    pdf_url: Optional[str] = None
    status: str
