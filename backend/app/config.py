"""WebSage AI — Application Configuration.

Loads settings from environment variables and backend/.env file.
Enforces limits approved in Requirements v1.2.
"""

from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    """Application configuration settings."""

    # Environment
    ENVIRONMENT: str = "development"

    # AI Provider Settings
    GROQ_API_KEY: str = Field(default="", description="Groq API key")
    GROQ_MODEL: str = Field(default="openai/gpt-oss-20b", description="Selected production Groq model")
    USE_MOCK_AI: bool = Field(default=True, description="Fallback to mock AI when no key is set or during testing")

    # Security & Resource Limits (from Requirements v1.2 Section 9)
    MAX_URL_LENGTH: int = 2048
    MAX_REDIRECTS: int = 3
    MAX_RESPONSE_BYTES: int = 2 * 1024 * 1024  # 2 MiB
    MAX_EXTRACTED_CHARS: int = 20000
    MIN_EXTRACTED_CHARS: int = 50  # Minimum readable text required for summarization
    FETCH_TIMEOUT_SECONDS: float = 10.0
    AI_TIMEOUT_SECONDS: float = 30.0

    # CORS Configuration
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
