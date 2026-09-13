# DSK AI Sales — Monolith Sales Engine (Layered)

> **Not microservices. One deploy unit.** Layers: `api/` → `core/` → `services/` → `db/` / `models/` / `schemas/`. FastAPI serves; SQLAlchemy (SQLite) persists; Jinja2 renders PDF; GigaChat generates text; React renders the interface. No orchestration, no separate DB containers.

---

## 1. What this is — architecture (not a feature list)

A layered monolith that takes simulated ERP progress (JBI schedules, material balances, apartment stock), calculates a personalized commercial proposal (KP), checks manager objections, compares with open competitor DB, and produces a PDF offer with a dynamic SVG floor-plan.

**Why monolith:** The domain is one continuous pipeline (ERP data → KP calculation → risk analysis → text generation → PDF). Splitting into services would add network boundaries without independent scaling needs. The deck is one build: `docker-compose up` gives backend (8000) + frontend (5173).

**Module boundaries (hard):**
- `api/`: HTTP surface. `manager.py` (dialog analysis + competitor lookup), `kp.py` (PDF endpoint + data), `risks.py`. Keeps controllers thin.
- `core/`: Business rules, no I/O except DB session. `kp_engine_db.py` (calculate, analyze_risks with 5 rules), `manager_support.py` (objections DB + GigaChat + fallback), `competitors.py` (district filtering).
- `services/`: External integrations. `gigachat_service.py` is the only place that touches GigaChat SDK / OAuth. If it breaks, `_generate_fallback()` keeps the system alive.
- `db/` + `models/`: SQLAlchemy ORM. SQLite file, no external server needed for local/dev.
- `templates/`: HTML → Weasyprint; Jinja2 variables (`{{ area }}`, `{{ room_type }}`, `{{ risk_summary }}`).

---

## 2. Stack (exact versions, not approximate)

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

## 3. Project structure (file-level)

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

## 4. The pipeline (how a request travels)

1. **ERP / DB:** `models/` + `db/` load simulated progress (JBI, material balance, apartment counts).
2. **Core:** `kp_engine_db.calculate_kp()` computes price, discount tiers, progress. `analyze_risks()` applies 5 rules (JBI delay >30d, material deficit, low progress, unfinished critical stages, delay >30d).
3. **Service:** `gigachat_service.generate_pdf()` builds `kp_pdf.html` with Jinja2 (sections 1–6), runs Weasyprint → bytes. If SDK unavailable: `_generate_fallback()` produces same structure from template.
4. **API:** `GET /api/v1/kp/pdf/{apartment_id}` returns `Response(content=pdf_bytes, media_type="application/pdf")`.
5. **Frontend:** `App.jsx` renders markdown, plays `typedText` animation, shows competitor comparison (▲/▼ arrows), downloads PDF via `handleDownloadPDF()`.

---

## 5. Critical outputs (verified, not aspirational)

### Section 2 — SVG floor-plan (multi-row, no overlap)
`backend/templates/kp_pdf.html`: `viewBox="0 0 400 280"`, two rows (`y=45` / `y=125` for 3+; `y=45` / `y=135` for 2-comn.). Blocks have correct dynamic areas (`{{ (area * 0.55)|round|int }} m²` etc.). Gold strokes `#c8a45c`, rounded rects `rx=5`. `</svg></div>` correct.

### Section 5 — Risks + manager comment (vertical, not inline)
Gradient background, table (progress / JBI / material / critical stages), gold left border `3pt`. Manager comment block is **vertical stacked list** (`<ul>` with 3 `<li>`: JBI-delay>30d, material deficit, unfinished stages) + `{{ risk_summary }}` below. Not a single prose line.

### Section 6 / Footer / Branding
Playfair headings (`font-family:Playfair Display`), Inter body. Footer: `+7 (473) 263-99-77`, manager name, legal address. Warning: 3-day offer validity.

---

## 6. What is fixed (issues I hit — and did not paper over)

| Symptom | Cause | Fix (file) |
|---|---|---|
| `ValueError: unsupported format character '''` at line 268 | Jinja `"%'d"` invalid | Pre-format with `fmt()` in `gigachat_service.generate_pdf()` |
| `⚠️ GigaChat не настроен` | `.env` not found / wrong path / CLIENT_ID used | Root `.env`; `GIGACHAT_AUTH_KEY`; `config.py` `env_file` both paths |
| `404 /api/v1/manager/analyze` | Router not included | `manager.py` created; mounted in `main.py` |
| PDF `500` / `weasyprint AttributeError: 'super'...transform` | Sandbox broken, real env OK | Code preserved; documented |
| White screen `/complex/2` | `useState` order wrong (`typedText` after `result`) | Fixed in `App.jsx` |
| Markdown table broken | Regex missing `filter(Boolean)` | Fixed in `App.jsx` `renderMarkdown()` |
| `indentationError` | Cleaned | All Python files |
| `NameError: svc_total` / `final_pdf` | Variables missing | Added to `generate_pdf()` |

**Not changed / not needed:** `GigaChat SDK` source (`gigachat` package), `.env` location (root), `floor_plan` DB column (`ALTER TABLE` not executed — model-sync disabled, no `OperationalError`).

---

## 7. Environment / start

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

**Env vars (root `.env` only):**
```
GIGACHAT_AUTH_KEY=<key>
GIGACHAT_MODEL=GigaChat-3-Ultra
GIGACHAT_TEMPERATURE=0.3
GIGACHAT_FALLBACK_ENABLED=True
```

---

## 8. What I do not do (constraints)

- Do **not** edit `gigachat` package (user instruction: “не трогай GigaChat”).
- Do **not** split into microservices (user: layered monolith).
- Do **not** change `.env` to backend/only; root is the contract.
- Do **not** run `ALTER TABLE` on `floor_plan`; keep model/DB sync disabled.
- Do **not** remove SVG plan in favor of table-only (layout A rejected; multi-row SVG restored).

---

Built by a single developer on one repo. No external orchestration. One `docker-compose.yml`. One `.env`. One `main.py`. PDF comes from HTML; AI comes from SDK + fallback; UI comes from React + Tailwind.
