"""WebSage AI — Application Configuration.

Loads settings from environment variables and backend/.env file.
Enforces limits approved in Requirements v1.2.
"""

from typing import List, Union
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator


class Settings(BaseSettings):
    """Application configuration settings."""

    # Environment
    ENVIRONMENT: str = "development"

    # AI Provider Settings
    AI_PROVIDER: str = Field(default="groq", description="Selected AI provider: 'groq' or 'gemini'")
    GROQ_API_KEY: str = Field(default="", description="Groq API key")
    GROQ_MODEL: str = Field(default="openai/gpt-oss-20b", description="Selected production Groq model")
    GEMINI_API_KEY: str = Field(default="", description="Google Gemini API key")
    GEMINI_MODEL: str = Field(default="gemini-flash-latest", description="Selected Gemini model")
    USE_MOCK_AI: bool = Field(default=False, description="Fallback to mock AI when no key is set or during testing")

    # Security & Resource Limits (from Requirements v1.2 Section 9)
    MAX_URL_LENGTH: int = 2048
    MAX_REDIRECTS: int = 3
    MAX_RESPONSE_BYTES: int = 2 * 1024 * 1024  # 2 MiB
    MAX_EXTRACTED_CHARS: int = 20000
    MIN_EXTRACTED_CHARS: int = 50  # Minimum readable text required for summarization
    FETCH_TIMEOUT_SECONDS: float = 10.0
    AI_TIMEOUT_SECONDS: float = 30.0

    # Rate Limiting Configuration
    RATE_LIMIT_SUMMARIZE: str = Field(
        default="10/minute",
        description="Per-client rate limit for /api/summarize endpoint (e.g. '10/minute')"
    )
    TRUST_PROXY_HEADERS: bool = Field(
        default=False,
        description="Whether to trust X-Forwarded-For headers from verified reverse proxies"
    )

    # CORS Configuration
    CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ]

    @field_validator("CORS_ORIGINS", mode="after")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            if v.startswith("["):
                import json
                return json.loads(v)
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    @field_validator("RATE_LIMIT_SUMMARIZE", mode="after")
    @classmethod
    def validate_rate_limit(cls, v: str) -> str:
        try:
            from limits import parse
            parse(v)
            return v
        except Exception:
            raise ValueError(f"Invalid rate limit string: '{v}'. Expected format like '10/minute' or '100/hour'.")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
