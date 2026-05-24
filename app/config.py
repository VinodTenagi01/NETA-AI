"""
Central configuration loaded from environment variables.
All secrets are injected at runtime — never hardcoded here.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://netaai_app:netaai_password@localhost:5432/netaai_prod"
    DATABASE_URL_SYNC: str = "postgresql://netaai_app:netaai_password@localhost:5432/netaai_prod"

    # Redis
    REDIS_URL: str = "redis://:redis_password@localhost:6379/0"

    # JWT
    SECRET_KEY: str = "change-me-in-production-use-openssl-rand-hex-32"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # App
    PROJECT_NAME: str = "NETA AI — Political Campaign Intelligence Platform"
    ALLOWED_ORIGINS: list[str] = ["http://localhost:5173", "https://app.netaai.in"]
    DEBUG: bool = False

    # NLP
    NLP_MODEL_PATH: str = "/models/indic-bert-political"

    # WhatsApp
    WHATSAPP_API_TOKEN: str = ""
    WHATSAPP_PHONE_ID: str = ""

    # Constituency constants (Serilingampally AC-52)
    CONSTITUENCY_AC_NUMBER: str = "52"
    CONSTITUENCY_NAME: str = "Serilingampally"
    CONSTITUENCY_STATE: str = "Telangana"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
