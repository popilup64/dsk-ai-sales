from fastapi import APIRouter, Query
from typing import Optional

router = APIRouter()


@router.get("/apartments")
async def get_apartments(
    complex_id: Optional[int] = Query(None),
    rooms: Optional[str] = Query(None),
    status: Optional[str] = Query("свободна"),
):
    """Список квартир с фильтрами"""
    # TODO: подключить БД
    return {
        "items": [],
        "filters": {"complex_id": complex_id, "rooms": rooms, "status": status}
    }
