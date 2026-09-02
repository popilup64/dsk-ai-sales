"""
DSK AI Sales — Backend API
Монолитная архитектура на FastAPI
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from api.v1 import complexes, apartments, kp, risks, services
settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-помощник для отдела продаж ГК «ДСК»",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS — чтобы фронтенд мог обращаться к бэку
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


@app.get("/health", tags=["System"])
async def health_check():
    """Проверка работоспособности API"""
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
