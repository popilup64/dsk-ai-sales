# DSK AI Sales — AI-помощник отдела продаж ГК «ДСК»

**Архитектурная позиция:** layered monolith (не микросервисы). Единая кодовая база с чётким разделением слоёв: `api/` (контроллеры), `core/` (бизнес-логика), `services/` (внешние интеграции), `models/` / `db/` (SQLAlchemy + SQLite), `schemas/` (Pydantic). Деплой — один контейнер + фронтенд, без сетевой оркестрации.

**Стек в деталях:** Python 3.12, FastAPI (async, OpenAPI `/docs`, Pydantic-валидация), SQLAlchemy 2.0 (SQLite), Jinja2 (шаблоны КП и PDF), Weasyprint (HTML→PDF). AI: GigaChat SDK (`gigachat`) с OAuth (`GIGACHAT_AUTH_KEY` в `.env`), `GigaChat-3-Ultra`, `temperature=0.3`; fallback на локальный Jinja2-шаблон при недоступности. Фронтенд: React 18 + Vite + Tailwind CSS; `renderMarkdown()` с преобразованием `**bold**`, таблиц `|pipe|`, списков в HTML (через `dangerouslySetInnerHTML`). Утилиты: Docker Compose, `weasyprint` для A4 PDF с Playfair Display + золотые (`#c8a45c`) акценты.

## Что реализовано (MVP)

- **ERP-симуляция:** графики ЖБИ, баланс материалов, остатки квартир (`db/init_db.py`, `core/kp_engine_db.py`).
- **KP с GigaChat:** `POST /api/v1/kp/generate`, `generate_kp_text()` (GigaChat или `_generate_fallback()`); текст в формате JSON + `source=gigachat|fallback`.
- **PDF:** нативный `GET /api/v1/kp/pdf/{apartment_id}` — `Response(media_type="application/pdf")` через Weasyprint (`templates/kp_pdf.html`); ошибка `unsupported format character '''` устранена через `fmt()` (предварительное форматирование чисел).
- **Менеджер / диалоги:** `POST /api/v1/manager/analyze` (`manager_support.py` с `OBJECTIONS_DB` — 4 типа возражений: цена, риски сроков, допуслуги, оплата; + `analyze_dialog_gigachat()` с попыкой через GigaChat, fallback на локальную БД; `trigger_word` нормализуется, `undefined` заменяется на реальные рекомендации). `GET /api/v1/competitors` — открытая БД (`COMPETITORS_DB`): Новая Москва, Красногорск (Парк Авеню 290к, Скандинавия 220к, Северная звезда 265к), Химки (Химки-Парк 210к, Московский 230к) с ценами и стрелками ▲/▼ относительно базовой.
- **Риски:** 5 правил (`core/kp_engine_db.py`) — задержки >30 дней, дефицит материалов, низкий прогресс, незавершённые критические этапы, JBI-риски.
- **UI:** анимация печати (`typedText` с `useEffect`), красивый КП-слот (`bg-gradient-to-br`), карточки менеджера с `renderMarkdown()`, типа `conversion_tips` с `→`-спанами.
- **Контроль скидок:** `manager.py` + `schemas/manager.py`; `.env` на корневом уровне (`config.py` ищет `..` и `backend/..`); `AUTH_KEY` не менялся, GigaChat не ломался.

## Защита от типичных ошибок

- `ValueError: unsupported format character '''` в `kp_pdf.html` — исправлено: заменены все `"%'d"|format(...)` на `{var_fmt}` с `fmt()`.
- `404 /manager/analyze` — исправлено подключением `manager.py` в `main.py` + экспорт в `schemas/__init__.py`.
- `KeyError: 'objection_type'` — исправлено: `analyze_dialog()` возвращает `"type"`, endpoint использует `.get()`; GigaChat-ответы нормализуются (`trigger`, `response`, `conversion_tip`).
- `White screen` (`typedText` до `result`) — исправлено порядком `useState` в `App.jsx`.
- `Markdown table` пустой заголовок — исправлен regex с `filter(Boolean)`.

## Как запускать

**Локально (без Docker — в этой среде Docker недоступен):**
```bash
# 1. Backend (GigaChat работает через AUTH_KEY в .env)
source backend/venv/bin/activate
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload

# 2. Frontend (другой терминал)
cd frontend && npm run dev

# 3. Проверка
curl http://localhost:8000/health
curl -X POST http://localhost:8000/api/v1/manager/analyze \
  -H "Content-Type: application/json" \
  -d '{"dialog_text":"дорого, сдвинут сроки"}'
```

**Через Docker (если Docker-демон доступен):**
```bash
sed -i '1d' docker-compose.yml  # убрать obsolete version

docker-compose build
docker-compose up -d

docker-compose ps
docker-compose logs -f backend
docker-compose exec backend bash  # проверка .env

docker-compose down             # остановка
```

URL: `http://localhost:8000/docs` (OpenAPI), `http://localhost:5173` (UI), `http://localhost:8000/api/v1/manager/analyze`, `http://localhost:8000/api/v1/competitors`.

**Переменные:** `.env` (корень + `backend/`), `GIGACHAT_AUTH_KEY` не заменён на `CLIENT_ID/SECRET`.

## Файл-структура (layered monolith)

```
backend/
  app/         config, main (FastAPI + роутеры)
  api/v1/      routes: kp, risks, manager, services, apartments, complexes
  core/        kp_engine_db, manager_support, competitors, manager_support
  services/    gigachat_service (OAuth + SDK + fallback)
  db/          session, init_db, SQLite
  models/      SQLAlchemy ORM
  schemas/     Pydantic (manager, kp, risk, apartment)
  templates/   kp_pdf.html (Weasyprint A4)
frontend/src/
  App.jsx      HomePage, ComplexPage, ManagerSupportBlock, renderMarkdown()
  index.html   Playfair Display + Inter
```

**Документация:** `docs/ARCHITECTURE.md` (почему монолит, FastAPI, React, SQLite), `DOCKER_COMMANDS.md` (команды `build`, `up -d`, `logs`, `down`), `README.md` (этот файл).
