"""
KPEngineDB — движок формирования КП и анализа рисков (SQLAlchemy-версия).

Пункт 3: Дополнительные услуги (полноценная таблица)
Пункт 7: Анализ рисков на основе ERP-данных
"""

from datetime import datetime, date
from typing import List, Dict, Tuple
import enum as _enum

from sqlalchemy.orm import Session
from sqlalchemy import select

from backend.models.complex import Complex
from backend.models.section import Section
from backend.models.apartment import Apartment
from backend.models.jbi_schedule import JBISchedule
from backend.models.material import Material
from backend.models.discount_rule import DiscountRule
from backend.models.service import Service
from backend.models.risk_rule import RiskRule


def _to_str(v) -> str:
    """Enum / date / None → строка. Универсальный конвертер."""
    if v is None:
        return ""
    if isinstance(v, _enum.Enum):
        return str(v.value)
    if isinstance(v, (datetime, date)):
        return v.strftime("%Y-%m-%d")
    return str(v)


def _to_float(v, default: float = 0.0) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


class KPEngineDB:
    """Движок формирования КП поверх SQLAlchemy."""

    def __init__(self, db: Session):
        self.db = db

    # ==================== ПУНКТ 3: Дополнительные услуги ====================
    def calculate_services(self, apartment_id: int,
                           selected_services: List[int]) -> Tuple[float, List[Dict]]:
        apt = self.db.get(Apartment, apartment_id)
        if apt is None:
            raise ValueError(f"Квартира {apartment_id} не найдена")
        area = _to_float(apt.area)

        services_total = 0.0
        services_breakdown: List[Dict] = []

        if not selected_services:
            return services_total, services_breakdown

        svcs = self.db.execute(
            select(Service).where(Service.id.in_(selected_services))
        ).scalars().all()
        by_id = {s.id: s for s in svcs}

        for sid in selected_services:
            svc = by_id.get(sid)
            if svc is None:
                continue

            if getattr(svc, "price", None) is not None:
                cost = _to_float(svc.price)
            elif getattr(svc, "price_per_m2", None) is not None:
                cost = _to_float(svc.price_per_m2) * area
            else:
                cost = 0.0

            services_total += cost
            services_breakdown.append({
                "service_id": svc.id,
                "name": svc.name,
                "category": _to_str(getattr(svc, "category", "")),
                "cost": round(cost, 2),
                "unit": _to_str(getattr(svc, "unit", "шт")) or "шт",
                "description": _to_str(getattr(svc, "description", "")),
            })

        return services_total, services_breakdown

    # ==================== Полный расчёт КП ====================
    def calculate_kp(self, apartment_id: int, payment_type: str,
                     selected_services: List[int]) -> Dict:
        apt = self.db.get(Apartment, apartment_id)
        if apt is None:
            raise ValueError(f"Квартира {apartment_id} не найдена")

        sec = self.db.get(Section, apt.section_id)
        if sec is None:
            raise ValueError(f"Секция для квартиры {apartment_id} не найдена")

        comp = self.db.get(Complex, sec.complex_id)
        if comp is None:
            raise ValueError(f"ЖК для квартиры {apartment_id} не найден")

        # 1. Базовая стоимость
        base_price = _to_float(apt.area) * _to_float(apt.price_per_m2)

        # 2. Скидка по типу оплаты
        rule = self.db.execute(
            select(DiscountRule).where(DiscountRule.payment_type == payment_type)
        ).scalar_one_or_none()
        if rule is None:
            rule = self.db.execute(
                select(DiscountRule).where(DiscountRule.payment_type == "ипотека")
            ).scalar_one_or_none()

        discount_percent = _to_float(getattr(rule, "discount_percent", 0))
        discount_amount = base_price * (discount_percent / 100.0)

        max_disc = getattr(rule, "max_discount_rub", None)
        if max_disc is not None and discount_amount > _to_float(max_disc):
            discount_amount = _to_float(max_disc)

        price_after_discount = base_price - discount_amount

        # 3. Доп. услуги
        services_total, services_breakdown = self.calculate_services(
            apartment_id, selected_services
        )

        final_price = price_after_discount + services_total

        return {
            "complex": {
                "id": comp.id,
                "name": comp.name,
                "class_": _to_str(getattr(comp, "class_", None)),
                "address": _to_str(getattr(comp, "address", "")),
                "completion_date": _to_str(getattr(comp, "completion_date", None)),
                "progress": _to_float(getattr(comp, "progress", 0)),
            },
            "section": {
                "id": sec.id,
                "section_number": _to_str(getattr(sec, "section_number", "")),
                "progress": _to_float(getattr(sec, "progress", 0)),
            },
            "apartment": {
                "id": apt.id,
                "room_type": _to_str(apt.room_type),
                "area": _to_float(apt.area),
                "floor": _to_str(apt.floor),
                "floor_total": _to_str(getattr(apt, "floor_total", "")),
                "finishing": _to_str(getattr(apt, "finishing", "")),   # ← Enum → строка
                "price_per_m2": _to_float(apt.price_per_m2),
            },
            "payment_type": payment_type,
            "base_price": round(base_price, 2),
            "discount_percent": discount_percent,
            "discount_amount": round(discount_amount, 2),
            "price_after_discount": round(price_after_discount, 2),
            "services_total": round(services_total, 2),
            "services_breakdown": services_breakdown,
            "final_price": round(final_price, 2),
            "requires_approval": bool(getattr(rule, "requires_approval", False)),
        }

    # ==================== ПУНКТ 7: Анализ рисков ====================
    def analyze_risks(self, apartment_id: int) -> List[Dict]:
        apt = self.db.get(Apartment, apartment_id)
        if apt is None:
            return []
        sec = self.db.get(Section, apt.section_id)
        if sec is None:
            return []
        comp = self.db.get(Complex, sec.complex_id)
        if comp is None:
            return []
        complex_id = comp.id

        risks: List[Dict] = []
        rules = self.db.execute(select(RiskRule)).scalars().all()

        def _rule(condition_type: str):
            return next((r for r in rules if r.condition_type == condition_type), None)

        rule_delay      = _rule("delay")
        rule_shortage   = _rule("material_shortage")
        rule_critical   = _rule("material_critical")
        rule_progress   = _rule("progress_low")
        rule_unfinished = _rule("unfinished_critical")

        # Правило 1: задержки ЖБИ > 30 дней
        if rule_delay is not None:
            delays = self.db.execute(
                select(JBISchedule).where(
                    JBISchedule.complex_id == complex_id,
                    JBISchedule.delay_days > 30,
                )
            ).scalars().all()
            for d in delays:
                risks.append({
                    "rule_id": rule_delay.id,
                    "severity": rule_delay.severity,
                    "title": rule_delay.rule_name,
                    "message": rule_delay.message_template.format(
                        material=d.material, delay_days=d.delay_days
                    ),
                    "affects_completion": True,
                    "estimated_delay_months": rule_delay.estimated_delay_months,
                    "source": "jbi_schedule",
                })

        # Правила 2–3: дефицит материалов
        mats = self.db.execute(
            select(Material).where(Material.complex_id == complex_id)
        ).scalars().all()
        for m in mats:
            if m.status == "критический дефицит" and rule_critical is not None:
                risks.append({
                    "rule_id": rule_critical.id,
                    "severity": rule_critical.severity,
                    "title": rule_critical.rule_name,
                    "message": rule_critical.message_template.format(
                        material=m.material_name,
                        quantity=m.quantity,
                        unit=m.unit,
                        threshold=getattr(m, "critical_threshold", 0),
                    ),
                    "affects_completion": True,
                    "estimated_delay_months": rule_critical.estimated_delay_months,
                    "source": "materials",
                })
            elif m.status == "дефицит" and rule_shortage is not None:
                risks.append({
                    "rule_id": rule_shortage.id,
                    "severity": rule_shortage.severity,
                    "title": rule_shortage.rule_name,
                    "message": rule_shortage.message_template.format(
                        material=m.material_name,
                        quantity=m.quantity,
                        unit=m.unit,
                    ),
                    "affects_completion": True,
                    "estimated_delay_months": rule_shortage.estimated_delay_months,
                    "source": "materials",
                })

        # Правило 4: низкая готовность
        if rule_progress is not None and getattr(comp, "completion_date", None):
            try:
                cd = comp.completion_date
                if isinstance(cd, str):
                    completion = datetime.strptime(cd, "%Y-%m-%d")
                elif isinstance(cd, (datetime, date)):
                    completion = datetime(cd.year, cd.month, cd.day)
                else:
                    completion = None
                if completion is not None:
                    months_left = (completion - datetime.now()).days / 30
                    if sec.progress < rule_progress.threshold and months_left < 12:
                        risks.append({
                            "rule_id": rule_progress.id,
                            "severity": rule_progress.severity,
                            "title": rule_progress.rule_name,
                            "message": rule_progress.message_template.format(
                                progress=sec.progress
                            ),
                            "affects_completion": True,
                            "estimated_delay_months": rule_progress.estimated_delay_months,
                            "source": "progress",
                        })
            except (ValueError, TypeError):
                pass

        # Правило 5: незавершённые критические этапы
        if rule_unfinished is not None:
            critical_unfinished = self.db.execute(
                select(JBISchedule).where(
                    JBISchedule.complex_id == complex_id,
                    JBISchedule.critical.is_(True),
                    JBISchedule.status.in_(["в работе", "не начато"]),
                )
            ).scalars().all()
            if critical_unfinished:
                risks.append({
                    "rule_id": rule_unfinished.id,
                    "severity": rule_unfinished.severity,
                    "title": rule_unfinished.rule_name,
                    "message": rule_unfinished.message_template.format(
                        estimated_delay_months=rule_unfinished.estimated_delay_months
                    ),
                    "affects_completion": True,
                    "estimated_delay_months": rule_unfinished.estimated_delay_months,
                    "source": "jbi_critical",
                })

        severity_order = {"critical": 0, "warning": 1}
        risks.sort(key=lambda x: severity_order.get(x["severity"], 99))
        return risks

    # ==================== GigaChat: Контекст ====================
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

        prompt_ctx = {
            "apartment_id": kp["apartment"]["id"],
            "complex_name": kp["complex"]["name"],
            "complex_class": kp["complex"]["class_"],
            "address": kp["complex"]["address"],
            "completion_date": kp["complex"]["completion_date"],
            "progress": kp["complex"]["progress"],
            "section_number": kp["section"]["section_number"],
            "room_type": kp["apartment"]["room_type"],
            "area": kp["apartment"]["area"],
            "floor": kp["apartment"]["floor"],
            "floor_total": kp["apartment"]["floor_total"],
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
            "requires_approval": kp["requires_approval"],
        }

        return {
            "kp_data": kp,
            "risks": risks,
            "gigachat_prompt_context": prompt_ctx,
        }