from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import os

from backend.db.session import SessionLocal
from backend.core.kp_engine_db import KPEngineDB
from backend.services.gigachat_service import get_gigachat_service
from backend.schemas import (
    KPRequest, KPResponse, KPTextPayload,
    ServiceItem, RiskItem,
)

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/kp/generate", response_model=KPResponse)
async def generate_kp(request: KPRequest, db: Session = Depends(get_db)):
    engine = KPEngineDB(db)

    kp = engine.calculate_kp(
        apartment_id=request.apartment_id,
        payment_type=request.payment_type,
        selected_services=request.selected_services,
    )
    risks = engine.analyze_risks(request.apartment_id)

    critical_count = sum(1 for r in risks if r["severity"] == "critical")
    warning_count = sum(1 for r in risks if r["severity"] == "warning")
    risk_level = "none"
    if critical_count > 0:
        risk_level = "critical"
    elif warning_count > 0:
        risk_level = "warning"

    context = engine.generate_gigachat_context(
        apartment_id=request.apartment_id,
        payment_type=request.payment_type,
        selected_services=request.selected_services,
    )

    gigachat = get_gigachat_service()
    text_result = gigachat.generate_kp_text(context)

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
        pdf_url="/api/v1/kp/pdf",
        status="generated",
    )


@router.post("/kp/pdf")
async def kp_pdf_from_text(payload: KPTextPayload, db: Session = Depends(get_db)):
    """PDF из УЖЕ сгенерированного текста КП (тот же, что в превью)."""
    engine = KPEngineDB(db)
    context = engine.generate_gigachat_context(
        apartment_id=payload.apartment_id,
        payment_type=payload.payment_type,
        selected_services=payload.selected_services,
    )

    gigachat = get_gigachat_service()
    context["_kp_text_for_pdf"] = payload.kp_text
    context["_kp_table_html"] = gigachat._md_table_to_html(payload.kp_text)
    context["kp_id"] = f"kp-{datetime.now().strftime('%Y%m%d')}-{payload.apartment_id:04d}"

    pdf_path = f"/tmp/kp_dsk_{payload.apartment_id}.pdf"
    try:
        gigachat.generate_pdf(context, pdf_path)
        with open(pdf_path, "rb") as f:
            data = f.read()
        return Response(
            content=data,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"inline; filename=KP-{payload.apartment_id}.pdf"
            },
        )
    finally:
        if os.path.exists(pdf_path):
            os.remove(pdf_path)


@router.get("/kp/pdf/{apartment_id}")
async def kp_pdf_legacy(
    apartment_id: int,
    payment_type: str = "наличные",
    selected_services: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    GET-версия для отладки и браузера.
    Пример: /api/v1/kp/pdf/13?payment_type=ипотека&selected_services=1,3
    """
    services_ids: List[int] = []
    if selected_services:
        for s in selected_services.split(","):
            s = s.strip()
            if s.isdigit():
                services_ids.append(int(s))

    engine = KPEngineDB(db)
    context = engine.generate_gigachat_context(
        apartment_id=apartment_id,
        payment_type=payment_type,
        selected_services=services_ids,
    )

    gigachat = get_gigachat_service()
    kp_result = gigachat.generate_kp_text(context)
    context["_kp_text_for_pdf"] = kp_result.get("kp_text") or ""
    context["_kp_table_html"] = gigachat._md_table_to_html(
        context["_kp_text_for_pdf"]
    )
    context["kp_id"] = f"kp-{datetime.now().strftime('%Y%m%d')}-{apartment_id:04d}"

    pdf_path = f"/tmp/kp_dsk_{apartment_id}.pdf"
    try:
        gigachat.generate_pdf(context, pdf_path)
        with open(pdf_path, "rb") as f:
            data = f.read()
        return Response(
            content=data,
            media_type="application/pdf",
            headers={"Content-Disposition": f"inline; filename=KP-{apartment_id}.pdf"},
        )
    finally:
        if os.path.exists(pdf_path):
            os.remove(pdf_path)