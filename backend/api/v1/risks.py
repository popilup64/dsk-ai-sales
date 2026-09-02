from fastapi import APIRouter

router = APIRouter()


@router.get("/risks/{apartment_id}")
async def analyze_risks(apartment_id: int):
    """Анализ рисков для квартиры"""
    # TODO: подключить RiskAnalyzer
    return {
        "apartment_id": apartment_id,
        "risks": [],
        "overall_level": "none",  # none | warning | critical
    }
