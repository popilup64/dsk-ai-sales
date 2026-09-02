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

    # GigaChat
    GIGACHAT_API_KEY: str = ""
    GIGACHAT_MODEL: str = "GigaChat"

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
