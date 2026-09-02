from fastapi import APIRouter
from pydantic import BaseModel
from typing import List

router = APIRouter()


class KPRequest(BaseModel):
    apartment_id: int
    payment_type: str  # наличные | ипотека | рассрочка
    selected_services: List[int] = []
    client_name: str = ""


class KPResponse(BaseModel):
    kp_id: str
    complex_name: str
    apartment_info: str
    base_price: float
    discount_amount: float
    services_total: float
    final_price: float
    risks: List[dict]
    pdf_url: str
    status: str


@router.post("/kp/generate", response_model=KPResponse)
async def generate_kp(request: KPRequest):
    """Генерация коммерческого предложения"""
    # TODO: подключить KPEngine + GigaChat + PDF
    return KPResponse(
        kp_id="kp-2026-001",
        complex_name="Скандинавия",
        apartment_info="2-комн., 58.2 м²",
        base_price=13095000,
        discount_amount=500000,
        services_total=0,
        final_price=12595000,
        risks=[],
        pdf_url="/static/kp-2026-001.pdf",
        status="generated",
    )
