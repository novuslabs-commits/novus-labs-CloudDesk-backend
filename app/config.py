from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    database_url: str
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 480
    model_path: str = "../model/saved_model_3"
    confidence_threshold: float = 0.70
    gemini_api_key: str = ""
    use_gemini_classifier: bool = False
    cors_origins: str = "http://localhost:3000"  # add this # local dev default: False (use DistilBERT)
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

@lru_cache
def get_settings() -> Settings:
    return Settings()