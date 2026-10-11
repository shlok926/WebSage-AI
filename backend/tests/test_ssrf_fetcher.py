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
    UpstreamFetchError,
    SecureTransportError,
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


@pytest.mark.asyncio
async def test_missing_pinning_transport_fails_closed():
    """Verify that if PinningTransport is None, fetcher fails closed with 500 SECURITY_ERROR without sending requests."""
    with patch("app.services.fetcher.validate_url_and_resolve", return_value=("https://example.com", "example.com", "93.184.216.34")), \
         patch("app.services.fetcher.PinningTransport", None), \
         patch("httpx.AsyncClient") as mock_client:
        with pytest.raises(SecureTransportError) as exc_info:
            await fetch_webpage_html("https://example.com")

        assert exc_info.value.status_code == 500
        assert exc_info.value.code == "SECURITY_ERROR"
        # Crucial: prove no HTTP client was created or unpinned request sent
        mock_client.assert_not_called()


@pytest.mark.asyncio
async def test_broken_pinning_transport_init_fails_closed():
    """Verify that if PinningTransport fails to initialize, fetcher fails closed without unpinned fallback."""
    with patch("app.services.fetcher.validate_url_and_resolve", return_value=("https://example.com", "example.com", "93.184.216.34")), \
         patch("app.services.fetcher.PinningTransport", side_effect=RuntimeError("Transport pool creation failed")), \
         patch("httpx.AsyncClient") as mock_client:
        with pytest.raises(SecureTransportError) as exc_info:
            await fetch_webpage_html("https://example.com")

        assert exc_info.value.status_code == 500
        assert exc_info.value.code == "SECURITY_ERROR"
        mock_client.assert_not_called()


@pytest.mark.asyncio
async def test_unpinned_transport_never_instantiated():
    """Verify that httpx.AsyncClient is always provided a secure PinningTransport and never default unpinned."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.headers = {"content-type": "text/html"}

    async def mock_iter():
        yield b"<html><body>Safe</body></html>"

    mock_response.aiter_bytes = mock_iter

    captured_client_kwargs = {}

    class MockAsyncClient:
        def __init__(self, **kwargs):
            nonlocal captured_client_kwargs
            captured_client_kwargs = kwargs

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        def stream(self, *args, **kwargs):
            mock_ctx = AsyncMock()
            mock_ctx.__aenter__.return_value = mock_response
            return mock_ctx

    with patch("app.services.fetcher.validate_url_and_resolve", return_value=("https://example.com", "example.com", "93.184.216.34")), \
         patch("httpx.AsyncClient", MockAsyncClient):
        await fetch_webpage_html("https://example.com")

    # Verify that transport keyword argument was strictly passed and is not None
    assert "transport" in captured_client_kwargs
    assert captured_client_kwargs["transport"] is not None
    assert isinstance(captured_client_kwargs["transport"], PinningTransport)


def test_httpcore_and_httpx_compatibility():
    """Verify that current versions of HTTPX and HTTPCore support the custom network backend architecture."""
    import httpcore
    target_ip = "93.184.216.34"

    # 1. Verify AnyIOBackend is available and exports connect_tcp
    backend = PinningNetworkBackend(target_ip=target_ip)
    assert hasattr(backend._backend, "connect_tcp")
    assert isinstance(backend._backend, httpcore.AnyIOBackend)

    # 2. Verify PinningTransport creates connection pool correctly with strict TLS
    transport = PinningTransport(target_ip=target_ip)
    assert hasattr(transport, "_pool")
    assert isinstance(transport._pool, httpcore.AsyncConnectionPool)
    import ssl
    assert transport._pool._ssl_context.verify_mode == ssl.CERT_REQUIRED
    assert transport._pool._ssl_context.check_hostname is True

    # 3. Verify connect_tcp redirects host to validated IP while preserving SNI / TLS args
    with patch.object(backend._backend, "connect_tcp", new_callable=AsyncMock) as mock_connect:
        import asyncio
        asyncio.run(backend.connect_tcp("example.com", 443, server_hostname="example.com"))
        mock_connect.assert_called_once_with("93.184.216.34", 443, server_hostname="example.com")


@pytest.mark.asyncio
async def test_real_https_tls_hostname_and_sni_validation(tmp_path):
    """Verify real TLS handshake, certificate validation, SNI, and Host headers on controlled HTTPS server."""
    import asyncio
    import datetime
    import ssl
    from cryptography import x509

    from cryptography.x509.oid import NameOID
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa

    # 1. Generate test CA
    ca_key = rsa.generate_private_key(65537, 2048)
    ca_name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "Test CA")])
    ca_cert = (
        x509.CertificateBuilder()
        .subject_name(ca_name)
        .issuer_name(ca_name)
        .public_key(ca_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=1))
        .not_valid_after(datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=1))
        .add_extension(x509.BasicConstraints(ca=True, path_length=None), True)
        .add_extension(x509.KeyUsage(digital_signature=True, content_commitment=False, key_encipherment=False, data_encipherment=False, key_agreement=False, key_cert_sign=True, crl_sign=True, encipher_only=False, decipher_only=False), True)
        .add_extension(x509.SubjectKeyIdentifier.from_public_key(ca_key.public_key()), False)
        .sign(ca_key, hashes.SHA256())
    )

    # 2. Generate Server Cert with SAN: test.local
    server_key = rsa.generate_private_key(65537, 2048)
    server_cert = (
        x509.CertificateBuilder()
        .subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "test.local")]))
        .issuer_name(ca_name)
        .public_key(server_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=1))
        .not_valid_after(datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=1))
        .add_extension(x509.SubjectAlternativeName([x509.DNSName("test.local")]), False)
        .add_extension(x509.AuthorityKeyIdentifier.from_issuer_public_key(ca_key.public_key()), False)
        .sign(ca_key, hashes.SHA256())
    )

    ca_file = str(tmp_path / "ca.pem")
    server_cert_file = str(tmp_path / "server.pem")
    server_key_file = str(tmp_path / "key.pem")

    with open(ca_file, "wb") as f:
        f.write(ca_cert.public_bytes(serialization.Encoding.PEM))
    with open(server_cert_file, "wb") as f:
        f.write(server_cert.public_bytes(serialization.Encoding.PEM))
    with open(server_key_file, "wb") as f:
        f.write(server_key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))

    server_ssl = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    server_ssl.load_cert_chain(server_cert_file, server_key_file)

    sni_received = []
    def sni_callback(ssl_obj, server_name, ssl_ctx):
        sni_received.append(server_name)

    server_ssl.sni_callback = sni_callback
    host_header_received = []

    async def handle_client(reader, writer):
        line = await reader.readline()
        while True:
            header_line = await reader.readline()
            if not header_line or header_line == b"\r\n":
                break
            if header_line.lower().startswith(b"host:"):
                host_header_received.append(header_line.decode().strip())
        writer.write(b"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\nContent-Length: 13\r\n\r\nHello World!\n")
        await writer.drain()
        writer.close()
        await writer.wait_closed()

    server = await asyncio.start_server(handle_client, "127.0.0.1", 0, ssl=server_ssl)
    port = server.sockets[0].getsockname()[1]

    try:
        # Pinned request to test.local connecting through 127.0.0.1
        client_ssl_ctx = ssl.create_default_context(cafile=ca_file)
        transport = PinningTransport(target_ip="127.0.0.1", verify=client_ssl_ctx)
        async with httpx.AsyncClient(transport=transport) as client:
            resp = await client.get(f"https://test.local:{port}/")
            assert resp.status_code == 200
            assert resp.text == "Hello World!\n"

        assert sni_received == ["test.local"]
        assert host_header_received[0] == f"Host: test.local:{port}"

        # Hostname mismatch rejected by real TLS certificate validation
        transport_mismatched = PinningTransport(target_ip="127.0.0.1", verify=client_ssl_ctx)
        async with httpx.AsyncClient(transport=transport_mismatched) as client:
            with pytest.raises(httpx.ConnectError):
                await client.get(f"https://mismatched.local:{port}/")

    finally:
        server.close()
        await server.wait_closed()
