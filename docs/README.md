# DSK AI Sales — AI-помощник для отдела продаж ГК «ДСК»

## Описание
Автоматизация процесса продажи квартир на основе ERP-данных о ходе строительства. 
AI-агент анализирует графики работ, остатки материалов, формирует персонализированные 
коммерческие предложения и предупреждает о рисках изменения сроков.

## Стек технологий
- **Backend:** Python 3.11, FastAPI, SQLAlchemy, SQLite
- **Frontend:** React 18, Vite, Tailwind CSS
- **AI:** GigaChat API (обязательное условие заказчика)
- **PDF:** WeasyPrint (HTML → PDF)

## Архитектура
Монолитная слоистая архитектура:
```
backend/
├── api/        # HTTP-роутеры (FastAPI)
├── core/       # Бизнес-логика (КП, риски, скидки)
├── models/     # SQLAlchemy-модели
├── schemas/    # Pydantic-схемы валидации
├── services/   # Внешние интеграции (GigaChat)
└── db/         # Подключение к БД
```

## Запуск

### 1. Backend

```bash
cd backend
python -m venv venv

# Mac/Linux:
source venv/bin/activate

# Windows:
venv\Scripts\activate

pip install -r requirements.txt
```

#### Настройка GigaChat (опционально, но рекомендуется)

1. Зарегистрируйтесь на https://developers.sber.ru/
2. Создайте проект и получите **Client ID** и **Client Secret**
3. Скопируйте файл `.env.example` в `.env` и заполните:

```bash
cp .env.example .env
# Отредактируйте .env — добавьте GIGACHAT_CLIENT_ID и GIGACHAT_CLIENT_SECRET
```

> **Важно:** Если ключи GigaChat не настроены, система автоматически использует 
> **fallback-шаблон** — локально сгенерированный текст КП. Это позволяет 
> разрабатывать и тестировать систему без доступа к API.

#### Запуск сервера

```bash
uvicorn app.main:app --reload --port 8000
```

API доступно по адресу: http://localhost:8000  
Документация (Swagger): http://localhost:8000/docs

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Приложение доступно по адресу: http://localhost:5173

## API Endpoints

| Метод | Endpoint | Описание |
|---|---|---|
| GET | `/health` | Проверка работоспособности |
| GET | `/api/v1/complexes` | Список ЖК |
| GET | `/api/v1/apartments` | Квартиры с фильтрами |
| GET | `/api/v1/services` | Доп. услуги |
| POST | `/api/v1/kp/generate` | **Генерация КП** (расчёт + AI-текст) |
| GET | `/api/v1/risks/{id}` | Анализ рисков |

## Пример: генерация КП

```bash
curl -X POST http://localhost:8000/api/v1/kp/generate   -H "Content-Type: application/json"   -d '{
    "apartment_id": 2,
    "payment_type": "наличные",
    "selected_services": [1, 3]
  }'
```

**Ответ:**
```json
{
  "kp_id": "kp-20260903-0002",
  "complex_name": "Скандинавия",
  "apartment_info": "2-комн., 58.2 м²",
  "base_price": 13095000,
  "discount_amount": 500000,
  "final_price": 16064000,
  "risks": [...],
  "risk_level": "warning",
  "kp_text": "КОММЕРЧЕСКОЕ ПРЕДЛОЖЕНИЕ...",
  "kp_source": "fallback"
}
```

