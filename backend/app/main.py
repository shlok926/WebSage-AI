"""WebSage AI — FastAPI Application Entrypoint.

Implements REST API endpoints, security middleware, and standardized error handling
in strict conformance with Requirements v1.2 and Security Baseline v1.2.
"""

import ipaddress
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.config import settings
from app.models import SummarizeRequest, SummarizeResponse, ErrorResponse, HealthResponse
from app.services.fetcher import FetchError, fetch_webpage_html
from app.services.extractor import extract_readable_text
from app.services.ai.base import AIError
from app.services.ai.factory import get_ai_summarizer


def get_client_ip(request: Request) -> str:
    """Safely extract client IP for rate limiting.

    Only honors forwarded headers if TRUST_PROXY_HEADERS is explicitly True.
    Defaults to request.client.host (direct socket peer) to prevent arbitrary
    client-controlled header spoofing.

    When TRUST_PROXY_HEADERS is True:
    - Checks X-Real-IP first (commonly populated with the true edge client IP).
    - If inspecting X-Forwarded-For, uses the rightmost candidate (appended by the
      immediate trusted reverse proxy) rather than the untrusted leftmost entry.
    - Validates candidate string syntax using ipaddress.ip_address.
    """
    if settings.TRUST_PROXY_HEADERS:
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            candidate = real_ip.strip()
            try:
                ipaddress.ip_address(candidate)
                return candidate
            except ValueError:
                pass

        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            ips = [ip.strip() for ip in forwarded_for.split(",") if ip.strip()]
            if ips:
                candidate = ips[-1]
                try:
                    ipaddress.ip_address(candidate)
                    return candidate
                except ValueError:
                    pass

    if request.client and request.client.host:
        return request.client.host
    return "127.0.0.1"



limiter = Limiter(key_func=get_client_ip)

app = FastAPI(
    title="WebSage AI API",
    version="1.2",
    description="AI Webpage Summarizer Backend API",
)

app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)

# CORS Configuration — Restricted to approved frontend origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Accept"],
)


@app.exception_handler(RateLimitExceeded)
async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """Handle per-client rate limit exhaustion with standardized 429 response."""
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "error": {
                "code": "RATE_LIMIT_EXCEEDED",
                "message": "Rate limit exceeded. Please wait before submitting more requests.",
            }
        },
    )


@app.exception_handler(FetchError)
async def fetch_error_handler(request: Request, exc: FetchError):
    """Handle webpage fetching, SSRF, and HTML extraction errors."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message}},
    )


@app.exception_handler(AIError)
async def ai_error_handler(request: Request, exc: AIError):
    """Handle AI provider errors, rate limits, and timeouts."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message}},
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    """Handle request schema validation errors without leaking internal schemas."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": {
                "code": "INVALID_REQUEST",
                "message": "Malformed request. A valid 'url' property (max 2048 chars) is required.",
            }
        },
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Fallback handler ensuring internal errors never expose stack traces or secrets."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An internal error occurred while processing the request.",
            }
        },
    )


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Minimal health check endpoint without exposing sensitive configuration."""
    return HealthResponse(status="ok")


def get_summarize_rate_limit() -> str:
    """Return configured rate limit for /api/summarize endpoint, failing safely if malformed."""
    limit_str = settings.RATE_LIMIT_SUMMARIZE
    try:
        from limits import parse
        parse(limit_str)
        return limit_str
    except Exception:
        return "10/minute"


@app.post(
    "/api/summarize",
    response_model=SummarizeResponse,
    responses={
        400: {"model": ErrorResponse},
        413: {"model": ErrorResponse},
        415: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
        429: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
        502: {"model": ErrorResponse},
        504: {"model": ErrorResponse},
    },
)
@limiter.limit(get_summarize_rate_limit)
async def summarize_webpage(request: Request, payload: SummarizeRequest):
    """Fetch public HTML webpage, extract readable content, and generate AI summary."""
    # 1. Fetch public HTML safely with SSRF protection, size caps, and timeouts
    html_content, final_url, final_host = await fetch_webpage_html(payload.url)

    # 2. Extract and clean readable text from HTML (bounded to 20,000 chars)
    bounded_text, original_chars = extract_readable_text(html_content)

    # 3. Generate summary via configured AI provider
    summarizer = get_ai_summarizer()
    summary = await summarizer.summarize(bounded_text)

    # 4. Return documented response
    return SummarizeResponse(
        summary=summary,
        source_url=final_url,
        source_host=final_host,
        extracted_characters=original_chars,
    )
