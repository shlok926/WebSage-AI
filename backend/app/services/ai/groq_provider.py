"""WebSage AI — Groq API Provider.

Connects to the official Groq Chat Completions endpoint using the
approved production model (openai/gpt-oss-20b) with timeouts,
sanitized error mapping, and strict credential isolation.
"""

import httpx
from typing import Optional
from app.config import settings
from app.services.ai.base import (
    AISummarizer,
    AIError,
    AIRateLimitError,
    AITimeoutError,
    AIAuthenticationError,
    SYSTEM_SUMMARIZER_PROMPT,
)


class GroqAISummarizer(AISummarizer):
    """Groq API inference implementation."""

    GROQ_ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.GROQ_API_KEY
        self.model = model or settings.GROQ_MODEL

    async def summarize(self, text: str) -> str:
        if not self.api_key or self.api_key.strip() in ("", "your_groq_api_key_here"):
            raise AIAuthenticationError("Groq API key is not configured in backend/.env.")

        headers = {
            "Authorization": f"Bearer {self.api_key.strip()}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_SUMMARIZER_PROMPT},
                {"role": "user", "content": f"Summarize the following extracted webpage content:\n\n{text}"},
            ],
            "temperature": 0.3,
            "max_tokens": 512,
        }

        timeout = httpx.Timeout(settings.AI_TIMEOUT_SECONDS, connect=5.0)

        async with httpx.AsyncClient(timeout=timeout) as client:
            try:
                response = await client.post(self.GROQ_ENDPOINT, headers=headers, json=payload)

                if response.status_code in (401, 403):
                    raise AIAuthenticationError("Invalid or unauthorized Groq API key.")

                if response.status_code == 429:
                    raise AIRateLimitError("Groq free tier rate limit reached. Please wait before retrying.")

                if response.status_code != 200:
                    raise AIError(
                        "AI_PROVIDER_ERROR",
                        f"Groq API returned HTTP {response.status_code}.",
                        502,
                    )

                data = response.json()
                choices = data.get("choices")
                if not choices or not isinstance(choices, list) or len(choices) == 0:
                    raise AIError("AI_MALFORMED_RESPONSE", "Invalid response structure from AI provider.", 502)

                message = choices[0].get("message", {})
                content = message.get("content", "").strip()

                if not content:
                    raise AIError("AI_EMPTY_RESPONSE", "AI provider returned an empty summary.", 502)

                return content

            except httpx.TimeoutException:
                raise AITimeoutError()
            except (AIError, AIAuthenticationError, AIRateLimitError):
                raise
            except httpx.HTTPError:
                raise AIError("AI_CONNECTION_ERROR", "Failed to communicate with AI provider.", 502)
