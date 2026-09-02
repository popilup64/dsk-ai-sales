"""
KPEngine — движок формирования КП и анализа рисков для ГК «ДСК»
Пункт 3: Дополнительные услуги (полноценная таблица)
Пункт 7: Управление ожиданиями / анализ рисков (полноценная система)
"""

import json
from datetime import datetime
from typing import List, Dict, Tuple


class KPEngine:
    """
    Движок формирования коммерческого предложения с:
    - Расчётом доп.услуг (паркинг, кладовка, ремонт)
    - Автоматическим анализом рисков по ERP-данным
    - Формированием контекста для GigaChat
    """

    def __init__(self, data_dir: str = "./data"):
        self.data_dir = data_dir
        self._load_data()

    def _load_json(self, name: str):
        with open(f"{self.data_dir}/{name}", "r", encoding="utf-8") as f:
            return json.load(f)

    def _load_data(self):
        complexes = self._load_json("complexes.json")
        sections = self._load_json("sections.json")
        apartments = self._load_json("apartments.json")

        self.complexes = {c["id"]: c for c in complexes}
        self.sections = {s["id"]: s for s in sections}
        self.apartments = {a["id"]: a for a in apartments}

        self.jbi_schedules = self._load_json("jbi_schedules.json")
        self.materials = self._load_json("materials.json")
        self.discount_rules = {d["payment_type"]: d for d in self._load_json("discount_rules.json")}
        self.services_data = {s["id"]: s for s in self._load_json("services.json")}
        self.risk_rules = self._load_json("risk_rules.json")

    # ==================== ПУНКТ 3: Дополнительные услуги ====================
    def calculate_services(self, apartment_id: int, selected_services: List[int]) -> Tuple[float, List[Dict]]:
        """
        Рассчитывает стоимость выбранных доп.услуг.

        Args:
            apartment_id: ID квартиры
            selected_services: Список ID услуг [1, 3] = паркинг + ремонт

        Returns:
            (services_total, services_breakdown)
        """
        apt = self.apartments[apartment_id]
        area = apt["area"]
        services_total = 0.0
        services_breakdown = []

        for sid in selected_services:
            svc = self.services_data[sid]

            if svc["price"] is not None:
                cost = svc["price"]
            elif svc["price_per_m2"] is not None:
                cost = svc["price_per_m2"] * area
            else:
                cost = 0.0

            services_total += cost
            services_breakdown.append({
                "service_id": sid,
                "name": svc["name"],
                "category": svc["category"],
                "cost": round(cost, 2),
                "unit": svc["unit"],
                "description": svc["description"]
            })

        return services_total, services_breakdown

    def calculate_kp(self, apartment_id: int, payment_type: str, 
                     selected_services: List[int]) -> Dict:
        """
        Полный расчёт коммерческого предложения.

        Args:
            apartment_id: ID квартиры
            payment_type: "наличные" | "ипотека" | "рассрочка" | "наличные_акция"
            selected_services: Список ID доп.услуг

        Returns:
            Словарь с полными данными КП
        """
        apt = self.apartments[apartment_id]
        sec = self.sections[apt["section_id"]]
        comp = self.complexes[sec["complex_id"]]

        # 1. Базовая стоимость квартиры
        base_price = apt["area"] * apt["price_per_m2"]

        # 2. Скидка по типу оплаты
        rule = self.discount_rules.get(payment_type, self.discount_rules["ипотека"])
        discount_percent = rule["discount_percent"]
        discount_amount = base_price * (discount_percent / 100)

        # Лимит скидки
        if discount_amount > rule["max_discount_rub"]:
            discount_amount = rule["max_discount_rub"]

        price_after_discount = base_price - discount_amount

        # 3. Дополнительные услуги (ПУНКТ 3 — полноценная таблица)
        services_total, services_breakdown = self.calculate_services(apartment_id, selected_services)

        # 4. Итоговая сумма
        final_price = price_after_discount + services_total

        return {
            "complex": comp,
            "section": sec,
            "apartment": apt,
            "payment_type": payment_type,
            "base_price": round(base_price, 2),
            "discount_percent": discount_percent,
            "discount_amount": round(discount_amount, 2),
            "price_after_discount": round(price_after_discount, 2),
            "services_total": round(services_total, 2),
            "services_breakdown": services_breakdown,
            "final_price": round(final_price, 2),
            "requires_approval": rule["requires_approval"]
        }

    # ==================== ПУНКТ 7: Анализ рисков ====================
    def analyze_risks(self, apartment_id: int) -> List[Dict]:
        """
        Полноценный анализ рисков на основе ERP-данных:
        - Задержки ЖБИ > 30 дней
        - Дефицит / критический дефицит материалов
        - Низкая готовность при приближении срока
        - Незавершённые критические этапы

        Returns:
            Список рисков, отсортированных по severity (critical → warning)
        """
        apt = self.apartments[apartment_id]
        sec = self.sections[apt["section_id"]]
        comp = self.complexes[sec["complex_id"]]
        complex_id = comp["id"]

        risks = []

        # --- Правило 1: Критическая задержка ЖБИ (>30 дней) ---
        delays = [j for j in self.jbi_schedules
                  if j["complex_id"] == complex_id and j["delay_days"] > 30]
        rule_delay = next((r for r in self.risk_rules if r["condition_type"] == "delay"), None)

        for d in delays:
            risks.append({
                "rule_id": rule_delay["id"],
                "severity": rule_delay["severity"],
                "title": rule_delay["rule_name"],
                "message": rule_delay["message_template"].format(
                    material=d["material"],
                    delay_days=d["delay_days"]
                ),
                "affects_completion": True,
                "estimated_delay_months": rule_delay["estimated_delay_months"],
                "source": "jbi_schedule"
            })

        # --- Правило 2 & 3: Дефицит материалов ---
        mats = [m for m in self.materials if m["complex_id"] == complex_id]
        rule_shortage = next((r for r in self.risk_rules if r["condition_type"] == "material_shortage"), None)
        rule_critical = next((r for r in self.risk_rules if r["condition_type"] == "material_critical"), None)

        for m in mats:
            if m["status"] == "критический дефицит":
                risks.append({
                    "rule_id": rule_critical["id"],
                    "severity": rule_critical["severity"],
                    "title": rule_critical["rule_name"],
                    "message": rule_critical["message_template"].format(
                        material=m["material_name"],
                        quantity=m["quantity"],
                        unit=m["unit"],
                        threshold=m["critical_threshold"]
                    ),
                    "affects_completion": True,
                    "estimated_delay_months": rule_critical["estimated_delay_months"],
                    "source": "materials"
                })
            elif m["status"] == "дефицит":
                risks.append({
                    "rule_id": rule_shortage["id"],
                    "severity": rule_shortage["severity"],
                    "title": rule_shortage["rule_name"],
                    "message": rule_shortage["message_template"].format(
                        material=m["material_name"],
                        quantity=m["quantity"],
                        unit=m["unit"]
                    ),
                    "affects_completion": True,
                    "estimated_delay_months": rule_shortage["estimated_delay_months"],
                    "source": "materials"
                })

        # --- Правило 4: Низкая готовность при приближении срока ---
        completion = datetime.strptime(comp["completion_date"], "%Y-%m-%d")
        months_left = (completion - datetime.now()).days / 30

        rule_progress = next((r for r in self.risk_rules if r["condition_type"] == "progress_low"), None)
        if sec["progress"] < rule_progress["threshold"] and months_left < 12:
            risks.append({
                "rule_id": rule_progress["id"],
                "severity": rule_progress["severity"],
                "title": rule_progress["rule_name"],
                "message": rule_progress["message_template"].format(progress=sec["progress"]),
                "affects_completion": True,
                "estimated_delay_months": rule_progress["estimated_delay_months"],
                "source": "progress"
            })

        # --- Правило 5: Незавершённые критические этапы ---
        critical_unfinished = [j for j in self.jbi_schedules
                               if j["complex_id"] == complex_id
                               and j["critical"] is True
                               and j["status"] in ["в работе", "не начато"]]
        rule_unfinished = next((r for r in self.risk_rules if r["condition_type"] == "unfinished_critical"), None)

        if critical_unfinished:
            risks.append({
                "rule_id": rule_unfinished["id"],
                "severity": rule_unfinished["severity"],
                "title": rule_unfinished["rule_name"],
                "message": rule_unfinished["message_template"].format(
                    estimated_delay_months=rule_unfinished["estimated_delay_months"]
                ),
                "affects_completion": True,
                "estimated_delay_months": rule_unfinished["estimated_delay_months"],
                "source": "jbi_critical"
            })

        # Сортировка: critical → warning
        severity_order = {"critical": 0, "warning": 1}
        risks.sort(key=lambda x: severity_order.get(x["severity"], 99))

        return risks

    # ==================== GigaChat: Контекст ====================
    def generate_gigachat_context(self, apartment_id: int, payment_type: str,
                                   selected_services: List[int]) -> Dict:
        """
        Формирует полный контекст для отправки в GigaChat.

        Returns:
            {
                "kp_data": {...},
                "risks": [...],
                "gigachat_prompt_context": {...}
            }
        """
        kp = self.calculate_kp(apartment_id, payment_type, selected_services)
        risks = self.analyze_risks(apartment_id)

        # Сводка рисков текстом
        if risks:
            risk_summary = "\n\nВЫЯВЛЕННЫЕ РИСКИ:\n"
            for r in risks:
                icon = "🔴" if r["severity"] == "critical" else "🟡"
                risk_summary += f"{icon} {r['title']}: {r['message']}\n"
        else:
            risk_summary = "\n\nРиски не выявлены. Строительство идёт по графику."

        # Доп.услуги текстом
        if kp["services_breakdown"]:
            services_text = "\n\nДОПОЛНИТЕЛЬНЫЕ УСЛУГИ:\n"
            for s in kp["services_breakdown"]:
                services_text += f"• {s['name']}: {s['cost']:,.0f} ₽ ({s['description']})\n"
            services_text += f"Итого по услугам: {kp['services_total']:,.0f} ₽"
        else:
            services_text = ""

        context = {
            "kp_data": kp,
            "risks": risks,
            "gigachat_prompt_context": {
                "complex_name": kp["complex"]["name"],
                "complex_class": kp["complex"]["class"],
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

        return context


# ==================== ПРИМЕР ИСПОЛЬЗОВАНИЯ ====================
if __name__ == "__main__":
    engine = KPEngine(data_dir="./data")

    # Пример: Квартира №2, наличные, паркинг + ремонт под ключ
    result = engine.calculate_kp(
        apartment_id=2,
        payment_type="наличные",
        selected_services=[1, 3]
    )
    print(f"КП: {result['final_price']:,.0f} ₽")
    print(f"Требует согласования: {result['requires_approval']}")

    risks = engine.analyze_risks(2)
    print(f"Рисков выявлено: {len(risks)}")
