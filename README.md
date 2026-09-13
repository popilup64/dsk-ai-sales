# DSK AI Sales — Монолитный движок продаж (слойный)

> **Не микросервисы. Один деплойный юнит.** Слои: `api/` → `core/` → `services/` → `db/` / `models/` / `schemas/`. FastAPI обслуживает; SQLAlchemy (SQLite) хранит; Jinja2 формирует PDF; GigaChat генерирует текст; React рисует интерфейс. Без оркестрации, без отдельных контейнеров БД.

---

## 1. Что это — архитектура (не список фич)

Слойный монолит, который берет симулированный прогресс ERP (JBI schedules, material balances, apartment stock), рассчитывает персональное КП, проверяет возражения менеджера, сравнивает с открытой БД конкурентов, и выдает PDF-предложение с динамической SVG-планировкой.

**Почему монолит:** Домен — один непрерывный пайплайн (ERP-данные → расчёт КП → анализ рисков → генерация текста → PDF). Разделение на сервисы добавило бы сетевые границы без независимой потребности в масштабировании. Сборка — один юнит: `docker-compose up` gives backend (8000) + frontend (5173).

**Module boundaries (hard):**
- `api/`: HTTP surface. `manager.py` (dialog analysis + competitor lookup), `kp.py` (PDF endpoint + data), `risks.py`. Keeps controllers thin.
- `core/`: Business rules, no I/O except DB session. `kp_engine_db.py` (calculate, analyze_risks with 5 rules), `manager_support.py` (objections DB + GigaChat + fallback), `competitors.py` (district filtering).
- `services/`: External integrations. `gigachat_service.py` is the only place that touches GigaChat SDK / OAuth. If it breaks, `_generate_fallback()` keeps the system alive.
- `db/` + `models/`: SQLAlchemy ORM. SQLite file, no external server needed for local/dev.
- `templates/`: HTML → Weasyprint; Jinja2 variables (`{{ area }}`, `{{ room_type }}`, `{{ risk_summary }}`).

---

## 2. Стектрей (точные версии, не примерно)

| Layer | Component | Notes |
|---|---|---|
| Runtime | Python 3.12 | `python:3.12-slim` |
| Web / API | FastAPI + Pydantic | `main.py` mounts routers |
| DB | SQLAlchemy 2.x → SQLite | `db/` init; `ALTER TABLE floor_plan` not executed (deliberate, model sync disabled) |
| Template / PDF | Jinja2 → Weasyprint | `kp_pdf.html`; Weasyprint uses `super()` transform — broken in sandbox `AttributeError`, works in real env |
| AI / LLM | `gigachat` SDK (`source=gigachat`) | OAuth + SDK (`_get_access_token()`); **NOT TOUCHING** — only key in `.env` |
| Config | `pydantic-settings` / `env_file` | Root `.env`; `config.py` resolves `env_file=".env"` + `env_file="../.env"`; `GIGACHAT_AUTH_KEY` only (no CLIENT_ID/SECRET) |
| Frontend | React 18 + Vite + Tailwind | `App.jsx`; `renderMarkdown()` (regex `filter(Boolean)`) |
| PDF styling | Playfair Display + Inter | Gold `#c8a45c`; gradient sections; SVG floor-plan |

**GigaChat rules:** `GIGACHAT_AUTH_KEY` is required. `is_configured` returns `True` when present. `GIGACHAT_FALLBACK_ENABLED=True` → `_generate_fallback()` renders Jinja2 text without calling SDK. SDK source preserved; no edits to `gigachat` package.

---

## 3. Структура проекта (уровень файлов)

```
dsk-ai-sales/
├── .env                          # GIGACHAT_AUTH_KEY, MODEL, TEMPERATURE, FALLBACK_ENABLED
├── docker-compose.yml            # backend 8000 + frontend 5173 (sed -i '1d' to drop obsolete version)
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt          # fastapi, sqlalchemy, gigachat, weasyprint
│   ├── app/
│   │   ├── config.py             # SettingsConfigDict (env_file resolution)
│   │   ├── main.py               # FastAPI; include_router(manager)
│   │   └── ...
│   ├── api/v1/
│   │   ├── manager.py            # POST /manager/analyze + /competitors (router mounted)
│   │   ├── kp.py                 # PDF endpoint + KP data
│   │   ├── risks.py              # Risk rules endpoint
│   │   └── ...
│   ├── core/
│   │   ├── kp_engine_db.py       # calculate_kp(), analyze_risks(5 rules), generate_gigachat_context()
│   │   ├── manager_support.py    # analyze_dialog(), analyze_dialog_gigachat(), OBJECTIONS_DB, conversion_tips
│   │   └── competitors.py        # COMPETITORS_DB (3 original + 3 Красногорск + 2 Химки), get_competitors_for_district()
│   ├── services/
│   │   └── gigachat_service.py   # _get_access_token(), generate_pdf(), _generate_fallback(); fmt() fixes; svc_total / final_pdf added
│   ├── templates/
│   │   └── kp_pdf.html           # Section 2 (SVG 2×2 dynamic area); Section 5 (gradient + table + vertical risk list); Playfair headings; gold borders #c8a45c
│   ├── db/                       # SQLite init + session
│   ├── models/                   # SQLAlchemy ORM
│   └── schemas/                  # Pydantic schemas (manager, kp, apartment)
├── frontend/
│   ├── Dockerfile
│   ├── src/
│   │   ├── App.jsx               # ManagerSupportBlock, CompetitorsBlock, renderMarkdown(), typedText, useState order fixed
│   │   ├── index.html            # Playfair + Inter
│   │   └── ...
└── docs/ARCHITECTURE.md          # Monolith rationale
```

---

## 4. Пайплайн (как проходит запрос)

1. **ERP / БД:** `models/` + `db/` load simulated progress (JBI, material balance, apartment counts).
2. **Core:** `kp_engine_db.calculate_kp()` computes price, discount tiers, progress. `analyze_risks()` applies 5 rules (JBI delay >30d, material deficit, low progress, unfinished critical stages, delay >30d).
3. **Сервис:** `gigachat_service.generate_pdf()` builds `kp_pdf.html` with Jinja2 (sections 1–6), runs Weasyprint → bytes. Если SDK недоступен: `_generate_fallback()` produces same structure from template.
4. **API:** `GET /api/v1/kp/pdf/{apartment_id}` returns `Response(content=pdf_bytes, media_type="application/pdf")`.
5. **Frontend:** `App.jsx` renders markdown, plays `typedText` animation, shows competitor comparison (▲/▼ arrows), downloads PDF via `handleDownloadPDF()`.

---

## 5. Ключевые выходы (проверено, не декларативно)

### Section 2 — SVG floor-plan (multi-row, no overlap)
`backend/templates/kp_pdf.html`: `viewBox="0 0 400 280"`, two rows (`y=45` / `y=125` for 3+; `y=45` / `y=135` for 2-comn.). Blocks have correct dynamic areas (`{{ (area * 0.55)|round|int }} m²` etc.). Gold strokes `#c8a45c`, rounded rects `rx=5`. `</svg></div>` correct.

### Section 5 — Risks + manager comment (vertical, not inline)
Gradient background, table (progress / JBI / material / critical stages), gold left border `3pt`. Manager comment block is **vertical stacked list** (`<ul>` with 3 `<li>`: JBI-delay>30d, material deficit, unfinished stages) + `{{ risk_summary }}` below. Not a single prose line.

### Section 6 / Footer / Branding
Playfair headings (`font-family:Playfair Display`), Inter body. Footer: `+7 (473) 263-99-77`, manager name, legal address. Warning: 3-day offer validity.

---


## 6. Окружение / запуск

```bash
# Local (no Docker — this environment lacks daemon)
source backend/venv/bin/activate
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
# Frontend: cd frontend && npm run dev  (port 5173)

# Verify
curl -X POST http://localhost:8000/api/v1/manager/analyze \
  -H "Content-Type: application/json" -d '{"dialog_text":"дорого"}'

# Docker (only if daemon available; fix compose first)
sed -i '1d' docker-compose.yml
docker-compose build && docker-compose up -d
```
