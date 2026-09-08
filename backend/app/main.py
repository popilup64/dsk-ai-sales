"""
DSK AI Sales — Backend API
Монолитная архитектура на FastAPI
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.config import get_settings
from backend.api.v1 import complexes, apartments, kp, risks, services, manager
from backend.db.init_db import init_database

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-помощник для отдела продаж ГК «ДСК»",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем роутеры
app.include_router(complexes.router, prefix="/api/v1", tags=["Комплексы"])
app.include_router(apartments.router, prefix="/api/v1", tags=["Квартиры"])
app.include_router(kp.router, prefix="/api/v1", tags=["КП"])
app.include_router(risks.router, prefix="/api/v1", tags=["Риски"])
app.include_router(services.router, prefix="/api/v1", tags=["Услуги"])
app.include_router(manager.router, prefix="/api/v1", tags=["Менеджер / Конкуренты"])


@app.on_event("startup")
async def startup_event():
    """Инициализация БД при старте"""
    init_database()


@app.get("/health", tags=["System"])
async def health_check():
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "debug": settings.DEBUG,
    }


@app.get("/", tags=["System"])
async def root():
    return {
        "message": "DSK AI Sales API",
        "docs": "/docs",
        "health": "/health",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
