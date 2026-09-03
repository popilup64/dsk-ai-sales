from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional, List

from backend.db.session import SessionLocal
from backend.models import Apartment, Section, Complex
from backend.schemas import ApartmentResponse

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/apartments", response_model=List[ApartmentResponse])
async def get_apartments(
    complex_id: Optional[int] = Query(None),
    rooms: Optional[str] = Query(None),
    status: Optional[str] = Query("свободна"),
    min_price: Optional[int] = Query(None),
    max_price: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """Список квартир с фильтрами"""
    query = db.query(Apartment).join(Section).join(Complex)

    if complex_id:
        query = query.filter(Section.complex_id == complex_id)
    if rooms:
        query = query.filter(Apartment.room_type == rooms)
    if status:
        query = query.filter(Apartment.status == status)
    if min_price:
        query = query.filter(Apartment.price_per_m2 >= min_price)
    if max_price:
        query = query.filter(Apartment.price_per_m2 <= max_price)

    apartments = query.all()
    result = []
    for a in apartments:
        result.append(ApartmentResponse(
            id=a.id,
            section_id=a.section_id,
            floor=a.floor,
            floor_total=a.floor_total,
            rooms=a.rooms,
            room_type=a.room_type,
            area=a.area,
            price_per_m2=a.price_per_m2,
            status=a.status.value,
            finishing=a.finishing.value,
            complex_name=a.section.complex.name,
            complex_class=a.section.complex.class_.value
        ))
    return result
