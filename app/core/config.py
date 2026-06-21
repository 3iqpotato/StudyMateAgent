from pydantic_settings import BaseSettings
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent.parent


class Settings(BaseSettings):
    APP_NAME: str = "AI Test Helper"
    DEBUG: bool = False

    # Postgres поотделно
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_HOST: str = "postgres"
    POSTGRES_PORT: int = 5433

    # Сглобена URL
    DATABASE_URL: str
    DATABASE_URL_LOCAL: str = ""

    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    OLLAMA_BASE_URL: str
    OLLAMA_MODEL: str = "qwen3.5:9b"

    MAX_CONVERSATIONS_PER_USER: int = 3

    CHROMA_HOST: str = "localhost"
    CHROMA_PORT: int = 8001

    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_CHAT_ID: str = ""

    class Config:
        env_file = str(ROOT_DIR / ".env")
        extra = "ignore"  # игнорира непознати променливи


settings = Settings()