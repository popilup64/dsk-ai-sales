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

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
API доступно по адресу: http://localhost:8000
Документация: http://localhost:8000/docs

### Frontend
```bash
cd frontend
npm install
npm run dev
```
Приложение доступно по адресу: http://localhost:5173

## Команда
- [Имя] — Backend / AI
- [Имя] — Frontend / UX
- [Имя] — Product / Analytics
