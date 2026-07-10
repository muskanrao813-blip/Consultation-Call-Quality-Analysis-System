from pydantic_settings import BaseSettings
from functools import lru_cache
from pathlib import Path
import os

# Load .env file explicitly
from dotenv import load_dotenv
load_dotenv()


class Settings(BaseSettings):
    database_url: str = "sqlite:///./test.db"
    redis_url: str = "redis://localhost:6379/0"
    google_application_credentials: str = ""
    gcs_bucket_name: str = "dietician-qa-audio"
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    llm_provider: str = "gemini"
    transcription_provider: str = "google_stt"
    celery_concurrency: int = 10
    environment: str = "development"

    class Config:
        case_sensitive = False


@lru_cache()
def get_settings():
    return Settings()
