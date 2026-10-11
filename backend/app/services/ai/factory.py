"""WebSage AI — AI Provider Factory.

Selects the appropriate provider instance according to configuration.
"""

from app.config import settings
from app.services.ai.base import AISummarizer
from app.services.ai.mock_provider import MockAISummarizer
from app.services.ai.groq_provider import GroqAISummarizer


def get_ai_summarizer() -> AISummarizer:
    """Instantiate and return the configured AI summarizer.

    In production mode, mock AI responses are strictly prohibited.
    If the key is missing in production or when mock AI is disabled,
    GroqAISummarizer is returned, which properly raises AIAuthenticationError
    without leaking secrets.
    """
    if settings.ENVIRONMENT.lower() == "production":
        return GroqAISummarizer()

    if settings.USE_MOCK_AI:
        return MockAISummarizer()

    return GroqAISummarizer()
