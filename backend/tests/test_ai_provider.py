"""Tests for AI provider abstraction, mock provider, Groq, Gemini, and error isolation."""

import asyncio
from unittest.mock import AsyncMock, MagicMock
import pytest

from app.services.ai.mock_provider import MockAISummarizer
from app.services.ai.groq_provider import GroqAISummarizer
from app.services.ai.gemini_provider import GeminiAISummarizer
from app.services.ai.base import (
    AIError,
    AIRateLimitError,
    AITimeoutError,
    AIAuthenticationError,
)
from google.genai import errors


# ---------------------------------------------------------------------------
# Mock AI Provider Tests
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Groq Provider Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_groq_provider_missing_key_safety():
    """Verify Groq provider fails safely without key and does not leak secrets."""
    groq = GroqAISummarizer(api_key="")
    with pytest.raises(AIAuthenticationError) as exc:
        await groq.summarize("Some extracted text")
    assert "not configured" in exc.value.message


# ---------------------------------------------------------------------------
# Gemini Provider Tests
# ---------------------------------------------------------------------------

def test_gemini_provider_initialization():
    """Verify Gemini provider initializes with explicit or default settings."""
    gemini = GeminiAISummarizer(api_key="test_key", model="gemini-2.5-flash")
    assert gemini.api_key == "test_key"
    assert gemini.model == "gemini-2.5-flash"


@pytest.mark.asyncio
async def test_gemini_provider_missing_key():
    """Verify Gemini provider fails safely when API key is empty or placeholder."""
    for placeholder in ("", "replace_with_your_gemini_api_key", "   "):
        gemini = GeminiAISummarizer(api_key=placeholder)
        with pytest.raises(AIAuthenticationError) as exc:
            await gemini.summarize("Some extracted webpage text")
        assert "not configured" in exc.value.message


@pytest.mark.asyncio
async def test_gemini_provider_success_mocked_client():
    """Verify successful summarization using mocked google-genai client."""
    mock_response = MagicMock()
    mock_response.text = "This is a concise, factual summary of the article produced by Gemini."

    mock_client = MagicMock()
    mock_client.aio.models.generate_content = AsyncMock(return_value=mock_response)

    gemini = GeminiAISummarizer(api_key="valid_test_key", client=mock_client)
    result = await gemini.summarize("Valid public article text for summarization.")

    assert result == "This is a concise, factual summary of the article produced by Gemini."
    mock_client.aio.models.generate_content.assert_awaited_once()


@pytest.mark.asyncio
async def test_gemini_provider_empty_or_malformed_response():
    """Verify handling of empty or structurally malformed responses from Gemini."""
    # 1. Malformed response (no text attribute)
    mock_malformed = MagicMock(spec=[])
    mock_client = MagicMock()
    mock_client.aio.models.generate_content = AsyncMock(return_value=mock_malformed)

    gemini = GeminiAISummarizer(api_key="valid_test_key", client=mock_client)
    with pytest.raises(AIError) as exc:
        await gemini.summarize("Sample text")
    assert exc.value.code == "AI_MALFORMED_RESPONSE"

    # 2. Empty response text
    mock_empty = MagicMock()
    mock_empty.text = "   "
    mock_client.aio.models.generate_content = AsyncMock(return_value=mock_empty)

    with pytest.raises(AIError) as exc_empty:
        await gemini.summarize("Sample text")
    assert exc_empty.value.code == "AI_EMPTY_RESPONSE"


@pytest.mark.asyncio
async def test_gemini_provider_authentication_error():
    """Verify HTTP 401/403 APIError is mapped to AIAuthenticationError without leaking keys."""
    secret_key = "AIzaSyFakeSecretKeyValueToRedact"
    mock_client = MagicMock()
    api_error = errors.APIError(401, {"error": {"message": f"Invalid API key: {secret_key}"}})
    mock_client.aio.models.generate_content = AsyncMock(side_effect=api_error)

    gemini = GeminiAISummarizer(api_key=secret_key, client=mock_client)
    with pytest.raises(AIAuthenticationError) as exc:
        await gemini.summarize("Sample article text")

    assert exc.value.status_code == 502
    assert exc.value.code == "AI_AUTH_ERROR"
    assert secret_key not in exc.value.message


@pytest.mark.asyncio
async def test_gemini_provider_rate_limit_error():
    """Verify HTTP 429 APIError is mapped to AIRateLimitError."""
    mock_client = MagicMock()
    api_error = errors.APIError(429, {"error": {"message": "Quota exceeded / Resource exhausted"}})
    mock_client.aio.models.generate_content = AsyncMock(side_effect=api_error)

    gemini = GeminiAISummarizer(api_key="valid_key", client=mock_client)
    with pytest.raises(AIRateLimitError) as exc:
        await gemini.summarize("Sample article text")

    assert exc.value.status_code == 429
    assert exc.value.code == "RATE_LIMIT_EXCEEDED"


@pytest.mark.asyncio
async def test_gemini_provider_timeout_handling(monkeypatch):
    """Verify AI timeout raises AITimeoutError."""
    from app.config import settings

    async def slow_generate(*args, **kwargs):
        await asyncio.sleep(0.05)
        return MagicMock(text="Finished")

    mock_client = MagicMock()
    mock_client.aio.models.generate_content = AsyncMock(side_effect=slow_generate)

    monkeypatch.setattr(settings, "AI_TIMEOUT_SECONDS", 0.01)

    gemini = GeminiAISummarizer(api_key="valid_key", client=mock_client)
    with pytest.raises(AITimeoutError) as exc:
        await gemini.summarize("Sample article text")

    assert exc.value.status_code == 504
    assert exc.value.code == "AI_TIMEOUT"


@pytest.mark.asyncio
async def test_gemini_provider_secret_redaction_on_unexpected_error():
    """Verify unexpected connection exceptions never expose API credentials."""
    secret_key = "AIzaSySecretNeverToExpose"
    mock_client = MagicMock()
    mock_client.aio.models.generate_content = AsyncMock(
        side_effect=RuntimeError(f"Connection failure involving {secret_key}")
    )

    gemini = GeminiAISummarizer(api_key=secret_key, client=mock_client)
    with pytest.raises(AIError) as exc:
        await gemini.summarize("Sample article text")

    assert exc.value.code == "AI_CONNECTION_ERROR"
    assert secret_key not in exc.value.message


# ---------------------------------------------------------------------------
# Factory & Provider Selection Tests
# ---------------------------------------------------------------------------

def test_factory_production_rejects_mock(monkeypatch):
    """Verify get_ai_summarizer never returns MockAISummarizer in production."""
    from app.services.ai.factory import get_ai_summarizer
    from app.config import settings

    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    monkeypatch.setattr(settings, "USE_MOCK_AI", True)

    # With default Groq
    monkeypatch.setattr(settings, "AI_PROVIDER", "groq")
    provider_groq = get_ai_summarizer()
    assert isinstance(provider_groq, GroqAISummarizer)

    # With Gemini
    monkeypatch.setattr(settings, "AI_PROVIDER", "gemini")
    provider_gemini = get_ai_summarizer()
    assert isinstance(provider_gemini, GeminiAISummarizer)
    assert not isinstance(provider_gemini, MockAISummarizer)


def test_factory_disabled_mock_uses_configured_provider(monkeypatch):
    """Verify get_ai_summarizer selects appropriate real provider when USE_MOCK_AI is False."""
    from app.services.ai.factory import get_ai_summarizer
    from app.config import settings

    monkeypatch.setattr(settings, "ENVIRONMENT", "development")
    monkeypatch.setattr(settings, "USE_MOCK_AI", False)

    # Groq selection
    monkeypatch.setattr(settings, "AI_PROVIDER", "groq")
    provider = get_ai_summarizer()
    assert isinstance(provider, GroqAISummarizer)

    # Gemini selection
    monkeypatch.setattr(settings, "AI_PROVIDER", "gemini")
    provider_gemini = get_ai_summarizer()
    assert isinstance(provider_gemini, GeminiAISummarizer)


def test_factory_invalid_provider_raises_error(monkeypatch):
    """Verify invalid AI_PROVIDER setting raises a sanitized configuration error."""
    from app.services.ai.factory import get_ai_summarizer
    from app.config import settings

    monkeypatch.setattr(settings, "ENVIRONMENT", "development")
    monkeypatch.setattr(settings, "USE_MOCK_AI", False)
    monkeypatch.setattr(settings, "AI_PROVIDER", "unsupported_provider")

    with pytest.raises(AIError) as exc:
        get_ai_summarizer()
    assert exc.value.code == "CONFIG_ERROR"
    assert "Unsupported AI_PROVIDER" in exc.value.message
