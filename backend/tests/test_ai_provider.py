"""Tests for AI provider abstraction, mock provider, and error isolation."""

import pytest
from app.services.ai.mock_provider import MockAISummarizer
from app.services.ai.groq_provider import GroqAISummarizer
from app.services.ai.base import (
    AIRateLimitError,
    AITimeoutError,
    AIAuthenticationError,
)


@pytest.mark.asyncio
async def test_mock_summarizer_standard_output():
    """Verify mock summarizer generates a valid, bounded summary."""
    summarizer = MockAISummarizer()
    sample_text = (
        "WebSage AI is a lightweight demonstration application designed to fetch public web pages "
        "and produce concise summaries. The project emphasizes secure development practices, "
        "including strict SSRF mitigation, bounded memory usage, and zero required financial cost."
    )
    summary = await summarizer.summarize(sample_text)

    assert isinstance(summary, str)
    assert len(summary) > 50
    words = summary.split()
    assert 30 <= len(words) <= 250  # Conforms to ~100-200 words expectation


@pytest.mark.asyncio
async def test_mock_summarizer_simulated_errors():
    """Verify mock summarizer raises categorized errors upon trigger phrases."""
    summarizer = MockAISummarizer()

    with pytest.raises(AIRateLimitError) as exc_429:
        await summarizer.summarize("Content with __SIMULATE_RATE_LIMIT__ trigger.")
    assert exc_429.value.status_code == 429
    assert exc_429.value.code == "RATE_LIMIT_EXCEEDED"

    with pytest.raises(AITimeoutError) as exc_504:
        await summarizer.summarize("Content with __SIMULATE_TIMEOUT__ trigger.")
    assert exc_504.value.status_code == 504
    assert exc_504.value.code == "AI_TIMEOUT"

    with pytest.raises(AIAuthenticationError) as exc_auth:
        await summarizer.summarize("Content with __SIMULATE_AUTH_ERROR__ trigger.")
    assert exc_auth.value.status_code == 502
    assert exc_auth.value.code == "AI_AUTH_ERROR"


@pytest.mark.asyncio
async def test_groq_provider_missing_key_safety():
    """Verify Groq provider fails safely without key and does not leak secrets."""
    groq = GroqAISummarizer(api_key="")
    with pytest.raises(AIAuthenticationError) as exc:
        await groq.summarize("Some extracted text")
    assert "not configured" in exc.value.message


def test_factory_production_rejects_mock(monkeypatch):
    """Verify get_ai_summarizer never returns MockAISummarizer in production."""
    from app.services.ai.factory import get_ai_summarizer
    from app.config import settings

    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    monkeypatch.setattr(settings, "USE_MOCK_AI", True)

    provider = get_ai_summarizer()
    assert isinstance(provider, GroqAISummarizer)
    assert not isinstance(provider, MockAISummarizer)


def test_factory_disabled_mock_uses_groq(monkeypatch):
    """Verify get_ai_summarizer uses Groq when USE_MOCK_AI is False."""
    from app.services.ai.factory import get_ai_summarizer
    from app.config import settings

    monkeypatch.setattr(settings, "ENVIRONMENT", "development")
    monkeypatch.setattr(settings, "USE_MOCK_AI", False)

    provider = get_ai_summarizer()
    assert isinstance(provider, GroqAISummarizer)
    assert not isinstance(provider, MockAISummarizer)

