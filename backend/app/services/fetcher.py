"""WebSage AI — SSRF-Safe Web Page Fetcher.

Implements strict SSRF defenses, pre-request DNS validation, outbound IP pinning
(DNS rebinding / TOCTOU mitigation), redirect revalidation, streaming size caps,
and timeouts according to Requirements v1.2 and Security Baseline v1.2.
"""

import ipaddress
import socket
from urllib.parse import urlparse, urljoin
import httpx
import ssl
from typing import Tuple, Optional, Union

from app.config import settings

# Configure IP-pinning transport to eliminate DNS rebinding TOCTOU window
try:
    import httpcore

    class PinningNetworkBackend(httpcore.AsyncNetworkBackend):
        """Network backend that connects exclusively to a pre-validated public IP."""
        def __init__(self, target_ip: str):
            super().__init__()
            self.target_ip = target_ip
            # Use public AnyIOBackend instead of private _network_backend attribute
            self._backend = httpcore.AnyIOBackend()

        async def connect_tcp(self, host: str, port: int, *args, **kwargs):
            # Outbound TCP socket is pinned to the pre-validated IP address,
            # preventing DNS rebinding/TOCTOU attacks where DNS changes after validation.
            # Host/SNI and TLS certificate verification are preserved at the HTTP/TLS layer.
            return await self._backend.connect_tcp(self.target_ip, port, *args, **kwargs)

        async def connect_unix_socket(self, *args, **kwargs):
            return await self._backend.connect_unix_socket(*args, **kwargs)

        async def sleep(self, seconds: float):
            return await self._backend.sleep(seconds)

    class PinningTransport(httpx.AsyncHTTPTransport):
        """Custom HTTP transport pinning TCP connections to verified public IP.

        Preserves:
        - Full TLS certificate validation (CERT_REQUIRED), hostname checking, and SNI
        - Transport settings (verify, cert, trust_env, limits, http1, http2, retries)
        - Clean connection pooling and lifecycle without allocating unpinned pools
        """
        def __init__(
            self,
            target_ip: str,
            verify: Union[ssl.SSLContext, str, bool] = True,
            cert: Optional[Union[str, Tuple[str, str]]] = None,
            trust_env: bool = True,
            http1: bool = True,
            http2: bool = False,
            limits: Optional[httpx.Limits] = None,
            retries: int = 0,
            **kwargs,
        ):
            # Do not invoke super().__init__ to prevent allocating an unpinned pool.
            limits = limits or httpx.Limits()
            if isinstance(verify, ssl.SSLContext):
                ssl_context = verify
            else:
                ssl_context = httpx.create_ssl_context(verify=verify, cert=cert, trust_env=trust_env)

            self._pool = httpcore.AsyncConnectionPool(
                ssl_context=ssl_context,
                max_connections=limits.max_connections,
                max_keepalive_connections=limits.max_keepalive_connections,
                keepalive_expiry=limits.keepalive_expiry,
                http1=http1,
                http2=http2,
                retries=retries,
                network_backend=PinningNetworkBackend(target_ip),
            )

except Exception:
    PinningTransport = None
    PinningNetworkBackend = None




class FetchError(Exception):
    """Base exception for web fetch errors."""
    def __init__(self, code: str, message: str, status_code: int):
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class SSRFValidationError(FetchError):
    """Raised when a URL targets non-public or prohibited destinations."""
    def __init__(self, message: str = "The requested URL is not accessible or prohibited."):
        super().__init__("SSRF_BLOCKED", message, 400)


class PayloadTooLargeError(FetchError):
    """Raised when the fetched page exceeds size limit."""
    def __init__(self, message: str = "Webpage size exceeds the maximum limit of 2 MiB."):
        super().__init__("PAYLOAD_TOO_LARGE", message, 413)


class UnsupportedContentTypeError(FetchError):
    """Raised when the content type is not supported HTML."""
    def __init__(self, message: str = "This page does not contain readable HTML content."):
        super().__init__("UNSUPPORTED_CONTENT", message, 415)


class UpstreamTimeoutError(FetchError):
    """Raised when upstream fetch exceeds timeout."""
    def __init__(self, message: str = "The webpage request timed out."):
        super().__init__("UPSTREAM_TIMEOUT", message, 504)


class UpstreamFetchError(FetchError):
    """Raised when upstream fetch fails."""
    def __init__(self, message: str = "Failed to retrieve the requested webpage."):
        super().__init__("UPSTREAM_ERROR", message, 502)


class SecureTransportError(FetchError):
    """Raised when secure pinned transport cannot be initialized or used.

    Enforces fail-closed security: unpinned fallback requests are strictly prohibited.
    """
    def __init__(self, message: str = "Secure network transport unavailable."):
        super().__init__("SECURITY_ERROR", message, 500)


def is_public_ip(ip_str: str) -> bool:
    """Validate whether an IP address is a safe, publicly routable address.

    Blocks: private, loopback, link-local, multicast, reserved, unspecified,
    CGNAT (100.64.0.0/10), documentation ranges, and IPv4-mapped equivalents.
    """
    try:
        ip = ipaddress.ip_address(ip_str)
        # Unwrap IPv4-mapped IPv6 addresses (e.g. ::ffff:127.0.0.1)
        if getattr(ip, "ipv4_mapped", None):
            ip = ip.ipv4_mapped

        # Reject all non-globally-routable addresses (including CGNAT RFC 6598)
        if not ip.is_global:
            return False

        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_multicast
            or ip.is_reserved
            or ip.is_unspecified
        ):
            return False
        return True
    except ValueError:
        return False


def validate_url_and_resolve(url_str: str) -> Tuple[str, str, str]:
    """Validate URL syntax, scheme, credentials, and resolve DNS to ensure public IP.

    Returns:
        Tuple[normalized_url, hostname, validated_ip]
    Raises:
        SSRFValidationError or FetchError
    """
    if len(url_str) > settings.MAX_URL_LENGTH:
        raise FetchError("INVALID_URL", f"URL exceeds maximum allowed length of {settings.MAX_URL_LENGTH} characters.", 400)

    try:
        parsed = urlparse(url_str)
    except Exception:
        raise SSRFValidationError("Invalid URL format.")

    # 1. Scheme check: only http and https
    if parsed.scheme.lower() not in ("http", "https"):
        raise SSRFValidationError("Only HTTP and HTTPS URLs are supported.")

    # 2. Reject embedded userinfo/credentials (e.g. http://user:pass@example.com)
    if parsed.username or parsed.password:
        raise SSRFValidationError("URLs with embedded credentials are not allowed.")

    hostname = parsed.hostname
    if not hostname:
        raise SSRFValidationError("URL must include a valid hostname.")

    port = parsed.port or (443 if parsed.scheme.lower() == "https" else 80)

    # 3. DNS resolution & IP check
    try:
        addr_info = socket.getaddrinfo(hostname, port, type=socket.SOCK_STREAM)
        if not addr_info:
            raise SSRFValidationError("Failed to resolve host destination.")

        resolved_ips = []
        for item in addr_info:
            sockaddr = item[4]
            ip_str = sockaddr[0]
            if not is_public_ip(ip_str):
                raise SSRFValidationError("Access to private, loopback, or internal network destinations is prohibited.")
            resolved_ips.append(ip_str)

        if not resolved_ips:
            raise SSRFValidationError("Failed to resolve host destination.")

        primary_ip = resolved_ips[0]

    except socket.gaierror:
        raise SSRFValidationError("Could not resolve host name.")
    except SSRFValidationError:
        raise
    except Exception:
        raise SSRFValidationError("Invalid host destination.")

    return url_str, hostname, primary_ip


async def fetch_webpage_html(url: str) -> Tuple[str, str, str]:
    """Fetch HTML content from a public URL safely.

    Enforces:
    - Pre-request SSRF validation on initial URL
    - Outbound IP pinning to prevent DNS rebinding / TOCTOU evasion
    - Manual redirect following (max 3 hops) with revalidation on each hop
    - Streaming byte limiting (aborts if > 2 MiB)
    - Content-Type verification (must be HTML)
    - 10-second overall timeout

    Returns:
        Tuple[html_content, final_url, final_host]
    """
    current_url, current_host, current_ip = validate_url_and_resolve(url)
    redirect_count = 0

    headers = {
        "User-Agent": "WebSageAI/1.2 (+https://websage-ai.local; demonstration summarizer)",
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "en-US,en;q=0.9",
    }

    # Setup timeout
    timeout = httpx.Timeout(
        settings.FETCH_TIMEOUT_SECONDS,
        connect=min(5.0, settings.FETCH_TIMEOUT_SECONDS),
        read=settings.FETCH_TIMEOUT_SECONDS,
    )

    while True:
        # Enforce fail-closed security: outbound requests are strictly prohibited
        # if the custom IP-pinning transport is unavailable or fails to initialize.
        if PinningTransport is None:
            raise SecureTransportError("Secure network transport is unavailable.")

        try:
            transport = PinningTransport(current_ip)
        except Exception:
            raise SecureTransportError("Failed to initialize secure network transport.")

        if transport is None:
            raise SecureTransportError("Secure network transport is unavailable.")

        client_kwargs = {
            "timeout": timeout,
            "follow_redirects": False,
            "transport": transport,
        }

        async with httpx.AsyncClient(**client_kwargs) as client:
            try:
                # Security Notice (CodeQL py/full-ssrf / CWE-918):
                # CodeQL flags this GET request because `current_url` originates from user input.
                # However, full SSRF is strictly mitigated here by:
                # 1. `validate_url_and_resolve()` pre-resolving and blocking private, loopback, link-local,
                #    cloud metadata (169.254.169.254), multicast, and non-global IPs.
                # 2. `PinningTransport(current_ip)` overriding the HTTP transport layer to bind the outbound
                #    socket directly to the pre-validated public IP, preventing DNS rebinding (TOCTOU attacks).
                async with client.stream("GET", current_url, headers=headers) as response:
                    # Check for redirect status codes
                    if response.status_code in (301, 302, 303, 307, 308):
                        redirect_count += 1
                        if redirect_count > settings.MAX_REDIRECTS:
                            raise FetchError("TOO_MANY_REDIRECTS", f"Exceeded maximum of {settings.MAX_REDIRECTS} redirects.", 400)

                        location = response.headers.get("location")
                        if not location:
                            raise UpstreamFetchError("Redirect response did not include a Location header.")

                        # Resolve relative redirect URLs against current_url
                        next_url = urljoin(current_url, location)
                        current_url, current_host, current_ip = validate_url_and_resolve(next_url)
                        continue

                    # If response is not redirect, check status
                    if response.status_code >= 400:
                        raise UpstreamFetchError(f"Webpage returned error status HTTP {response.status_code}.")

                    # Validate Content-Type
                    content_type = response.headers.get("content-type", "").lower()
                    if not any(t in content_type for t in ("text/html", "application/xhtml+xml")):
                        raise UnsupportedContentTypeError(f"Unsupported content type '{content_type}'. Only HTML pages can be summarized.")

                    # Stream body with size limit
                    chunks = []
                    total_bytes = 0

                    async for chunk in response.aiter_bytes():
                        total_bytes += len(chunk)
                        if total_bytes > settings.MAX_RESPONSE_BYTES:
                            raise PayloadTooLargeError()
                        chunks.append(chunk)

                    # Determine encoding
                    encoding = response.encoding or "utf-8"
                    raw_bytes = b"".join(chunks)

                    try:
                        html_content = raw_bytes.decode(encoding, errors="replace")
                    except Exception:
                        html_content = raw_bytes.decode("utf-8", errors="replace")

                    return html_content, current_url, current_host

            except httpx.TimeoutException:
                raise UpstreamTimeoutError()
            except FetchError:
                raise
            except httpx.HTTPError:
                raise UpstreamFetchError("An error occurred while connecting to the target webpage.")
