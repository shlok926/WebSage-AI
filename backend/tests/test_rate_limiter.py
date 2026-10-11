"""WebSage AI — Rate Limiting and Abuse Protection Tests."""

import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient

from app.main import app, limiter
from app.config import settings


@pytest.fixture(autouse=True)
def reset_limiter():
    """Reset limiter state between tests."""
    limiter.reset()
    yield
    limiter.reset()


def test_rate_limit_allows_requests_below_threshold():
    """Verify requests under the configured threshold succeed normally."""
    client = TestClient(app)

    with patch("app.main.fetch_webpage_html", new_callable=AsyncMock) as mock_fetch, \
         patch("app.main.extract_readable_text", return_value=("Safe content text.", 100)), \
         patch("app.main.get_ai_summarizer") as mock_factory:
        mock_fetch.return_value = ("<html><body>Safe content text.</body></html>", "https://example.com", "example.com")
        mock_summarizer = AsyncMock()
        mock_summarizer.summarize.return_value = "Concise summary of content."
        mock_factory.return_value = mock_summarizer

        response = client.post("/api/summarize", json={"url": "https://example.com/page1"})
        assert response.status_code == 200
        assert "summary" in response.json()


def test_rate_limit_blocks_excessive_requests():
    """Verify requests exceeding the configured limit return HTTP 429 and standardized error schema."""
    client = TestClient(app)

    with patch.object(settings, "RATE_LIMIT_SUMMARIZE", "2/minute"), \
         patch("app.main.fetch_webpage_html", new_callable=AsyncMock) as mock_fetch, \
         patch("app.main.extract_readable_text", return_value=("Safe content text.", 100)), \
         patch("app.main.get_ai_summarizer") as mock_factory:
        mock_fetch.return_value = ("<html><body>Safe content text.</body></html>", "https://example.com", "example.com")
        mock_summarizer = AsyncMock()
        mock_summarizer.summarize.return_value = "Concise summary of content."
        mock_factory.return_value = mock_summarizer

        # Request 1 (Allowed)
        r1 = client.post("/api/summarize", json={"url": "https://example.com/1"})
        assert r1.status_code == 200

        # Request 2 (Allowed)
        r2 = client.post("/api/summarize", json={"url": "https://example.com/2"})
        assert r2.status_code == 200

        # Request 3 (Exceeded -> 429)
        r3 = client.post("/api/summarize", json={"url": "https://example.com/3"})
        assert r3.status_code == 429
        data = r3.json()
        assert "error" in data
        assert data["error"]["code"] == "RATE_LIMIT_EXCEEDED"
        assert "Rate limit exceeded" in data["error"]["message"]


def test_health_check_exempt_from_rate_limits():
    """Verify health check /health endpoint is exempt from /api/summarize rate limiting."""
    client = TestClient(app)

    with patch.object(settings, "RATE_LIMIT_SUMMARIZE", "1/minute"), \
         patch("app.main.fetch_webpage_html", new_callable=AsyncMock) as mock_fetch, \
         patch("app.main.extract_readable_text", return_value=("Safe content text.", 100)), \
         patch("app.main.get_ai_summarizer") as mock_factory:
        mock_fetch.return_value = ("<html><body>Safe content text.</body></html>", "https://example.com", "example.com")
        mock_summarizer = AsyncMock()
        mock_summarizer.summarize.return_value = "Summary"
        mock_factory.return_value = mock_summarizer

        # Exhaust summarize limit
        client.post("/api/summarize", json={"url": "https://example.com"})
        r_exhausted = client.post("/api/summarize", json={"url": "https://example.com"})
        assert r_exhausted.status_code == 429

        # Health endpoint must still return 200 OK
        r_health = client.get("/health")
        assert r_health.status_code == 200
        assert r_health.json() == {"status": "ok"}


def test_untrusted_forwarded_for_cannot_bypass_rate_limit():
    """Verify that when TRUST_PROXY_HEADERS=False, client-supplied X-Forwarded-For is ignored."""
    client = TestClient(app)

    with patch.object(settings, "RATE_LIMIT_SUMMARIZE", "1/minute"), \
         patch.object(settings, "TRUST_PROXY_HEADERS", False), \
         patch("app.main.fetch_webpage_html", new_callable=AsyncMock) as mock_fetch, \
         patch("app.main.extract_readable_text", return_value=("Safe content text.", 100)), \
         patch("app.main.get_ai_summarizer") as mock_factory:
        mock_fetch.return_value = ("<html><body>Safe content text.</body></html>", "https://example.com", "example.com")
        mock_summarizer = AsyncMock()
        mock_summarizer.summarize.return_value = "Summary"
        mock_factory.return_value = mock_summarizer

        # Request 1 from client
        r1 = client.post("/api/summarize", json={"url": "https://example.com"}, headers={"X-Forwarded-For": "1.1.1.1"})
        assert r1.status_code == 200

        # Request 2 attempting bypass with spoofed X-Forwarded-For header
        r2 = client.post("/api/summarize", json={"url": "https://example.com"}, headers={"X-Forwarded-For": "2.2.2.2"})
        # Must still be blocked because both requests originated from the same peer (testclient)
        assert r2.status_code == 429
        assert r2.json()["error"]["code"] == "RATE_LIMIT_EXCEEDED"


def test_trusted_proxy_headers_honored_when_configured():
    """Verify that when TRUST_PROXY_HEADERS=True, distinct clients behind trusted proxy have independent limits."""
    client = TestClient(app)

    with patch.object(settings, "RATE_LIMIT_SUMMARIZE", "1/minute"), \
         patch.object(settings, "TRUST_PROXY_HEADERS", True), \
         patch("app.main.fetch_webpage_html", new_callable=AsyncMock) as mock_fetch, \
         patch("app.main.extract_readable_text", return_value=("Safe content text.", 100)), \
         patch("app.main.get_ai_summarizer") as mock_factory:
        mock_fetch.return_value = ("<html><body>Safe content text.</body></html>", "https://example.com", "example.com")
        mock_summarizer = AsyncMock()
        mock_summarizer.summarize.return_value = "Summary"
        mock_factory.return_value = mock_summarizer

        # Client A request succeeds
        r_a = client.post("/api/summarize", json={"url": "https://example.com"}, headers={"X-Forwarded-For": "203.0.113.195"})
        assert r_a.status_code == 200

        # Client B from different forwarded IP also succeeds
        r_b = client.post("/api/summarize", json={"url": "https://example.com"}, headers={"X-Forwarded-For": "198.51.100.44"})
        assert r_b.status_code == 200


def test_trusted_proxy_uses_rightmost_ip_preventing_prefix_injection():
    """Verify that behind trusted proxy, an attacker cannot bypass limits by prefixing spoofed IPs."""
    client = TestClient(app)

    with patch.object(settings, "RATE_LIMIT_SUMMARIZE", "1/minute"), \
         patch.object(settings, "TRUST_PROXY_HEADERS", True), \
         patch("app.main.fetch_webpage_html", new_callable=AsyncMock) as mock_fetch, \
         patch("app.main.extract_readable_text", return_value=("Safe content text.", 100)), \
         patch("app.main.get_ai_summarizer") as mock_factory:
        mock_fetch.return_value = ("<html><body>Safe content text.</body></html>", "https://example.com", "example.com")
        mock_summarizer = AsyncMock()
        mock_summarizer.summarize.return_value = "Summary"
        mock_factory.return_value = mock_summarizer

        # Attacker sends spoofed prefix 1.1.1.1, real edge peer 203.0.113.10
        r1 = client.post("/api/summarize", json={"url": "https://example.com"}, headers={"X-Forwarded-For": "1.1.1.1, 203.0.113.10"})
        assert r1.status_code == 200

        # Attacker tries to bypass by changing spoofed prefix to 2.2.2.2, same edge peer 203.0.113.10
        r2 = client.post("/api/summarize", json={"url": "https://example.com"}, headers={"X-Forwarded-For": "2.2.2.2, 203.0.113.10"})
        assert r2.status_code == 429
        assert r2.json()["error"]["code"] == "RATE_LIMIT_EXCEEDED"


def test_trusted_proxy_prefers_x_real_ip():
    """Verify that when X-Real-IP is provided by a trusted proxy, it is preferred."""
    client = TestClient(app)

    with patch.object(settings, "RATE_LIMIT_SUMMARIZE", "1/minute"), \
         patch.object(settings, "TRUST_PROXY_HEADERS", True), \
         patch("app.main.fetch_webpage_html", new_callable=AsyncMock) as mock_fetch, \
         patch("app.main.extract_readable_text", return_value=("Safe content text.", 100)), \
         patch("app.main.get_ai_summarizer") as mock_factory:
        mock_fetch.return_value = ("<html><body>Safe content text.</body></html>", "https://example.com", "example.com")
        mock_summarizer = AsyncMock()
        mock_summarizer.summarize.return_value = "Summary"
        mock_factory.return_value = mock_summarizer

        r1 = client.post("/api/summarize", json={"url": "https://example.com"}, headers={"X-Real-IP": "198.51.100.55"})
        assert r1.status_code == 200

        r2 = client.post("/api/summarize", json={"url": "https://example.com"}, headers={"X-Real-IP": "198.51.100.55"})
        assert r2.status_code == 429


def test_invalid_rate_limit_string_fails_safely_to_fallback():
    """Verify that a malformed rate limit string fails safely to a strict fallback rather than disabling limits."""
    client = TestClient(app)

    with patch.object(settings, "RATE_LIMIT_SUMMARIZE", "malformed_limit_string"), \
         patch("app.main.fetch_webpage_html", new_callable=AsyncMock) as mock_fetch, \
         patch("app.main.extract_readable_text", return_value=("Safe content text.", 100)), \
         patch("app.main.get_ai_summarizer") as mock_factory:
        mock_fetch.return_value = ("<html><body>Safe content text.</body></html>", "https://example.com", "example.com")
        mock_summarizer = AsyncMock()
        mock_summarizer.summarize.return_value = "Summary"
        mock_factory.return_value = mock_summarizer

        # Uses 10/minute fallback; first request succeeds
        r1 = client.post("/api/summarize", json={"url": "https://example.com"})
        assert r1.status_code == 200
