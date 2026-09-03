from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from backend.db.session import SessionLocal
from backend.models import Service
from backend.schemas import ServiceResponse

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/services", response_model=List[ServiceResponse])
async def get_services(db: Session = Depends(get_db)):
    """Список дополнительных услуг"""
    services = db.query(Service).filter(Service.available == True).all()
    return [
        ServiceResponse(
            id=s.id,
            name=s.name,
            price=s.price,
            price_per_m2=s.price_per_m2,
            unit=s.unit,
            category=s.category,
            description=s.description
        )
        for s in services
    ]
