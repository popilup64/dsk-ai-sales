"""
Сервис интеграции с GigaChat API.
Если ключи не настроены — использует локальный fallback (Jinja2-шаблон).
"""

import json
import re
import uuid
import logging
from pathlib import Path
from typing import Dict, Optional, List
from datetime import datetime

import httpx
from jinja2 import Template

from backend.app.config import get_settings

settings = get_settings()

logger = logging.getLogger(__name__)

# Константы API
GIGACHAT_OAUTH_URL = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
GIGACHAT_API_URL = "https://api.giga.chat/v1/chat/completions"

# Путь к шаблону PDF (не зависит от CWD)
_TEMPLATE_PDF = Path(__file__).resolve().parents[1] / "templates" / "kp_pdf.html"


class GigaChatService:
    """Клиент для работы с GigaChat API"""

    def __init__(self):
        self.access_token: Optional[str] = None
        self.token_expires_at: Optional[datetime] = None

        self.is_configured = bool(
            settings.GIGACHAT_CLIENT_ID and settings.GIGACHAT_CLIENT_SECRET
        ) or bool(settings.GIGACHAT_AUTH_KEY)

    # ==================== OAuth2 ====================
    def _get_access_token(self) -> str:
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
        data = {"scope": "GIGACHAT_API_PERS"}

        try:
            with httpx.Client(verify=False, timeout=10.0) as client:
                resp = client.post(GIGACHAT_OAUTH_URL, headers=headers, data=data)
                resp.raise_for_status()
                token_data = resp.json()
                token = token_data.get("access_token")
                if not token:
                    raise Exception(f"Токен не получен: {token_data}")
                self.access_token = token

                expires_at_ms = token_data.get("expires_at", 0)
                if expires_at_ms:
                    self.token_expires_at = datetime.fromtimestamp(expires_at_ms / 1000.0)
                else:
                    self.token_expires_at = datetime.fromtimestamp(
                        datetime.now().timestamp() + 1800 - 60
                    )
                return token
        except Exception as e:
            logger.error(f"⚠️ Ошибка получения токена: {e}")
            raise

    # ==================== Markdown → HTML ====================
    @staticmethod
    def _md_table_to_html(kp_text: str) -> str:
        """
        Извлекает первую markdown-таблицу из текста КП и превращает её в HTML.
        Возвращает "" если таблицы нет.
        """
        if not kp_text:
            return ""

        table_lines: List[str] = []
        in_table = False
        for raw in kp_text.splitlines():
            line = raw.strip()
            if line.startswith("|") and line.endswith("|"):
                table_lines.append(line)
                in_table = True
            elif in_table:
                # таблица закончилась — дальше не идём
                break

        if not table_lines:
            return ""

        rows: List[List[str]] = []
        for line in table_lines:
            # строка-разделитель вида | :--- | :--- |
            if re.fullmatch(r"\|[\s:\-|]+\|", line):
                continue
            cells = [c.strip() for c in line.strip("|").split("|")]
            rows.append(cells)

        if not rows:
            return ""

        html = ['<table style="width:100%;border-collapse:collapse;font-size:9.5pt;margin:8pt 0">']
        for i, row in enumerate(rows):
            tag = "th" if i == 0 else "td"
            style_cell = (
                "background:#0a1f44;color:#fff;font-weight:700;"
                if i == 0
                else ""
            )
            html.append("<tr>")
            for cell in row:
                cell_html = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", cell)
                html.append(
                    f'<{tag} style="{style_cell}text-align:left;'
                    f'padding:7pt;border:0.5pt solid #ddd">{cell_html}</{tag}>'
                )
            html.append("</tr>")
        html.append("</table>")
        return "".join(html)

    # ==================== Промпт для КП ====================
    def _build_prompt(self, context: Dict) -> str:
        ctx = context["gigachat_prompt_context"]

        # Жёсткая подмена: GigaChat не должен менять цифры
        bp = int(round(ctx.get("base_price", 0)))
        disc = int(round(ctx.get("discount_amount", 0)))
        after_disc = int(round(ctx.get("price_after_discount", bp - disc)))
        final = int(round(ctx.get("final_price", bp - disc)))
        svc_total = int(round(ctx.get("services_total", 0)))
        ptype = ctx.get("payment_type", "наличный расчёт")
        disc_text = f"{disc:,}".replace(",", " ") if disc > 0 else "0"

        services_lines = ""
        for s in ctx.get("services_breakdown", []):
            services_lines += f"\n| {s['name']} | {int(round(s['cost'])):,} ₽ |".replace(",", " ")

        services_names = ", ".join(
            s["name"] for s in ctx.get("services_breakdown", [])
        ) or "нет"

        prompt = f"""Ты — AI-аналитик отдела продаж ГК «ДСК».
Твоя задача: на основе предоставленных ERP-данных сформировать профессиональное коммерческое предложение (КП) для клиента.

ВАЖНО: используй ТОЛЬКО следующие цифры из БД — не придумывай и не округляй по-своему:
- Базовая стоимость: {bp:,} ₽ (замени запятые на пробелы)
- Скидка {ctx.get('discount_percent', 0)}% ({ptype}): − {disc_text} ₽ (если ипотека — скидка 0 ₽)
- После скидки: {after_disc:,} ₽
- Доп. услуги (если выбраны): {services_lines if services_lines else 'нет'}
- ИТОГО К ОПЛАТЕ: {final:,} ₽
Итоговая сумма в тексте КП ДОЛЖНА быть ровно {final:,} ₽. Не отклоняйся ни на рубль.

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
Этаж: {ctx['floor']} из {ctx.get('floor_total', '?')}
Отделка: {ctx['finishing']}
Цена за м²: {ctx['price_per_m2']:,.0f} ₽

=== ФИНАНСОВЫЕ УСЛОВИЯ (из БД — не меняй) ===
Тип оплаты: {ptype}
Базовая: {bp:,} ₽
Скидка: {disc_text} ₽
После скидки: {after_disc:,} ₽
{ctx.get('services_text', '')}
ИТОГО К ОПЛАТЕ: {final:,} ₽

=== АНАЛИЗ РИСКОВ ===
{ctx.get('risk_summary', 'Риски не выявлены.')}

=== ЗАДАЧА ===
Сформируй текст КП в деловом, уверенном стиле. Обязательно должна быть таблица с точными цифрами выше. Упомяни выбранные услуги ({services_names}) и тип оплаты ({ptype}). Если ипотека — укажи, что скидка 0%, но фиксируется базовая цена.

Структура текста:
1. Приветствие и краткая презентация ЖК (2–3 предложения).
2. Описание квартиры с акцентом на преимущества.
3. Финансовые условия — таблицей, чётко и понятно.
4. Упоминание скидки как выгодного спецпредложения.
5. Если есть риски — мягкое, но честное предупреждение.
6. Дополнительные услуги (если выбраны).
7. Призыв к действию и срок действия КП (3 дня).
8. Контакты менеджера.

Ответ строго в формате JSON: {{"kp_text":"...", "has_risks":true/false, "risk_level":"none|warning|critical"}}
"""
        return prompt

    # ==================== Генерация текста КП ====================
    def generate_kp_text(self, context: Dict) -> Dict:
        """
        Генерирует текст КП через GigaChat или fallback.
        Возвращает: {"kp_text": str, "has_risks": bool, "risk_level": str, "source": str}
        Дополнительно кладёт в context:
            context["_kp_text_for_pdf"] — точный текст (для PDF)
            context["_kp_table_html"]   — HTML-таблица из markdown (для PDF)
        """
        if not self.is_configured:
            logger.warning("⚠️ GigaChat не настроен, пробуем принудительно...")
            from backend.app.config import get_settings as _gs
            s = _gs()
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
                    {
                        "role": "system",
                        "content": (
                            "Ты — профессиональный аналитик недвижимости. "
                            "Пиши деловые тексты на русском языке. "
                            "Отвечай только в запрошенном JSON-формате."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                "temperature": settings.GIGACHAT_TEMPERATURE,
                "max_tokens": settings.GIGACHAT_MAX_TOKENS,
            }

            with httpx.Client(verify=False, timeout=settings.GIGACHAT_TIMEOUT) as client:
                response = client.post(GIGACHAT_API_URL, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()

            content = data["choices"][0]["message"]["content"]

            try:
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()

                result = json.loads(content)
                result["source"] = "gigachat"
                # ← ключевое: сохраняем текст и HTML-таблицу в context,
                #   чтобы PDF-эндпоинт их использовал без повторной генерации
                context["_kp_text_for_pdf"] = result.get("kp_text", content)
                context["_kp_table_html"] = self._md_table_to_html(
                    context["_kp_text_for_pdf"]
                )
                return result
            except json.JSONDecodeError:
                context["_kp_text_for_pdf"] = content
                context["_kp_table_html"] = self._md_table_to_html(content)
                return {
                    "kp_text": content,
                    "has_risks": bool(context.get("risks", [])),
                    "risk_level": self._detect_risk_level(context),
                    "source": "gigachat_raw",
                }

        except Exception as e:
            logger.error(f"⚠️ Ошибка GigaChat: {e}")
            logger.info(f"🔧 FALLBACK ENABLED = {settings.GIGACHAT_FALLBACK_ENABLED}")
            if settings.GIGACHAT_FALLBACK_ENABLED:
                return self._generate_fallback(context)
            raise

    # ==================== Fallback ====================
    def _generate_fallback(self, context: Dict) -> Dict:
        ctx = context.get("gigachat_prompt_context", {})
        kp_data = context.get("kp_data") if isinstance(context.get("kp_data"), dict) else None

        # Принудительно берём цифры из kp_data (а не из GigaChat)
        if kp_data:
            for k in ("base_price", "price_after_discount", "discount_amount",
                      "final_price", "services_total"):
                if k in kp_data and kp_data[k] is not None:
                    ctx.setdefault(k, kp_data[k])

        # Форматирование чисел с пробелами
        def fmt(n):
            try:
                return f"{int(round(float(n))):,}".replace(",", " ")
            except Exception:
                return "0"

        ctx = dict(ctx)  # не мутируем исходный
        ctx["base_price_fmt"] = fmt(ctx.get("base_price", 0))
        ctx["discount_amount_fmt"] = fmt(ctx.get("discount_amount", 0))
        ctx["price_after_discount_fmt"] = fmt(ctx.get("price_after_discount", 0))
        ctx["services_total_fmt"] = fmt(ctx.get("services_total", 0))
        ctx["final_price_fmt"] = fmt(ctx.get("final_price", 0))
        for s in ctx.get("services_breakdown", []):
            s["cost_fmt"] = fmt(s.get("cost", 0))
        ctx.setdefault("kp_valid_days", 3)
        ctx.setdefault("floor_total", "?")

        template_str = """Уважаемый клиент!

Группа компаний «ДСК» рада предложить Вам эксклюзивную возможность приобретения квартиры в ЖК {{ complex_class|capitalize }}-класса «{{ complex_name }}». Это современный комплекс по адресу {{ address }}, сочетающий передовые архитектурные решения и развитую инфраструктуру для комфортной жизни.

Для Вас подобрана {{ room_type }}-комнатная квартира площадью {{ area }} м² на высоком {{ floor }} этаже из {{ floor_total }}. Планировка обеспечивает максимальное количество света и впечатляющие виды. Отделка: {{ finishing }}.

Финансовые условия:
| Позиция | Сумма (₽) |
| :--- | :--- |
| Базовая стоимость квартиры | {{ base_price_fmt }} ₽ |
| Скидка ({{ discount_percent }}% — {{ 'спецпредложение за наличный расчёт' if discount_percent > 0 else 'без скидки — ипотека' }}) | {% if discount_amount > 0 %}− {{ discount_amount_fmt }} ₽{% else %}0 ₽{% endif %} |
| Стоимость квартиры со скидкой | {{ price_after_discount_fmt }} ₽ |
{% if services_total > 0 %}| Дополнительные услуги ({{ services_breakdown|map(attribute='name')|join(', ') }}) | {{ services_total_fmt }} ₽ |{% endif %}
| **ИТОГО К ОПЛАТЕ** | **{{ final_price_fmt }} ₽** |

Мы ценим наше партнерство. Скидка {{ discount_percent }}% фиксируется для типа оплаты <strong>{{ payment_type }}</strong>. При полной оплате скидка составляет {{ discount_amount_fmt }} рублей.

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

        kp_text = Template(template_str).render(**ctx)

        # Сохраняем текст и HTML-таблицу в context для PDF
        context["_kp_text_for_pdf"] = kp_text
        context["_kp_table_html"] = self._md_table_to_html(kp_text)

        has_risks = "Риски не выявлены" not in ctx.get("risk_summary", "")
        risk_level = self._detect_risk_level(context)

        return {
            "kp_text": kp_text,
            "has_risks": has_risks,
            "risk_level": risk_level,
            "source": "fallback",
        }

    # ==================== PDF ====================
    def generate_pdf(self, context: Dict, output_path: str = "/tmp/kp_dsk.pdf") -> str:
        """
        Рендерит PDF.
        ВАЖНО: никакой повторной генерации КП — берём уже сохранённые
        context["_kp_text_for_pdf"] и context["_kp_table_html"].
        """
        gc = context.get("gigachat_prompt_context") or {}
        kp_data = context.get("kp_data") or {}

        def _fmt(n):
            try:
                return f"{int(round(float(n))):,}".replace(",", " ")
            except Exception:
                return "0"

        final_num = int(round(float(
            kp_data.get("final_price") or gc.get("final_price") or 0
        )))
        base_num = int(round(float(
            kp_data.get("base_price") or gc.get("base_price") or 0
        )))

        ctx = {
            # идентификация
            "kp_id":         context.get("kp_id", "-"),
            "apartment_id":  gc.get("apartment_id", ""),
            # объект
            "complex_name":  gc.get("complex_name", "ДСК"),
            "complex_class": gc.get("complex_class", ""),
            "address":       gc.get("address", ""),
            "progress":      gc.get("progress", 0),
            "section_number": gc.get("section_number", ""),
            "completion_date": gc.get("completion_date", ""),
            # квартира
            "room_type":     gc.get("room_type", ""),
            "area":          gc.get("area", 0),
            "floor":         gc.get("floor", ""),
            "floor_total":   gc.get("floor_total", ""),
            "finishing":     gc.get("finishing", ""),
            # финансы
            "discount_percent": gc.get("discount_percent", 0) or 0,
            "final_price":   final_num,
            "final_pdf":     final_num,
            "base_price_pdf": base_num,
            "final_price_fmt": _fmt(final_num),
            "base_price_fmt":  _fmt(base_num),
            # риски
            "risk_summary":  gc.get("risk_summary", ""),
            # текст из превью
            "_kp_text_for_pdf": context.get("_kp_text_for_pdf", ""),
            "_kp_table_html":   context.get("_kp_table_html", ""),
        }

        with open(str(_TEMPLATE_PDF), "r", encoding="utf-8") as f:
            html = Template(f.read()).render(**ctx)

        from weasyprint import HTML
        HTML(string=html).write_pdf(output_path)
        return output_path

    # ==================== Анализ диалога ====================
    def analyze_dialog(self, dialog_text: str) -> List[Dict]:
        """
        Отправляет диалог в GigaChat и получает список возражений в JSON.
        """
        if not self.is_configured:
            logger.warning("GigaChat не настроен, анализ недоступен.")
            return []

        prompt = f"""
        Проанализируй диалог менеджера и клиента. Выяви ВСЕ возражения, даже неявные.
        Не используй жёсткий список типов — определи сам на основе текста.
        Верни JSON-массив объектов с полями:
        - "objection_type": строка
        - "trigger_word": ключевое слово из диалога
        - "response_template": готовый ответ менеджера (2-3 предложения)
        - "conversion_tip": совет по конверсии
        - "recommendations": массив строк (опционально)

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
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.3,
                "max_tokens": 1000,
            }
            with httpx.Client(verify=False, timeout=settings.GIGACHAT_TIMEOUT) as client:
                response = client.post(GIGACHAT_API_URL, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()

            content = data["choices"][0]["message"]["content"]

            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            result = json.loads(content)
            if isinstance(result, list):
                return result
            logger.warning(f"GigaChat вернул не список, а {type(result)}. Игнорируем.")
            return []
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка парсинга JSON от GigaChat: {e}")
            return []
        except Exception as e:
            logger.error(f"Ошибка при analyze_dialog: {e}", exc_info=True)
            return []

    # ==================== Уровень риска ====================
    def _detect_risk_level(self, context: Dict) -> str:
        risks = context.get("risks", [])
        if any(r.get("severity") == "critical" for r in risks):
            return "critical"
        if any(r.get("severity") == "warning" for r in risks):
            return "warning"
        return "none"


# Singleton
_gigachat_service: Optional[GigaChatService] = None


def get_gigachat_service() -> GigaChatService:
    global _gigachat_service
    if _gigachat_service is None:
        _gigachat_service = GigaChatService()
    return _gigachat_service