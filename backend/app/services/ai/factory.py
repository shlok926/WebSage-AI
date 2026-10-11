"""WebSage AI — AI Provider Factory.

Selects the appropriate provider instance according to configuration.
Supports Groq (default) and Gemini providers, with strict production guardrails.
"""

from app.config import settings
from app.services.ai.base import AISummarizer, AIError
from app.services.ai.mock_provider import MockAISummarizer
from app.services.ai.groq_provider import GroqAISummarizer
from app.services.ai.gemini_provider import GeminiAISummarizer


def get_ai_summarizer() -> AISummarizer:
    """Instantiate and return the configured AI summarizer.

    In production mode, mock AI responses are strictly prohibited.
    Returns GroqAISummarizer (default) or GeminiAISummarizer based on AI_PROVIDER.
    If credentials are missing or invalid, the provider raises AIAuthenticationError
    without leaking secrets.
    """
    provider_name = (settings.AI_PROVIDER or "groq").lower().strip()

    if settings.ENVIRONMENT.lower() == "production":
        if provider_name == "gemini":
            return GeminiAISummarizer()
        elif provider_name == "groq":
            return GroqAISummarizer()
        else:
            raise AIError(
                "CONFIG_ERROR",
                f"Unsupported AI_PROVIDER '{settings.AI_PROVIDER}'. Choose 'groq' or 'gemini'.",
                502,
            )

    if settings.USE_MOCK_AI:
        return MockAISummarizer()

    if provider_name == "gemini":
        return GeminiAISummarizer()
    elif provider_name == "groq":
        return GroqAISummarizer()
    else:
        raise AIError(
            "CONFIG_ERROR",
            f"Unsupported AI_PROVIDER '{settings.AI_PROVIDER}'. Choose 'groq' or 'gemini'.",
            502,
        )
