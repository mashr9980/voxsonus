# app/core/config.py
import os
from pydantic_settings import BaseSettings
from pydantic import Extra
from typing import List

class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Subtitles Platform"
    API_V1_STR: str = "/api"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24

    POSTGRES_USER: str = os.getenv("DB_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("DB_PASSWORD", "123")
    POSTGRES_SERVER: str = os.getenv("DB_HOST", "localhost")
    POSTGRES_PORT: str = os.getenv("DB_PORT", "5432")
    POSTGRES_DB: str = os.getenv("DB_NAME", "ai_subtitles")
    DATABASE_URL: str = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_SERVER}:{POSTGRES_PORT}/{POSTGRES_DB}"
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8080"]
    
    # Frontend URL for payment redirects
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "")

    STRIPE_API_KEY: str = os.getenv("STRIPE_API_KEY", "")
    STRIPE_WEBHOOK_SECRET: str = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    
    ASSEMBLY_AI_API_KEY: str = os.getenv("ASSEMBLY_AI_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "uploads")
    OUTPUT_DIR: str = os.getenv("OUTPUT_DIR", "outputs")
    
    MAX_FILE_SIZE: int = 1024 * 1024 * 1024  # 1GB
    PRICE_PER_MINUTE: float = 1.0

    # IONOS object storage configuration
    IONOS_ENDPOINT_URL: str = os.getenv("IONOS_ENDPOINT_URL", "")
    IONOS_ACCESS_KEY_ID: str = os.getenv("IONOS_ACCESS_KEY_ID", "")
    IONOS_SECRET_ACCESS_KEY: str = os.getenv("IONOS_SECRET_ACCESS_KEY", "")
    IONOS_BUCKET_NAME: str = os.getenv("IONOS_BUCKET_NAME", "")

    USE_OBJECT_STORAGE: bool = os.getenv("USE_OBJECT_STORAGE", "false").lower() == "true"

    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", "")
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra=Extra.ignore

settings = Settings()