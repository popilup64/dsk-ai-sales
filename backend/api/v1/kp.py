from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
import os

from backend.db.session import SessionLocal
from backend.core.kp_engine_db import KPEngineDB
from backend.services.gigachat_service import get_gigachat_service
from backend.schemas import KPRequest, KPResponse, ServiceItem, RiskItem

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/kp/generate", response_model=KPResponse)
async def generate_kp(request: KPRequest, db: Session = Depends(get_db)):
    """
    Генерация коммерческого предложения:
    1. Расчёт цены через KPEngineDB
    2. Анализ рисков
    3. Генерация текста через GigaChat (или fallback)
    """

    # 1. Расчёт КП и рисков
    engine = KPEngineDB(db)

    kp = engine.calculate_kp(
        apartment_id=request.apartment_id,
        payment_type=request.payment_type,
        selected_services=request.selected_services
    )

    risks = engine.analyze_risks(request.apartment_id)

    # 2. Определяем уровень риска
    critical_count = sum(1 for r in risks if r["severity"] == "critical")
    warning_count = sum(1 for r in risks if r["severity"] == "warning")
    risk_level = "none"
    if critical_count > 0:
        risk_level = "critical"
    elif warning_count > 0:
        risk_level = "warning"

    # 3. Генерируем контекст для GigaChat
    context = engine.generate_gigachat_context(
        apartment_id=request.apartment_id,
        payment_type=request.payment_type,
        selected_services=request.selected_services
    )

    # 4. Генерируем текст КП (GigaChat или fallback)
    gigachat = get_gigachat_service()
    text_result = gigachat.generate_kp_text(context)

    # 5. Формируем ответ
    services_breakdown = [ServiceItem(**s) for s in kp["services_breakdown"]]
    risks_response = [RiskItem(**r) for r in risks]

    return KPResponse(
        kp_id=f"kp-{datetime.now().strftime('%Y%m%d')}-{request.apartment_id:04d}",
        complex_name=kp["complex"]["name"],
        complex_class=kp["complex"]["class_"],
        address=kp["complex"]["address"],
        apartment_info=f"{kp['apartment']['room_type']}-комн., {kp['apartment']['area']} м²",
        area=kp["apartment"]["area"],
        floor=f"{kp['apartment']['floor']} из {kp['apartment']['floor_total']}",
        finishing=kp["apartment"]["finishing"],
        price_per_m2=kp["apartment"]["price_per_m2"],
        base_price=kp["base_price"],
        discount_percent=kp["discount_percent"],
        discount_amount=kp["discount_amount"],
        price_after_discount=kp["price_after_discount"],
        services_total=kp["services_total"],
        services_breakdown=services_breakdown,
        final_price=kp["final_price"],
        risks=risks_response,
        risk_level=risk_level,
        requires_approval=kp["requires_approval"],
        completion_date=kp["complex"]["completion_date"],
        progress=kp["complex"]["progress"],
        kp_text=text_result.get("kp_text"),
        kp_source=text_result.get("source", "fallback"),
        pdf_url=f"/api/v1/kp/pdf/{request.apartment_id}",
        status="generated"
    )


@router.get("/kp/pdf/{apartment_id}")
async def kp_pdf(apartment_id: int, db: Session = Depends(get_db)):
    """Генерация PDF КП через Weasyprint"""
    engine = KPEngineDB(db)
    context = engine.generate_gigachat_context(
        apartment_id=apartment_id,
        payment_type="наличные",
        selected_services=[]
    )
    gigachat = get_gigachat_service()
    pdf_path = f"/tmp/kp_dsk_{apartment_id}.pdf"
    try:
        gigachat.generate_pdf(context, pdf_path)
        with open(pdf_path, "rb") as f:
            data = f.read()
        return Response(
            content=data,
            media_type="application/pdf",
            headers={"Content-Disposition": f"inline; filename=KP-{apartment_id}.pdf"}
        )
    finally:
        if os.path.exists(pdf_path): os.remove(pdf_path)
