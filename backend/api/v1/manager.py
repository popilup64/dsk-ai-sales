from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.db.session import SessionLocal
from backend.core.manager_support import analyze_dialog_gigachat, get_recommendations
from backend.core.competitors import get_competitors_for_district
from backend.schemas import ManagerAnalysisRequest, ManagerAnalysisResponse

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/manager/analyze")
async def analyze_dialog_endpoint(request: ManagerAnalysisRequest):
    results = analyze_dialog_gigachat(request.dialog_text)
    recommendations = {}
    for r in results.get("objections", []):
        recommendations[r.get("type") or r.get("objection_type")] = get_recommendations(r.get("type") or r.get("objection_type"))
    return {
        "detected_objections": results.get("detected_objections", len(results.get("objections", []))),
        "objections": results.get("objections", []),
        "recommendations": recommendations,
        "conversion_tips": results.get("conversion_tips", []),
        "source": results.get("source", "local_db"),
    }


@router.get("/competitors")
async def competitors(district: str = "Новая Москва"):
    return {
        "district": district,
        "competitors": get_competitors_for_district(district)
    }
