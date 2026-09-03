from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Конфигурация приложения"""

    # App
    APP_NAME: str = "DSK AI Sales"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = "sqlite:///./dsk_sales.db"

    # GigaChat API
    # Получить можно в личном кабинете GigaChat: https://developers.sber.ru/
    GIGACHAT_CLIENT_ID: str = ""           # Client ID из личного кабинета
    GIGACHAT_CLIENT_SECRET: str = ""       # Client Secret из личного кабинета
    GIGACHAT_AUTH_KEY: str = ""            # Или сразу Authorization Key (Base64)
    GIGACHAT_MODEL: str = "GigaChat"
    GIGACHAT_TEMPERATURE: float = 0.3      # Низкая температура — строгий деловой стиль
    GIGACHAT_MAX_TOKENS: int = 2048
    GIGACHAT_TIMEOUT: int = 30

    # Fallback: если GigaChat недоступен, использовать локальный шаблон
    GIGACHAT_FALLBACK_ENABLED: bool = True

    # Business logic
    DEFAULT_CASH_DISCOUNT: float = 5.0
    DEFAULT_CASH_DISCOUNT_MAX: float = 500_000
    RISK_DELAY_THRESHOLD_DAYS: int = 30
    KP_VALID_DAYS: int = 3

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
