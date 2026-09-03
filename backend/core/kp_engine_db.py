"""
KPEngineDB — движок КП и рисков, работающий с SQLAlchemy БД
"""

from datetime import datetime
from typing import List, Dict, Tuple
from sqlalchemy.orm import Session

from backend.models import (
    Complex, Section, Apartment, JBISchedule, Material,
    Service, DiscountRule, RiskRule
)


class KPEngineDB:
    """Движок формирования КП и анализа рисков (через БД)"""

    def __init__(self, db: Session):
        self.db = db

    # ==================== ПУНКТ 3: Доп.услуги ====================
    def calculate_services(self, apartment_id: int, selected_services: List[int]) -> Tuple[float, List[Dict]]:
        apt = self.db.query(Apartment).filter(Apartment.id == apartment_id).first()
        if not apt:
            return 0.0, []

        area = apt.area
        services_total = 0.0
        services_breakdown = []

        for sid in selected_services:
            svc = self.db.query(Service).filter(Service.id == sid).first()
            if not svc:
                continue

            if svc.price is not None:
                cost = float(svc.price)
            elif svc.price_per_m2 is not None:
                cost = float(svc.price_per_m2) * area
            else:
                cost = 0.0

            services_total += cost
            services_breakdown.append({
                "service_id": sid,
                "name": svc.name,
                "category": svc.category,
                "cost": round(cost, 2),
                "unit": svc.unit,
                "description": svc.description
            })

        return services_total, services_breakdown

    def calculate_kp(self, apartment_id: int, payment_type: str,
                     selected_services: List[int]) -> Dict:
        apt = self.db.query(Apartment).filter(Apartment.id == apartment_id).first()
        if not apt:
            raise ValueError(f"Квартира {apartment_id} не найдена")

        sec = self.db.query(Section).filter(Section.id == apt.section_id).first()
        comp = self.db.query(Complex).filter(Complex.id == sec.complex_id).first()

        # 1. Базовая стоимость
        base_price = apt.area * apt.price_per_m2

        # 2. Скидка
        rule = self.db.query(DiscountRule).filter(DiscountRule.payment_type == payment_type).first()
        if not rule:
            rule = self.db.query(DiscountRule).filter(DiscountRule.payment_type == "ипотека").first()

        discount_percent = rule.discount_percent if rule else 0.0
        discount_amount = base_price * (discount_percent / 100)

        if rule and discount_amount > rule.max_discount_rub:
            discount_amount = float(rule.max_discount_rub)

        price_after_discount = base_price - discount_amount

        # 3. Доп.услуги
        services_total, services_breakdown = self.calculate_services(apartment_id, selected_services)

        # 4. Итог
        final_price = price_after_discount + services_total

        return {
            "complex": {
                "id": comp.id,
                "name": comp.name,
                "address": comp.address,
                "class_": comp.class_.value,
                "completion_date": comp.completion_date.isoformat(),
                "progress": sec.progress,
            },
            "section": {"id": sec.id, "section_number": sec.section_number, "progress": sec.progress},
            "apartment": {
                "id": apt.id,
                "floor": apt.floor,
                "floor_total": apt.floor_total,
                "rooms": apt.rooms,
                "room_type": apt.room_type,
                "area": apt.area,
                "price_per_m2": apt.price_per_m2,
                "finishing": apt.finishing.value,
            },
            "payment_type": payment_type,
            "base_price": round(base_price, 2),
            "discount_percent": discount_percent,
            "discount_amount": round(discount_amount, 2),
            "price_after_discount": round(price_after_discount, 2),
            "services_total": round(services_total, 2),
            "services_breakdown": services_breakdown,
            "final_price": round(final_price, 2),
            "requires_approval": rule.requires_approval if rule else False
        }

    # ==================== ПУНКТ 7: Анализ рисков ====================
    def analyze_risks(self, apartment_id: int) -> List[Dict]:
        apt = self.db.query(Apartment).filter(Apartment.id == apartment_id).first()
        if not apt:
            return []

        sec = self.db.query(Section).filter(Section.id == apt.section_id).first()
        comp = self.db.query(Complex).filter(Complex.id == sec.complex_id).first()
        complex_id = comp.id

        risks = []

        # --- Правило 1: Задержки ЖБИ (>30 дней) ---
        delays = self.db.query(JBISchedule).filter(
            JBISchedule.complex_id == complex_id,
            JBISchedule.delay_days > 30
        ).all()
        rule_delay = self.db.query(RiskRule).filter(RiskRule.condition_type == "delay").first()

        for d in delays:
            if rule_delay:
                risks.append({
                    "rule_id": rule_delay.id,
                    "severity": rule_delay.severity,
                    "title": rule_delay.rule_name,
                    "message": rule_delay.message_template.format(
                        material=d.material,
                        delay_days=d.delay_days
                    ),
                    "affects_completion": rule_delay.affects_completion,
                    "estimated_delay_months": rule_delay.estimated_delay_months,
                    "source": "jbi_schedule"
                })

        # --- Правило 2 & 3: Дефицит материалов ---
        mats = self.db.query(Material).filter(Material.complex_id == complex_id).all()
        rule_shortage = self.db.query(RiskRule).filter(RiskRule.condition_type == "material_shortage").first()
        rule_critical = self.db.query(RiskRule).filter(RiskRule.condition_type == "material_critical").first()

        for m in mats:
            if m.status == "критический дефицит" and rule_critical:
                risks.append({
                    "rule_id": rule_critical.id,
                    "severity": rule_critical.severity,
                    "title": rule_critical.rule_name,
                    "message": rule_critical.message_template.format(
                        material=m.material_name,
                        quantity=m.quantity,
                        unit=m.unit,
                        threshold=m.critical_threshold
                    ),
                    "affects_completion": rule_critical.affects_completion,
                    "estimated_delay_months": rule_critical.estimated_delay_months,
                    "source": "materials"
                })
            elif m.status == "дефицит" and rule_shortage:
                risks.append({
                    "rule_id": rule_shortage.id,
                    "severity": rule_shortage.severity,
                    "title": rule_shortage.rule_name,
                    "message": rule_shortage.message_template.format(
                        material=m.material_name,
                        quantity=m.quantity,
                        unit=m.unit
                    ),
                    "affects_completion": rule_shortage.affects_completion,
                    "estimated_delay_months": rule_shortage.estimated_delay_months,
                    "source": "materials"
                })

        # --- Правило 4: Низкая готовность ---
        completion = datetime.strptime(comp.completion_date.isoformat(), "%Y-%m-%d")
        months_left = (completion - datetime.now()).days / 30

        rule_progress = self.db.query(RiskRule).filter(RiskRule.condition_type == "progress_low").first()
        if rule_progress and sec.progress < rule_progress.threshold and months_left < 12:
            risks.append({
                "rule_id": rule_progress.id,
                "severity": rule_progress.severity,
                "title": rule_progress.rule_name,
                "message": rule_progress.message_template.format(progress=sec.progress),
                "affects_completion": rule_progress.affects_completion,
                "estimated_delay_months": rule_progress.estimated_delay_months,
                "source": "progress"
            })

        # --- Правило 5: Незавершённые критические этапы ---
        critical_unfinished = self.db.query(JBISchedule).filter(
            JBISchedule.complex_id == complex_id,
            JBISchedule.critical == True,
            JBISchedule.status.in_(["в работе", "не начато"])
        ).all()
        rule_unfinished = self.db.query(RiskRule).filter(RiskRule.condition_type == "unfinished_critical").first()

        if critical_unfinished and rule_unfinished:
            risks.append({
                "rule_id": rule_unfinished.id,
                "severity": rule_unfinished.severity,
                "title": rule_unfinished.rule_name,
                "message": rule_unfinished.message_template.format(
                    estimated_delay_months=rule_unfinished.estimated_delay_months
                ),
                "affects_completion": rule_unfinished.affects_completion,
                "estimated_delay_months": rule_unfinished.estimated_delay_months,
                "source": "jbi_critical"
            })

        severity_order = {"critical": 0, "warning": 1}
        risks.sort(key=lambda x: severity_order.get(x["severity"], 99))

        return risks

    def generate_gigachat_context(self, apartment_id: int, payment_type: str,
                                   selected_services: List[int]) -> Dict:
        kp = self.calculate_kp(apartment_id, payment_type, selected_services)
        risks = self.analyze_risks(apartment_id)

        if risks:
            risk_summary = "\n\nВЫЯВЛЕННЫЕ РИСКИ:\n"
            for r in risks:
                icon = "🔴" if r["severity"] == "critical" else "🟡"
                risk_summary += f"{icon} {r['title']}: {r['message']}\n"
        else:
            risk_summary = "\n\nРиски не выявлены. Строительство идёт по графику."

        if kp["services_breakdown"]:
            services_text = "\n\nДОПОЛНИТЕЛЬНЫЕ УСЛУГИ:\n"
            for s in kp["services_breakdown"]:
                services_text += f"• {s['name']}: {s['cost']:,.0f} ₽ ({s['description']})\n"
            services_text += f"Итого по услугам: {kp['services_total']:,.0f} ₽"
        else:
            services_text = ""

        return {
            "kp_data": kp,
            "risks": risks,
            "gigachat_prompt_context": {
                "complex_name": kp["complex"]["name"],
                "complex_class": kp["complex"]["class_"],
                "address": kp["complex"]["address"],
                "completion_date": kp["complex"]["completion_date"],
                "section_number": kp["section"]["section_number"],
                "progress": kp["section"]["progress"],
                "room_type": kp["apartment"]["room_type"],
                "area": kp["apartment"]["area"],
                "floor": f"{kp['apartment']['floor']} из {kp['apartment']['floor_total']}",
                "finishing": kp["apartment"]["finishing"],
                "price_per_m2": kp["apartment"]["price_per_m2"],
                "base_price": kp["base_price"],
                "payment_type": payment_type,
                "discount_percent": kp["discount_percent"],
                "discount_amount": kp["discount_amount"],
                "price_after_discount": kp["price_after_discount"],
                "services_total": kp["services_total"],
                "services_breakdown": kp["services_breakdown"],
                "final_price": kp["final_price"],
                "risk_summary": risk_summary,
                "services_text": services_text,
                "requires_approval": kp["requires_approval"]
            }
        }
