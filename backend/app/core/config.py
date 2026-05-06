from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    DATABASE_URL: str
    SQL_ECHO: bool = False

    # API Keys
    OPENAI_API_KEY: str
    ELEVENLABS_API_KEY: str

    # Firecrawl Configuration (for web scraping)
    FIRECRAWL_API_KEY: str

    # News API Configuration (for article discovery)
    NEWS_API_KEY: str = Field(..., env="NEWS_API_KEY")
    """API key for News API service used for discovering news articles."""

    NEWS_API_BASE_URL: str = Field(default="https://newsapi.org/v2", env="NEWS_API_BASE_URL")
    """Base URL for News API endpoints."""

    # LangSmith Configuration
    LANGSMITH_TRACING: bool = True
    LANGSMITH_ENDPOINT: str = "https://api.smith.langchain.com"
    LANGSMITH_API_KEY: Optional[str] = None
    LANGSMITH_PROJECT: str = "personal-podcast"

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
