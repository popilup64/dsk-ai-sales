from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
import os


class Settings(BaseSettings):
    """Конфигурация приложения"""

    APP_NAME: str = "DSK AI Sales"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    DATABASE_URL: str = "sqlite:///./dsk_sales.db"

    GIGACHAT_CLIENT_ID: str = ""
    GIGACHAT_CLIENT_SECRET: str = ""
    GIGACHAT_AUTH_KEY: str = ""
    GIGACHAT_MODEL: str = "GigaChat"
    GIGACHAT_TEMPERATURE: float = 0.3
    GIGACHAT_MAX_TOKENS: int = 2048
    GIGACHAT_TIMEOUT: int = 30
    GIGACHAT_FALLBACK_ENABLED: bool = True

    DEFAULT_CASH_DISCOUNT: float = 5.0
    DEFAULT_CASH_DISCOUNT_MAX: float = 500_000
    RISK_DELAY_THRESHOLD_DAYS: int = 30
    KP_VALID_DAYS: int = 3

    # Подхватываем .env: сначала из backend/, затем из корня — независимо от CWD
    _here = os.path.dirname(__file__)
    _candidates = [
        os.path.join(_here, "..", ".env"),
        os.path.join(_here, "..", "..", ".env"),
    ]
    _env_files = tuple(p for p in _candidates if os.path.exists(p))

    model_config = SettingsConfigDict(
        env_file=_env_files if _env_files else ".env",
        extra="ignore"
    )


@lru_cache()
def get_settings() -> Settings:
    return Settings()