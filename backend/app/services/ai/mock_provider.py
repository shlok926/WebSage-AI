"""WebSage AI — Mock AI Provider.

Provides deterministic responses for offline testing and local development,
strictly conforming to the 100-200 word summarization contract.
"""

from app.services.ai.base import (
    AISummarizer,
    AIRateLimitError,
    AITimeoutError,
    AIAuthenticationError,
)


class MockAISummarizer(AISummarizer):
    """Mock summarizer for offline testing and development without live API keys."""

    async def summarize(self, text: str) -> str:
        # Check for simulated test triggers
        if "__SIMULATE_RATE_LIMIT__" in text:
            raise AIRateLimitError("Mock: Provider rate limit exceeded.")
        if "__SIMULATE_TIMEOUT__" in text:
            raise AITimeoutError("Mock: AI provider timed out.")
        if "__SIMULATE_AUTH_ERROR__" in text:
            raise AIAuthenticationError("Mock: Invalid API credentials.")

        # Extract first few sentences or key phrases for contextual realism
        preview = text[:150].strip()

        return (
            f"WebSage AI Overview: This webpage discusses topics related to '{preview}...'. "
            "The document provides structured information covering key principles, contextual details, "
            "and primary observations. Key findings emphasize operational clarity, objective methodology, "
            "and systematic verification of core ideas without unnecessary complexity. Overall, the content "
            "delivers a concise and coherent informational perspective suitable for quick review and analytical "
            "comprehension."
        )
