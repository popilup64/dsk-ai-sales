from fastapi import APIRouter

router = APIRouter()


@router.get("/services")
async def get_services():
    """Список дополнительных услуг"""
    return {
        "items": [
            {"id": 1, "name": "Подземный паркинг", "price": 850000, "unit": "место"},
            {"id": 2, "name": "Кладовое помещение", "price": 120000, "unit": "шт"},
            {"id": 3, "name": "Ремонт «под ключ»", "price_per_m2": 45000, "unit": "м²"},
            {"id": 4, "name": "Ремонт «предчистовая»", "price_per_m2": 22000, "unit": "м²"},
        ]
    }
