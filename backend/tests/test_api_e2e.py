"""End-to-end API integration tests for /health and /api/summarize endpoints."""

import pytest
from unittest.mock import patch


@pytest.mark.asyncio
async def test_health_check_endpoint(async_client):
    """Verify GET /health returns 200 OK without sensitive information."""
    response = await async_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_summarize_success_flow(async_client):
    """Verify POST /api/summarize complete successful pipeline."""
    mock_html = """
    <html>
        <body>
            <article>
                <h1>Autonomous Systems Research</h1>
                <p>Autonomous systems integrate sensing, decision making, and actuation to perform tasks independently.</p>
                <p>Modern advances in artificial intelligence and edge computing have significantly broadened the operational domains.</p>
            </article>
        </body>
    </html>
    """

    from unittest.mock import AsyncMock, MagicMock
    mock_ai = MagicMock()
    mock_ai.summarize = AsyncMock(return_value="Autonomous systems integrate sensing, decision making, and actuation independently.")

    with patch("app.main.fetch_webpage_html", return_value=(mock_html, "https://example.com/research", "example.com")), \
         patch("app.main.get_ai_summarizer", return_value=mock_ai):
        response = await async_client.post("/api/summarize", json={"url": "https://example.com/research"})

        assert response.status_code == 200
        data = response.json()
        assert "summary" in data
        assert data["source_url"] == "https://example.com/research"
        assert data["source_host"] == "example.com"
        assert data["extracted_characters"] > 50


@pytest.mark.asyncio
async def test_summarize_ssrf_rejection(async_client):
    """Verify POST /api/summarize rejects SSRF attempts with sanitized 400 error."""
    response = await async_client.post("/api/summarize", json={"url": "http://127.0.0.1:8000/private"})

    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "SSRF_BLOCKED"
    # Ensure no internal IPs or system paths are leaked
    assert "127.0.0.1" not in data["error"]["message"]


@pytest.mark.asyncio
async def test_summarize_invalid_request_body(async_client):
    """Verify malformed JSON requests return 400 with documented error shape."""
    response = await async_client.post("/api/summarize", json={"bad_field": "not a url"})

    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "INVALID_REQUEST"


@pytest.mark.asyncio
async def test_summarize_insufficient_content(async_client):
    """Verify pages with insufficient readable text return 422 error."""
    mock_html = "<html><body><p>Sparse</p></body></html>"

    with patch("app.main.fetch_webpage_html", return_value=(mock_html, "https://example.com/empty", "example.com")):
        response = await async_client.post("/api/summarize", json={"url": "https://example.com/empty"})

        assert response.status_code == 422
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "INSUFFICIENT_CONTENT"
