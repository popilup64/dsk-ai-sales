"""
Сервис интеграции с GigaChat API.
Если ключи не настроены — использует локальный fallback (Jinja2-шаблон).
"""

import json
import uuid
import logging
from typing import Dict, Optional, List
from datetime import datetime

import httpx
from jinja2 import Template

from backend.app.config import get_settings

settings = get_settings()

# Настройка логирования
logger = logging.getLogger(__name__)

# Константы API
GIGACHAT_OAUTH_URL = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
GIGACHAT_API_URL = "https://api.giga.chat/v1/chat/completions"


class GigaChatService:
    """Клиент для работы с GigaChat API"""

    def __init__(self):
        self.access_token: Optional[str] = None
        self.token_expires_at: Optional[datetime] = None

        # Проверяем, настроен ли GigaChat
        self.is_configured = bool(
            settings.GIGACHAT_CLIENT_ID and settings.GIGACHAT_CLIENT_SECRET
        ) or bool(settings.GIGACHAT_AUTH_KEY)

    # ==================== OAuth2 Авторизация (прямой запрос) ====================
    def _get_access_token(self) -> str:
        """Получает токен через прямой OAuth-запрос с scope=GIGACHAT_API_PERS"""
        if self.access_token and self.token_expires_at and datetime.now() < self.token_expires_at:
            return self.access_token

        auth_key = settings.GIGACHAT_AUTH_KEY
        if not auth_key:
            raise Exception("GIGACHAT_AUTH_KEY не задан")

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
            "RqUID": str(uuid.uuid4()),
            "Authorization": f"Basic {auth_key}",
        }
        data = {"scope": "GIGACHAT_API_PERS"}   # обязательно для физических лиц

        try:
            with httpx.Client(verify=False, timeout=10.0) as client:
                resp = client.post(GIGACHAT_OAUTH_URL, headers=headers, data=data)
                resp.raise_for_status()
                token_data = resp.json()
                token = token_data.get("access_token")
                if not token:
                    raise Exception(f"Токен не получен: {token_data}")
                self.access_token = token

                # expires_at приходит в миллисекундах
                expires_at_ms = token_data.get("expires_at", 0)
                if expires_at_ms:
                    self.token_expires_at = datetime.fromtimestamp(expires_at_ms / 1000.0)
                else:
                    # запасное значение: 30 минут минус 1 минута
                    self.token_expires_at = datetime.fromtimestamp(datetime.now().timestamp() + 1800 - 60)

                return token
        except Exception as e:
            logger.error(f"⚠️ Ошибка получения токена: {e}")
            raise

    # ==================== Построение промпта для КП ====================
    def _build_prompt(self, context: Dict) -> str:
        """Собирает промпт из контекста для GigaChat"""

        ctx = context["gigachat_prompt_context"]

        prompt = f"""Ты — AI-аналитик отдела продаж ГК «ДСК». 
Твоя задача: на основе предоставленных ERP-данных сформировать профессиональное коммерческое предложение (КП) для клиента.

=== ДАННЫЕ ОБ ОБЪЕКТЕ ===
Жилой комплекс: {ctx['complex_name']}
Класс: {ctx['complex_class']}
Адрес: {ctx['address']}
Плановая дата сдачи: {ctx['completion_date']}
Готовность объекта: {ctx['progress']}%
Секция: {ctx['section_number']}

=== ДАННЫЕ О КВАРТИРЕ ===
Тип: {ctx['room_type']}-комнатная
Площадь: {ctx['area']} м²
Этаж: {ctx['floor']}
Отделка: {ctx['finishing']}
Цена за м²: {ctx['price_per_m2']:,.0f} ₽

=== ФИНАНСОВЫЕ УСЛОВИЯ ===
Базовая стоимость: {ctx['base_price']:,.0f} ₽
Тип оплаты: {ctx['payment_type']}
Скидка: {ctx['discount_percent']}% (−{ctx['discount_amount']:,.0f} ₽)
Стоимость после скидки: {ctx['price_after_discount']:,.0f} ₽
{ctx.get('services_text', '')}
ИТОГО К ОПЛАТЕ: {ctx['final_price']:,.0f} ₽

=== АНАЛИЗ РИСКОВ ===
{ctx.get('risk_summary', 'Риски не выявлены.')}

=== ЗАДАЧА ===
Сформируй текст КП в деловом, уверенном стиле. Структура:
1. Приветствие и краткая презентация ЖК (2-3 предложения).
2. Описание квартиры с акцентом на преимущества.
3. Финансовые условия — таблицей, чётко и понятно.
4. Упоминание скидки как выгодного спецпредложения.
5. Если есть риски — мягкое, но честное предупреждение. Не пугай клиента, но не скрывай.
6. Дополнительные услуги (если выбраны).
7. Призыв к действию и срок действия КП (3 дня).
8. Контакты менеджера.

Важно:
- Не придумывай данных, которых нет в контексте.
- Если требуется согласование руководителя — укажи это.
- Ответ дай строго в формате JSON: {{"kp_text": "...", "has_risks": true/false, "risk_level": "none|warning|critical"}}
"""
        return prompt

    # ==================== Отправка в GigaChat (генерация КП) ====================
    def generate_kp_text(self, context: Dict) -> Dict:
        """
        Генерирует текст КП через GigaChat или fallback.

        Returns:
            {"kp_text": str, "has_risks": bool, "risk_level": str, "source": "gigachat|fallback"}
        """
        # Пытаемся через GigaChat даже при ошибках (принудительный режим)
        if not self.is_configured:
            logger.warning("⚠️ GigaChat не настроен, но пытаемся принудительно...")
            from backend.app.config import get_settings
            s = get_settings()
            if s.GIGACHAT_CLIENT_ID or s.GIGACHAT_AUTH_KEY:
                self.is_configured = True

        try:
            token = self._get_access_token()
            prompt = self._build_prompt(context)

            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            }

            payload = {
                "model": settings.GIGACHAT_MODEL,
                "messages": [
                    {"role": "system", "content": "Ты — профессиональный аналитик недвижимости. Пиши деловые тексты на русском языке. Отвечай только в запрошенном JSON-формате."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": settings.GIGACHAT_TEMPERATURE,
                "max_tokens": settings.GIGACHAT_MAX_TOKENS,
            }

            with httpx.Client(verify=False, timeout=settings.GIGACHAT_TIMEOUT) as client:
                response = client.post(
                    GIGACHAT_API_URL,
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                data = response.json()

            # Парсим ответ
            content = data["choices"][0]["message"]["content"]

            # Пытаемся извлечь JSON из ответа
            try:
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()

                result = json.loads(content)
                result["source"] = "gigachat"
                return result
            except json.JSONDecodeError:
                return {
                    "kp_text": content,
                    "has_risks": context.get("risks", []),
                    "risk_level": self._detect_risk_level(context),
                    "source": "gigachat_raw"
                }

        except Exception as e:
            logger.error(f"⚠️ Ошибка GigaChat: {e}")
            logger.info(f"🔧 FALLBACK ENABLED = {settings.GIGACHAT_FALLBACK_ENABLED}")
            if settings.GIGACHAT_FALLBACK_ENABLED:
                return self._generate_fallback(context)
            raise

    # ==================== Fallback: локальный шаблон ====================
    def _generate_fallback(self, context: Dict) -> Dict:
        """Генерирует текст КП локально, без GigaChat"""
        ctx = context["gigachat_prompt_context"]

        template_str = """Уважаемый клиент!

Группа компаний «ДСК» рада предложить Вам эксклюзивную возможность приобретения квартиры в ЖК {{ complex_class|capitalize }}-класса «{{ complex_name }}». Это современный комплекс по адресу {{ address }}, сочетающий передовые архитектурные решения и развитую инфраструктуру для комфортной жизни.

Для Вас подобрана {{ room_type }}-комнатная квартира площадью {{ area }} м² на высоком {{ floor }} этаже из {{ floor_total }}. Планировка обеспечивает максимальное количество света и впечатляющие виды. Отделка: {{ finishing }}.

Финансовые условия:
| Позиция | Сумма (₽) |
| :--- | :--- |
| Базовая стоимость квартиры | {{ base_price_fmt }} |
| Скидка {{ discount_percent }}% (спецпредложение за наличный расчёт) | −{{ discount_amount_fmt }} |
| **Итого за квартиру** | **{{ price_after_discount_fmt }}** |
{% if services_total > 0 %}| Дополнительные услуги ({{ services_breakdown|map(attribute='name')|join(', ') }}) | {{ services_total_fmt }} |{% endif %}
| **ИТОГО К ОПЛАТЕ** | **{{ final_price_fmt }}** |

Мы ценим наше партнерство, поэтому зафиксировали для Вас скидку в размере {{ discount_amount_fmt }} рублей при полной оплате наличными.

=== Важное уведомление о статусе строительства ===
Готовность объекта: {{ progress }}%. {% if risk_summary and 'Риски не выявлены' not in risk_summary %}{{ risk_summary }}{% else %}Строительство идёт по графику. Плановая дата сдачи: {{ completion_date }}.{% endif %}

Дополнительные услуги:
{% if services_breakdown %}{% for s in services_breakdown %}• {{ s.name }}: {{ s.cost_fmt }} ₽{% endfor %}{% else %}• По запросу: паркинг, кладовка, ремонт — уточняйте у менеджера.{% endif %}

Данное предложение действительно в течение {{ kp_valid_days }} банковских дней. Для бронирования квартиры и фиксации цены просим связаться с нами для подготовки договора.

С уважением,
Отдел продаж ГК «ДСК»
Контактное лицо: Ганиев Евгений Маратович — Руководитель проектов ДСК
Телефон: +7 (495) 000-00-00
Email: sales@dsk.ru

Срок действия КП: 3 дня с момента формирования."""

        template = Template(template_str)

        # Форматируем числа
        def fmt(n):
            return f"{int(round(n)):,}".replace(",", " ")
        ctx["price_per_m2_fmt"] = fmt(ctx.get("price_per_m2", 0))
        ctx["base_price_fmt"] = fmt(ctx.get("base_price", 0))
        ctx["discount_amount_fmt"] = fmt(ctx.get("discount_amount", 0))
        ctx["price_after_discount_fmt"] = fmt(ctx.get("price_after_discount", 0))
        ctx["services_total_fmt"] = fmt(ctx.get("services_total", 0))
        ctx["final_price_fmt"] = fmt(ctx.get("final_price", 0))
        for s in ctx.get("services_breakdown", []):
            s["cost_fmt"] = fmt(s.get("cost", 0))

        ctx["kp_id"] = datetime.now().strftime("%Y%m%d-%H%M")

        kp_text = template.render(**ctx)

        has_risks = "Риски не выявлены" not in ctx.get("risk_summary", "")
        risk_level = self._detect_risk_level(context)

        return {
            "kp_text": kp_text,
            "has_risks": has_risks,
            "risk_level": risk_level,
            "source": "fallback"
        }

    # ==================== Генерация PDF (уже была) ====================
    def generate_pdf(self, context: Dict, output_path: str = "/tmp/kp_dsk.pdf") -> str:
        from jinja2 import Template
        ctx = context.get("gigachat_prompt_context", context)
        def fmt(n): return f"{int(round(n)):,}".replace(",", " ")
        ctx["price_per_m2_fmt"] = fmt(ctx.get("price_per_m2", 0))
        ctx["base_price_fmt"] = fmt(ctx.get("base_price", 0))
        ctx["discount_amount_fmt"] = fmt(ctx.get("discount_amount", 0))
        ctx["price_after_discount_fmt"] = fmt(ctx.get("price_after_discount", 0))
        ctx["services_total_fmt"] = fmt(ctx.get("services_total", 0))
        ctx["final_price_fmt"] = fmt(ctx.get("final_price", 0))
        for s in ctx.get("services_breakdown", []): s["cost_fmt"] = fmt(s.get("cost", 0))
        ctx["kp_id"] = datetime.now().strftime("%Y%m%d-%H%M")
        # Преобразуем **слово** → <strong> в risk_summary и других текстовых поля для PDF
        for key in ("risk_summary",):
            if isinstance(ctx.get(key), str):
                ctx[key] = ctx[key].replace("**", "<strong>").replace("**", "</strong>") if "**" in ctx[key] else ctx[key]
        # Более надёжно: заменяем все **...**
        for k, v in ctx.items():
            if isinstance(v, str) and "**" in v:
                # Простая замена: **текст** → <strong>текст</strong>
                import re
                ctx[k] = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", v)

        with open("/home/zhabee/dsk-ai-sales/backend/templates/kp_pdf.html", "r", encoding="utf-8") as f:
            html = Template(f.read()).render(**ctx)
        from weasyprint import HTML
        HTML(string=html).write_pdf(output_path)
        return output_path

    # ==================== НОВЫЙ МЕТОД: анализ диалога ====================
    def analyze_dialog(self, dialog_text: str) -> List[Dict]:
        """
        Отправить диалог в GigaChat и получить список возражений в формате JSON.
        Возвращает массив объектов с полями:
            - objection_type (str): "цена", "риски сроков", "допуслуги" или "оплата"
            - trigger_word (str): ключевое слово, вызвавшее возражение
            - response_template (str): готовый ответ менеджера
            - conversion_tip (str или list): совет по конверсии
            - recommendations (list, опционально): дополнительные рекомендации
        При ошибке или недоступности GigaChat возвращает пустой список.
        """
        if not self.is_configured:
            logger.warning("GigaChat не настроен, анализ через GigaChat недоступен.")
            return []

        prompt = f"""
        Проанализируй диалог менеджера и клиента. Выяви возражения по следующим типам:
        цена, риски сроков, дополнительные услуги (паркинг, кладовка, ремонт), оплата (ипотека, кредит, рассрочка).

        Для каждого найденного возражения верни JSON-массив объектов с полями:
        - "objection_type": один из ["цена", "риски сроков", "допуслуги", "оплата"]
        - "trigger_word": ключевое слово, которое вызвало возражение (строка)
        - "response_template": готовый ответ менеджера (строка)
        - "conversion_tip": совет по увеличению конверсии (строка или массив строк)
        - "recommendations": (опционально) массив рекомендаций (строки)

        Если возражений нет, верни пустой массив [].
        Диалог:
        \"{dialog_text}\"

        Верни только JSON-массив, без пояснений.
        """

        try:
            token = self._get_access_token()
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": settings.GIGACHAT_MODEL,
                "messages": [
                    {"role": "system", "content": "Ты — профессиональный аналитик продаж. Отвечай только в JSON-формате."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.3,  # для более детерминированного ответа
                "max_tokens": 1000,
            }
            with httpx.Client(verify=False, timeout=settings.GIGACHAT_TIMEOUT) as client:
                response = client.post(GIGACHAT_API_URL, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()

            content = data["choices"][0]["message"]["content"]

            # Извлечение JSON из ответа (если обёрнут в ```json ... ```)
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            result = json.loads(content)
            if isinstance(result, list):
                return result
            else:
                logger.warning(f"GigaChat вернул не список, а {type(result)}. Игнорируем.")
                return []
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка парсинга JSON от GigaChat: {e}\nОтвет: {content if 'content' in locals() else ''}")
            return []
        except Exception as e:
            logger.error(f"Ошибка при вызове GigaChat analyze_dialog: {e}", exc_info=True)
            return []

    # ==================== Определение уровня риска ====================
    def _detect_risk_level(self, context: Dict) -> str:
        """Определяет уровень риска из контекста"""
        risks = context.get("risks", [])
        if any(r.get("severity") == "critical" for r in risks):
            return "critical"
        elif any(r.get("severity") == "warning" for r in risks):
            return "warning"
        return "none"


# Singleton
_gigachat_service: Optional[GigaChatService] = None


def get_gigachat_service() -> GigaChatService:
    global _gigachat_service
    if _gigachat_service is None:
        _gigachat_service = GigaChatService()
    return _gigachat_service