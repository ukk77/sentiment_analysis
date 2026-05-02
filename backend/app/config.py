from pydantic_settings import BaseSettings
from functools import lru_cache
import os

# Get the backend directory path
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(BACKEND_DIR, ".env")


class Settings(BaseSettings):
    NEWS_API_KEY: str
    FINNHUB_API_KEY: str
    HF_TOKEN: str = ""  # Optional, for Hugging Face authenticated requests
    
    class Config:
        env_file = ENV_PATH


@lru_cache()
def get_settings() -> Settings:
    return Settings()
