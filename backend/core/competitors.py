"""
Открытые базы конкурирующих объектов недвижимости в том же районе (имитация).
"""
from typing import List, Dict

COMPETITORS_DB = [
    {
        "complex_name": "ЖК «Европейский»",
        "address": "Москва, Новая Москва, ул. Тёплый Стан, 15",
        "district": "Новая Москва",
        "price_per_m2": 245000,
        "status": "строится",
        "class_": "комфорт",
        "completion_date": "2027-06-30",
        "progress": 62,
    },
    {
        "complex_name": "ЖК «Крымский квартал»",
        "address": "Москва, ул. Крымская, 12",
        "district": "Новая Москва",
        "price_per_m2": 238000,
        "status": "строится",
        "class_": "комфорт",
        "completion_date": "2027-09-15",
        "progress": 48,
    },
    {
        "complex_name": "ЖК «Городские истории»",
        "address": "Москва, пр-т Труда, 42",
        "district": "Новая Москва",
        "price_per_m2": 280000,
        "status": "строится",
        "class_": "бизнес",
        "completion_date": "2027-12-20",
        "progress": 35,
    },
    # Красногорск
    {
        "complex_name": "ЖК «Парк Авеню»",
        "address": "Красногорск, б-р Космонавтов, 8",
        "district": "Красногорск",
        "price_per_m2": 290000,
        "status": "строится",
        "class_": "бизнес",
        "completion_date": "2028-03-15",
        "progress": 58,
    },
    {
        "complex_name": "ЖК «Скандинавия»",
        "address": "Красногорск, ул. Лесная, 15 (Сосенское)",
        "district": "Красногорск",
        "price_per_m2": 220000,
        "status": "сдан",
        "class_": "комфорт",
        "completion_date": "2024-12-01",
        "progress": 100,
    },
    {
        "complex_name": "ЖК «Северная звезда»",
        "address": "Красногорск, пр-т Ленина, 22",
        "district": "Красногорск",
        "price_per_m2": 265000,
        "status": "строится",
        "class_": "комфорт",
        "completion_date": "2027-08-20",
        "progress": 45,
    },
    # Химки
    {
        "complex_name": "ЖК «Химки-Парк»",
        "address": "Химки, ул. Молодёжная, 3",
        "district": "Химки",
        "price_per_m2": 210000,
        "status": "строится",
        "class_": "комфорт",
        "completion_date": "2027-11-10",
        "progress": 40,
    },
    {
        "complex_name": "ЖК «Московский»",
        "address": "Химки, пр-т Мира, 7",
        "district": "Химки",
        "price_per_m2": 230000,
        "status": "строится",
        "class_": "бизнес",
        "completion_date": "2028-01-30",
        "progress": 22,
    },
]


def get_competitors_for_district(district: str = "Новая Москва") -> List[Dict]:
    return [
        {
            "name": c["complex_name"],
            "address": c["address"],
            "district": c["district"],
            "price_per_m2": c["price_per_m2"],
            "status": c["status"],
            "class_": c["class_"],
            "completion": c["completion_date"],
            "progress": c["progress"],
        }
        for c in COMPETITORS_DB if c["district"] == district
    ]
