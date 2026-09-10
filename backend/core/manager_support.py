"""
Поддержка менеджера: анализ типовых возражений и рекомендации.
Теперь с интеграцией GigaChat (приоритет), fallback на локальную БД.
"""
import logging
from typing import List, Dict

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ------------------------------------------------------------
# 1. Локальная база типовых возражений (для MVP без NLP)
# ------------------------------------------------------------
OBJECTIONS_DB = [
    {
        "trigger_words": ["дорого", "цена", "дорогая"],
        "objection_type": "цена",
        "response_template": "Мы фиксируем скидку 5% при полной оплате и готовы обсудить индивидуальные условия с руководителем.",
        "conversion_tip": "Акцентируйте выгоду скидки и срок действия (3 дня).",
    },
    {
        "trigger_words": ["сдача", "срок", "сдвиг", "задержка"],
        "objection_type": "риски сроков",
        "response_template": "Строительство идёт под контролем ДСК. При возникновении рисков клиент получает автоматическое уведомление с альтернативными вариантами.",
        "conversion_tip": "Предлагайте резервный лот или гибкий график платежей.",
    },
    {
        "trigger_words": ["паркинг", "кладовка", "ремонт", "услуги"],
        "objection_type": "допуслуги",
        "response_template": "Дополнительные услуги включаются по запросу и фиксируются в КП. Паркинг и ремонт — договорная цена с гарантией качества ДСК.",
        "conversion_tip": "Покажите расчёт экономии при покупке комплекса (паркинг + ремонт).",
    },
    {
        "trigger_words": ["ипотека", "кредит", "процент"],
        "objection_type": "оплата",
        "response_template": "Мы работаем с банками-партнёрами и оформляем ипотеку на выгодных условиях. Рассрочка возможна до 3 месяцев без процентов.",
        "conversion_tip": "Уточните у клиента сумму первоначального взноса — это ускоряет одобрение.",
    },
    {
        "trigger_words": ["перейти", "другой гк", "конкурент", "уход", "сменить", "выбрать другой"],
        "objection_type": "смена застройщика / конкуренты",
        "response_template": "Мы понимаем важность сравнения. ДСК — 58 лет на рынке, 20+ проектов, готовность под контролем с автоматическими уведомлениями. Предлагаем сравнить данные в КП с конкурентами (см. раздел 5).",
        "conversion_tip": "Покажите клиенту реальные данные готовности и сроки прошлых объектов. Предложите визит на стройплощадку.",
    },
]

# ------------------------------------------------------------
# 2. Локальный анализ (по ключевым словам)
# ------------------------------------------------------------
def analyze_dialog(dialog_text: str) -> List[Dict]:
    """Анализ диалога менеджера с клиентом на основе локальной БД."""
    results = []
    text_lower = dialog_text.lower()
    for entry in OBJECTIONS_DB:
        for word in entry["trigger_words"]:
            if word in text_lower:
                results.append({
                    "trigger": word,
                    "trigger_word": word,
                    "type": entry["objection_type"],
                    "response": entry["response_template"],
                    "conversion_tip": entry["conversion_tip"],
                })
                break
    return results

# ------------------------------------------------------------
# 3. Рекомендации (локальные)
# ------------------------------------------------------------
def get_recommendations(objection_type: str) -> List[str]:
    """Подготовка рекомендаций для менеджера по типу возражения."""
    mapping = {
        "цена": [
            "Напомните о скидке 5% и сроке действия (3 дня).",
            "Предложите фиксированную цену при бронировании сегодня.",
        ],
        "риски сроков": [
            "Покажите клиенту данные о готовности (55-82%).",
            "Предложите альтернативный лот или гибкий график платежей.",
        ],
        "допуслуги": [
            "Показать экономию при комплексной покупке (паркинг + ремонт).",
            "Уточнить, нужна ли кладовка или ремонт на этапе бронирования.",
        ],
        "оплата": [
            "Уточнить сумму первоначального взноса для ускорения одобрения.",
            "Предложить рассрочку без процентов до 3 месяцев.",
        ],
    }
    return mapping.get(objection_type, ["Уточните детали у клиента и предложите индивидуальное решение."])

# ------------------------------------------------------------
# 4. Основная функция с приоритетом GigaChat
# ------------------------------------------------------------
def analyze_dialog_gigachat(dialog_text: str) -> Dict:
    """
    Анализ диалога с попыткой через GigaChat.
    Если GigaChat доступен и вернул структурированный ответ — используем его.
    Иначе — fallback на локальную базу.
    Возвращает словарь с полями:
        - detected_objections: int
        - objections: List[Dict]  (каждый словарь содержит как минимум 'type' и др.)
        - recommendations: Dict[str, List[str]]  # по типам
        - conversion_tips: List[str]  # советы по конверсии
        - source: str  # "gigachat" или "local_db"
    """
    results = []
    source_tag = "local_db"

    try:
        from backend.services.gigachat_service import get_gigachat_service
        svc = get_gigachat_service()
        if svc.is_configured:
            logger.info("GigaChat доступен, пробуем получить анализ...")
            gigachat_results = svc.analyze_dialog(dialog_text)  # <- новый метод
            if gigachat_results and isinstance(gigachat_results, list) and len(gigachat_results) > 0:
                results = gigachat_results
                source_tag = "gigachat"
                logger.info(f"GigaChat вернул {len(results)} возражений.")
            else:
                logger.warning("GigaChat вернул пустой или некорректный ответ, используем локальную БД.")
        else:
            logger.info("GigaChat не настроен (is_configured=False), используем локальную БД.")
    except ImportError as e:
        logger.warning(f"Не удалось импортировать gigachat_service: {e}")
    except Exception as e:
        logger.error(f"Ошибка при вызове GigaChat: {e}", exc_info=True)

    # Если GigaChat не дал результатов — используем локальный анализ
    if not results:
        logger.info("Используем локальную базу для анализа.")
        results = analyze_dialog(dialog_text)
        source_tag = "local_db"

    # Формируем итоговый словарь
    recommendations = {}
    conversion_tips = []

    for item in results:
        obj_type = item.get("objection_type") or item.get("type")
        trigger_raw = item.get("trigger_word") or item.get("trigger") or item.get("keyword")
        if not trigger_raw and obj_type:
            trigger_raw = obj_type.split()[0]
        item["trigger"] = trigger_raw or obj_type or "—"
        item["trigger_word"] = trigger_raw or obj_type or "—"
        # Исправляем GigaChat-ответы: если response пуст или undefined — подставляем свой
        if not item.get("response") or item.get("response") == "undefined":
            item["response"] = get_recommendations(obj_type)[0] if obj_type else "Предложите клиенту индивидуальное решение."
        if not item.get("conversion_tip") or str(item.get("conversion_tip")).lower() == "undefined":
            item["conversion_tip"] = get_recommendations(obj_type)[1] if obj_type else "Уточните детали и предложите скидку или гибкий график."
        if not obj_type:
            continue

        # Рекомендации: если GigaChat дал свои — берём их, иначе локальные
        if source_tag == "gigachat" and "recommendations" in item:
            recs = item["recommendations"]
            if isinstance(recs, list):
                recommendations[obj_type] = recs
            else:
                recommendations[obj_type] = [recs]
        else:
            recommendations[obj_type] = get_recommendations(obj_type)

        # Советы по конверсии: если GigaChat дал — берём, иначе из локальной БД или рекомендаций
        if source_tag == "gigachat" and "conversion_tip" in item:
            tip = item["conversion_tip"]
            if isinstance(tip, list):
                conversion_tips.extend(tip)
            else:
                conversion_tips.append(tip)
        else:
            tip = item.get("conversion_tip")
            if tip:
                conversion_tips.append(tip)
            else:
                conversion_tips.extend(get_recommendations(obj_type))

    # Удаляем дубликаты советов
    conversion_tips = list(set(conversion_tips))

    return {
        "detected_objections": len(results),
        "objections": results,
        "recommendations": recommendations,
        "conversion_tips": conversion_tips,
        "source": source_tag,
    }