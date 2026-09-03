from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.db.session import SessionLocal
from backend.core.kp_engine_db import KPEngineDB

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/risks/{apartment_id}")
async def analyze_risks(apartment_id: int, db: Session = Depends(get_db)):
    """Анализ рисков для квартиры"""
    engine = KPEngineDB(db)
    risks = engine.analyze_risks(apartment_id)

    critical_count = sum(1 for r in risks if r["severity"] == "critical")
    warning_count = sum(1 for r in risks if r["severity"] == "warning")

    level = "none"
    if critical_count > 0:
        level = "critical"
    elif warning_count > 0:
        level = "warning"

    return {
        "apartment_id": apartment_id,
        "risks": risks,
        "overall_level": level,
        "total_critical": critical_count,
        "total_warning": warning_count,
    }
