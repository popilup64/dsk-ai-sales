from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from backend.db.session import SessionLocal
from backend.models import Complex, Section, Apartment
from backend.schemas import ComplexResponse

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/complexes", response_model=List[ComplexResponse])
async def get_complexes(db: Session = Depends(get_db)):
    """Список жилых комплексов"""
    complexes = db.query(Complex).all()
    result = []
    for c in complexes:
        avg_progress = sum(s.progress for s in c.sections) / len(c.sections) if c.sections else 0
        data = {
            "id": c.id, "name": c.name, "address": c.address,
            "district": c.district, "completion_date": c.completion_date,
            "status": c.status.value, "class_": c.class_.value,
            "price_per_m2_base": c.price_per_m2_base, "description": c.description,
            "progress": round(avg_progress, 1)
        }
        result.append(ComplexResponse(**data))
    return result


@router.get("/complexes/{complex_id}/apartments")
def list_apartments(complex_id: int, db: Session = Depends(get_db)):
    """Квартиры в ЖК"""
    section_ids = [s.id for s in db.query(Section).filter(Section.complex_id == complex_id).all()]
    apts = db.query(Apartment).filter(Apartment.section_id.in_(section_ids)).all()
    return {
        "complex_id": complex_id,
        "apartments": [
            {
                "id": a.id, "section_id": a.section_id,
                "floor": a.floor, "floor_total": a.floor_total,
                "rooms": a.rooms, "room_type": a.room_type,
                "area": a.area, "price_per_m2": a.price_per_m2,
                "status": a.status.value if hasattr(a.status, 'value') else a.status,
                "finishing": a.finishing.value if hasattr(a.finishing, 'value') else a.finishing
            } for a in apts
        ]
    }
