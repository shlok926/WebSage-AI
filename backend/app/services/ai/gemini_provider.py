"""WebSage AI — Google Gemini API Provider.

Connects to Google's official Gemini API using the official `google-genai` SDK
with strict input bounds, 30-second timeouts, prompt-injection isolation,
and sanitized error mapping.
"""

import asyncio
from typing import Optional, Any
from app.config import settings
from app.services.ai.base import (
    AISummarizer,
    AIError,
    AIRateLimitError,
    AITimeoutError,
    AIAuthenticationError,
    SYSTEM_SUMMARIZER_PROMPT,
)


class GeminiAISummarizer(AISummarizer):
    """Google Gemini API inference implementation using the google-genai SDK."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        client: Optional[Any] = None,
    ):
        self.api_key = api_key if api_key is not None else settings.GEMINI_API_KEY
        self.model = model or settings.GEMINI_MODEL
        self._client = client

    def _get_client(self) -> Any:
        if self._client is not None:
            return self._client

        from google import genai
        return genai.Client(api_key=self.api_key.strip())

    async def summarize(self, text: str) -> str:
        if not self.api_key or self.api_key.strip() in (
            "",
            "replace_with_your_gemini_api_key",
            "your_gemini_api_key_here",
        ):
            raise AIAuthenticationError("Gemini API key is not configured in backend/.env.")

        from google.genai import types, errors

        client = self._get_client()

        contents = f"Summarize the following extracted webpage content:\n\n{text}"
        config = types.GenerateContentConfig(
            system_instruction=SYSTEM_SUMMARIZER_PROMPT,
            thinking_config=types.ThinkingConfig(thinking_budget=0),
            temperature=0.3,
            max_output_tokens=1024,
        )

        try:
            response = await asyncio.wait_for(
                client.aio.models.generate_content(
                    model=self.model,
                    contents=contents,
                    config=config,
                ),
                timeout=settings.AI_TIMEOUT_SECONDS,
            )

        except asyncio.TimeoutError:
            raise AITimeoutError("Gemini API request exceeded the 30-second timeout.")

        except errors.APIError as err:
            if err.code in (401, 403):
                raise AIAuthenticationError("Invalid or unauthorized Gemini API key.")
            if err.code == 429:
                raise AIRateLimitError("Gemini API rate limit reached. Please wait before retrying.")
            raise AIError(
                "AI_PROVIDER_ERROR",
                f"Gemini API returned HTTP status {err.code}.",
                502,
            )

        except errors.ClientError as err:
            code = getattr(err, "code", None)
            if code in (401, 403):
                raise AIAuthenticationError("Invalid or unauthorized Gemini API key.")
            if code == 429:
                raise AIRateLimitError("Gemini API rate limit reached. Please wait before retrying.")
            raise AIError("AI_PROVIDER_ERROR", "Gemini client request failed.", 502)

        except errors.ServerError:
            raise AIError("AI_PROVIDER_ERROR", "Gemini service temporarily unavailable.", 502)

        except (AIError, AIAuthenticationError, AIRateLimitError, AITimeoutError):
            raise

        except Exception:
            # Catch unexpected network or connection exceptions without leaking secrets
            raise AIError("AI_CONNECTION_ERROR", "Failed to communicate with Gemini API.", 502)

        if not response or not hasattr(response, "text"):
            raise AIError("AI_MALFORMED_RESPONSE", "Invalid response structure from Gemini provider.", 502)

        content = (response.text or "").strip()
        if not content:
            raise AIError("AI_EMPTY_RESPONSE", "Gemini provider returned an empty summary.", 502)

        return content
