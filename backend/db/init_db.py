import json
import os
from datetime import datetime
from sqlalchemy.orm import Session
from backend.db.session import engine, Base, SessionLocal
from backend.models import (
    Complex, ComplexStatus, ComplexClass,
    Section, SectionStatus,
    Apartment, ApartmentStatus, FinishingType,
    JBISchedule, Material, Service, DiscountRule, RiskRule
)

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def load_json(filename: str):
    filepath = os.path.join(DATA_DIR, filename)
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def init_database():
    """Создаёт таблицы и заливает тестовые данные"""
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # Проверяем, есть ли уже данные
        if db.query(Complex).first():
            print("📦 Данные уже загружены, пропускаем инициализацию")
            return

        print("🚀 Инициализация базы данных...")

        # 1. Жилые комплексы
        complexes_data = load_json("complexes.json")
        for c in complexes_data:
            db.add(Complex(
                id=c["id"],
                name=c["name"],
                address=c["address"],
                district=c.get("district"),
                completion_date=datetime.strptime(c["completion_date"], "%Y-%m-%d").date(),
                status=ComplexStatus(c["status"]),
                class_=ComplexClass(c["class"]),
                price_per_m2_base=c["price_per_m2_base"],
                description=c.get("description")
            ))
        db.commit()
        print(f"  ✅ Комплексы: {len(complexes_data)}")

        # 2. Секции
        sections_data = load_json("sections.json")
        for s in sections_data:
            db.add(Section(
                id=s["id"],
                complex_id=s["complex_id"],
                section_number=s["section_number"],
                floors=s["floors"],
                progress=s["progress"],
                status=SectionStatus(s["status"])
            ))
        db.commit()
        print(f"  ✅ Секции: {len(sections_data)}")

        # 3. Квартиры
        apartments_data = load_json("apartments.json")
        for a in apartments_data:
            db.add(Apartment(
                id=a["id"],
                section_id=a["section_id"],
                floor=a["floor"],
                floor_total=a["floor_total"],
                rooms=a["rooms"],
                room_type=a["room_type"],
                area=a["area"],
                price_per_m2=a["price_per_m2"],
                status=ApartmentStatus(a["status"]),
                finishing=FinishingType(a["finishing"])
            ))
        db.commit()
        print(f"  ✅ Квартиры: {len(apartments_data)}")

        # 4. Графики ЖБИ
        jbi_data = load_json("jbi_schedules.json")
        for j in jbi_data:
            db.add(JBISchedule(
                id=j["id"],
                complex_id=j["complex_id"],
                section_id=j.get("section_id"),
                material=j["material"],
                planned_date=datetime.strptime(j["planned_date"], "%Y-%m-%d").date(),
                actual_date=datetime.strptime(j["actual_date"], "%Y-%m-%d").date() if j.get("actual_date") else None,
                delay_days=j.get("delay_days", 0),
                status=j["status"],
                critical=j.get("critical", False)
            ))
        db.commit()
        print(f"  ✅ Графики ЖБИ: {len(jbi_data)}")

        # 5. Материалы
        materials_data = load_json("materials.json")
        for m in materials_data:
            db.add(Material(
                id=m["id"],
                complex_id=m["complex_id"],
                material_name=m["material_name"],
                quantity=m["quantity"],
                unit=m["unit"],
                min_required=m["min_required"],
                critical_threshold=m["critical_threshold"],
                expected_delivery=datetime.strptime(m["expected_delivery"], "%Y-%m-%d").date() if m.get("expected_delivery") else None,
                status=m["status"]
            ))
        db.commit()
        print(f"  ✅ Материалы: {len(materials_data)}")

        # 6. Услуги
        services_data = load_json("services.json")
        for s in services_data:
            db.add(Service(
                id=s["id"],
                name=s["name"],
                price=s.get("price"),
                price_per_m2=s.get("price_per_m2"),
                unit=s["unit"],
                category=s["category"],
                applicable_to=str(s.get("applicable_to", "all")),
                description=s.get("description"),
                available=s.get("available", True)
            ))
        db.commit()
        print(f"  ✅ Услуги: {len(services_data)}")

        # 7. Правила скидок
        discounts_data = load_json("discount_rules.json")
        for d in discounts_data:
            db.add(DiscountRule(
                id=d["id"],
                payment_type=d["payment_type"],
                discount_percent=d["discount_percent"],
                max_discount_rub=d["max_discount_rub"],
                description=d.get("description"),
                conditions=d.get("conditions"),
                requires_approval=d.get("requires_approval", False)
            ))
        db.commit()
        print(f"  ✅ Правила скидок: {len(discounts_data)}")

        # 8. Правила рисков
        risks_data = load_json("risk_rules.json")
        for r in risks_data:
            db.add(RiskRule(
                id=r["id"],
                rule_name=r["rule_name"],
                condition_type=r["condition_type"],
                threshold=r.get("threshold", 0),
                severity=r["severity"],
                message_template=r["message_template"],
                affects_completion=r.get("affects_completion", True),
                estimated_delay_months=r.get("estimated_delay_months", 0)
            ))
        db.commit()
        print(f"  ✅ Правила рисков: {len(risks_data)}")

        print("🎉 База данных инициализирована!")

    finally:
        db.close()


if __name__ == "__main__":
    init_database()
