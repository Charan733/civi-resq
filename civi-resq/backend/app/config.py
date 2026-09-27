"""
CIVI-RESQ Backend Configuration
All secrets/config pulled from environment variables (.env). Never hardcode secrets.
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # --- App ---
    APP_NAME: str = "CIVI-RESQ"
    ENV: str = "development"
    DEBUG: bool = True

    # --- Database ---
    DATABASE_URL: str = "postgresql://civiresq:civiresq_pass@localhost:5432/civiresq_db"

    # --- Auth ---
    SECRET_KEY: str = "CHANGE_THIS_IN_PRODUCTION_use_openssl_rand_hex_32"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 8  # 8 hours

    # --- CORS ---
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    # --- ML ---
    MODEL_DIR: str = "ml/trained_models"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    return Settings()
