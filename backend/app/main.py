"""WebSage AI — FastAPI Application Entrypoint.

Implements REST API endpoints, security middleware, and standardized error handling
in strict conformance with Requirements v1.2 and Security Baseline v1.2.
"""

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.config import settings
from app.models import SummarizeRequest, SummarizeResponse, ErrorResponse, HealthResponse
from app.services.fetcher import FetchError, fetch_webpage_html
from app.services.extractor import extract_readable_text
from app.services.ai.base import AIError
from app.services.ai.factory import get_ai_summarizer

app = FastAPI(
    title="WebSage AI API",
    version="1.2",
    description="AI Webpage Summarizer Backend API",
)

# CORS Configuration — Restricted to approved frontend origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Accept"],
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


@app.post(
    "/api/summarize",
    response_model=SummarizeResponse,
    responses={
        400: {"model": ErrorResponse},
        413: {"model": ErrorResponse},
        415: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
        429: {"model": ErrorResponse},
        502: {"model": ErrorResponse},
        504: {"model": ErrorResponse},
    },
)
async def summarize_webpage(payload: SummarizeRequest):
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
