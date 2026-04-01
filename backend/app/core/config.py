from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # APIs
    FMP_API_KEY: str = ""
    JQUANTS_EMAIL: str = ""
    JQUANTS_PASSWORD: str = ""

    # Database
    DATABASE_URL: str = "sqlite:///./stockanalyzer.db"
    REDIS_URL: str = "redis://localhost:6379"

    # App
    APP_ENV: str = "development"
    API_KEY: str = ""

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
