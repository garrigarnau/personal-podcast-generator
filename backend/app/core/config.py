from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    DATABASE_URL: str
    SQL_ECHO: bool = False

    # API Keys
    OPENAI_API_KEY: str
    ELEVENLABS_API_KEY: str
    FIRECRAWL_API_KEY: str
    NEWS_API_KEY: Optional[str] = None

    # Application Settings
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # JWT Settings
    SECRET_KEY: str = "your-secret-key-change-this-in-production-use-openssl-rand-hex-32"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080  # 7 days

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Allow extra fields in .env without errors


settings = Settings()
