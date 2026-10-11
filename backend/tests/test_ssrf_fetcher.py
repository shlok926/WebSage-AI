"""Tests for SSRF prevention, outbound IP pinning, redirect revalidation, streaming limits, and timeouts."""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
import httpx

from app.services.fetcher import (
    fetch_webpage_html,
    validate_url_and_resolve,
    PinningNetworkBackend,
    PinningTransport,
    SSRFValidationError,
    PayloadTooLargeError,
    UnsupportedContentTypeError,
    UpstreamTimeoutError,
    FetchError,
)


@pytest.mark.asyncio
async def test_ssrf_blocks_private_ip():
    """Verify URLs resolving to private IPs are blocked before connecting."""
    with pytest.raises(SSRFValidationError):
        await fetch_webpage_html("http://127.0.0.1/admin")


@pytest.mark.asyncio
async def test_ssrf_blocks_aws_metadata_ip():
    """Verify cloud metadata endpoint (169.254.169.254) is blocked."""
    with pytest.raises(SSRFValidationError):
        await fetch_webpage_html("http://169.254.169.254/latest/meta-data/")


@pytest.mark.asyncio
async def test_reject_non_html_content_type():
    """Verify non-HTML responses (e.g. PDF or binary) return 415 error."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.headers = {"content-type": "application/pdf"}

    with patch("app.services.fetcher.validate_url_and_resolve", return_value=("https://example.com/file.pdf", "example.com", "93.184.216.34")), \
         patch("httpx.AsyncClient.stream") as mock_stream:
        mock_ctx = AsyncMock()
        mock_ctx.__aenter__.return_value = mock_response
        mock_stream.return_value = mock_ctx

        with pytest.raises(UnsupportedContentTypeError) as exc_info:
            await fetch_webpage_html("https://example.com/file.pdf")
        assert exc_info.value.status_code == 415
        assert exc_info.value.code == "UNSUPPORTED_CONTENT"


@pytest.mark.asyncio
async def test_enforce_streaming_body_size_limit():
    """Verify pages exceeding 2 MiB trigger 413 error during streaming."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.headers = {"content-type": "text/html"}

    # Simulate chunk stream exceeding 2 MiB (2 * 1024 * 1024 = 2,097,152 bytes)
    chunk_1mb = b"A" * (1024 * 1024)
    async def mock_iter():
        yield chunk_1mb
        yield chunk_1mb
        yield chunk_1mb  # Total = 3 MiB

    mock_response.aiter_bytes = mock_iter

    with patch("app.services.fetcher.validate_url_and_resolve", return_value=("https://example.com/huge.html", "example.com", "93.184.216.34")), \
         patch("httpx.AsyncClient.stream") as mock_stream:
        mock_ctx = AsyncMock()
        mock_ctx.__aenter__.return_value = mock_response
        mock_stream.return_value = mock_ctx

        with pytest.raises(PayloadTooLargeError) as exc_info:
            await fetch_webpage_html("https://example.com/huge.html")
        assert exc_info.value.status_code == 413
        assert exc_info.value.code == "PAYLOAD_TOO_LARGE"


@pytest.mark.asyncio
async def test_upstream_timeout_handling():
    """Verify timeouts raise 504 UPSTREAM_TIMEOUT error."""
    with patch("app.services.fetcher.validate_url_and_resolve", return_value=("https://example.com/slow", "example.com", "93.184.216.34")), \
         patch("httpx.AsyncClient.stream", side_effect=httpx.ReadTimeout("Timeout")):
        with pytest.raises(UpstreamTimeoutError) as exc_info:
            await fetch_webpage_html("https://example.com/slow")
        assert exc_info.value.status_code == 504
        assert exc_info.value.code == "UPSTREAM_TIMEOUT"


@pytest.mark.asyncio
async def test_dns_rebinding_network_backend_pinning():
    """Verify PinningNetworkBackend pins outbound TCP destination to the validated public IP."""
    target_public_ip = "93.184.216.34"
    backend = PinningNetworkBackend(target_ip=target_public_ip)

    connected_destination = []

    async def mock_super_connect(host, port, *args, **kwargs):
        connected_destination.append((host, port))
        mock_stream = AsyncMock()
        return mock_stream

    with patch.object(backend._backend, "connect_tcp", side_effect=mock_super_connect):
        # Even if the caller requests 'attacker-rebind.com', the backend connects strictly to target_public_ip
        await backend.connect_tcp("attacker-rebind.com", 443)

    assert len(connected_destination) == 1
    # Confirms outbound connection went to the pre-validated public IP, preventing rebinding
    assert connected_destination[0][0] == target_public_ip
    assert connected_destination[0][1] == 443


@pytest.mark.asyncio
async def test_redirect_to_private_ip_is_blocked():
    """Verify redirects to private or loopback destinations are blocked on redirect revalidation."""
    initial_response = MagicMock()
    initial_response.status_code = 302
    initial_response.headers = {"location": "http://127.0.0.1:8000/internal"}

    with patch("app.services.fetcher.validate_url_and_resolve") as mock_validate, \
         patch("httpx.AsyncClient.stream") as mock_stream:
        # First call validates initial public URL
        # Second call validates redirect destination and raises SSRFValidationError
        mock_validate.side_effect = [
            ("https://example.com/redirect", "example.com", "93.184.216.34"),
            SSRFValidationError("Access to private, loopback, or internal network destinations is prohibited."),
        ]

        mock_ctx = AsyncMock()
        mock_ctx.__aenter__.return_value = initial_response
        mock_stream.return_value = mock_ctx

        with pytest.raises(SSRFValidationError) as exc_info:
            await fetch_webpage_html("https://example.com/redirect")

        assert exc_info.value.status_code == 400
        assert exc_info.value.code == "SSRF_BLOCKED"


@pytest.mark.asyncio
async def test_redirect_limit_enforcement():
    """Verify exceeding maximum redirects (3 hops) raises TOO_MANY_REDIRECTS."""
    redirect_response = MagicMock()
    redirect_response.status_code = 302
    redirect_response.headers = {"location": "https://example.com/hop"}

    with patch("app.services.fetcher.validate_url_and_resolve", return_value=("https://example.com/hop", "example.com", "93.184.216.34")), \
         patch("httpx.AsyncClient.stream") as mock_stream:
        mock_ctx = AsyncMock()
        mock_ctx.__aenter__.return_value = redirect_response
        mock_stream.return_value = mock_ctx

        with pytest.raises(FetchError) as exc_info:
            await fetch_webpage_html("https://example.com/hop")

        assert exc_info.value.status_code == 400
        assert exc_info.value.code == "TOO_MANY_REDIRECTS"
