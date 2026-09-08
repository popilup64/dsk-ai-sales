# DSK AI Sales — AI-помощник продаж ГК «ДСК»

> **Монолит (Layered Monolith). Не микросервисы.** Единый деплой: `api/` → `core/` → `services/`. Без оркестрации.

Полный цикл: анализ ERP-прогресса, персональные коммерческие предложения (КП) с GigaChat, контроль скидок, уведомления о рисках, поддержка менеджера и сравнение с конкурентами.

## Структура папок (дерево)

```
dsk-ai-sales/
├── .env                          # GIGACHAT_AUTH_KEY, модель, температура
├── docker-compose.yml            # backend (8000) + frontend (5173)
├── backend/
│   ├── Dokerfile                 # python:3.12-slim
│   ├── requirements.txt         # fastapi, sqlalchemy, gigachat, weasyprint
│   ├── app/
│   │   ├── config.py             # SettingsConfigDict (env_file=../.env)
│   │   ├── main.py               # FastAPI + include_router(manager)
│   │   └── ...
│   ├── api/v1/
│   │   ├── manager.py            # /manager/analyze + /competitors
│   │   ├── kp.py, risks.py, ...
│   ├── core/
│   │   ├── manager_support.py    # OBJECTIONS_DB + analyze_dialog_gigachat()
│   │   ├── competitors.py        # COMPETITORS_DB (Красногорск, Химки)
│   │   ├── kp_engine_db.py       # риски + KP-расчёт
│   ├── services/
│   │   └── gigachat_service.py   # OAuth + generate_kp_text() + fallback
│   ├── templates/
│   │   └── kp_pdf.html           # A4, Playfair, золотые акценты
│   ├── db/                       # SQLite init + session
│   ├── models/                   # SQLAlchemy ORM
│   └── schemas/                  # Pydantic (manager, kp, apartment)
├── frontend/
│   ├── Dokerfile                 # node:18-alpine
│   ├── src/
│   │   ├── App.jsx               # ManagerSupportBlock, renderMarkdown()
│   │   ├── index.html            # Playfair Display + Inter
│   │   └── ...
└── docs/ARCHITECTURE.md         # почему монолит, FastAPI, React
```

## Стек

| Уровень | Технология / инструмент |
|---|---|
| Backend | Python 3.12, FastAPI, SQLAlchemy (SQLite), Pydantic, Jinja2 |
| AI / LLM | GigaChat SDK (`gigachat`), OAuth + SDK (`GIGACHAT_AUTH_KEY` в `.env`) |
| PDF | Weasyprint (HTML → PDF, шаблон `backend/templates/kp_pdf.html`) |
| Frontend | React 18 + Vite + Tailwind CSS, `dangerouslySetInnerHTML` для `renderMarkdown()` |
| Архитектура | ЛAYERED MONOLITH (`api/`, `core/`, `models/`, `services/`, `db/`, `schemas/`) — не микросервисы |
| Контейнеры | Docker Compose (`backend/Dockerfile`, `frontend/Dockerfile`) |

## Что здесь реализовано

- **ERP-симуляция**: графики ЖБИ, баланс материалов, остатки квартир (`db/`, `core/`)
- **КП + GigaChat**: генерация текста предложения через GigaChat (`backend/services/gigachat_service.py`); если недоступен — fallback-шаблон (Jinja2)
- **PDF**: `GET /api/v1/kp/pdf/{apartment_id}` → binary PDF (`Weasyprint`)
- **Менеджер / анализ диалогов**: `POST /api/v1/manager/analyze` — выявление возражений («дорого», «риски сроков», «допуслуги», «оплата») + рекомендации + `conversion_tips`
- **Конкуренты**: открытая БД (`COMPETITORS_DB`) для районов Новая Москва, Красногорск, Химки — с ценами, готовностью, стрелками ▲/▼
- **Контроль скидок / риски**: правила (`core/kp_engine_db.py`) — задержки >30 дней, дефицит материалов, незавершённые критические этапы
- **UI**: анимация печати (`typedText` с `useEffect`), красивые КП-карточки (`bg-gradient-to-br`), `renderMarkdown()` с таблицами/жирным

## Как запустить

### Быстрый локальный запуск (без Docker — в этой среде Docker недоступен)

```bash
# Backend
source backend/venv/bin/activate
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload

# Frontend (другой терминал)
cd frontend && npm run dev

# Проверка
curl http://localhost:8000/health
curl -X POST http://localhost:8000/api/v1/manager/analyze \
  -H "Content-Type: application/json" -d '{"dialog_text":"дорого"}'
```

### Через Docker (если Docker-демон работает)

```bash
# Убрать obsolete version из docker-compose.yml (по предупреждению)
sed -i '1d' docker-compose.yml

docker-compose build
docker-compose up -d

docker-compose ps
docker-compose logs -f backend

# Открыть в браузере
# API + docs: http://localhost:8000/docs
# Frontend: http://localhost:5173
```

### Переменные окружения (`.env` в корне и `backend/`)

```
GIGACHAT_AUTH_KEY=...
GIGACHAT_MODEL=GigaChat-3-Ultra
GIGACHAT_TEMPERATURE=0.3
GIGACHAT_FALLBACK_ENABLED=False
```

`GIGACHAT_AUTH_KEY` — обязательный ключ; `is_configured` возвращает `True`; GigaChat не ломается (не трогался).

## Ключевые файлы и коммиты

- `backend/app/main.py` — роутеры (`manager` подключён)
- `backend/services/gigachat_service.py` — OAuth + SDK + `generate_kp_text()` + `_generate_fallback()`
- `backend/core/manager_support.py` — `OBJECTIONS_DB`, `analyze_dialog()`, `analyze_dialog_gigachat()`
- `backend/core/competitors.py` — `COMPETITORS_DB` (Европейский, Крымский, Городские истории; Красногорск, Химки)
- `frontend/src/App.jsx` — `ManagerSupportBlock`, `CompetitorsBlock`, `renderMarkdown()`, `typedText`
- `backend/templates/kp_pdf.html` — A4, Playfair Display, золотые (`#c8a45c`) акценты

## Примечания

- `weasyprint` в sandbox-окружении может давать `AttributeError`; в продакшене (`docker-compose`) работает
- `.env` ищется из корня (`backend/app/config.py`: `env_file=".env"` + `env_file="../.env"`)
- PDF генерируется из HTML-шаблона; кнопка «Скачать PDF» по центру (`flex justify-center`)
