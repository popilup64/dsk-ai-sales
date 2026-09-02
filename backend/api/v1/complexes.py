from fastapi import APIRouter

router = APIRouter()


@router.get("/complexes")
async def get_complexes():
    """Список жилых комплексов"""
    return {
        "items": [
            {
                "id": 1,
                "name": "Скандинавия",
                "class": "комфорт",
                "address": "Москва, поселение Сосенское, ул. Лесная, 15",
                "price_per_m2_base": 220000,
                "status": "строится",
                "progress": 65,
            },
            {
                "id": 2,
                "name": "Парк Авеню",
                "class": "бизнес",
                "address": "Московская область, г. Красногорск, б-р Космонавтов, 8",
                "price_per_m2_base": 290000,
                "status": "строится",
                "progress": 42,
            },
        ]
    }
