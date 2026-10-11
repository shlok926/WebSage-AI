"""WebSage AI — HTML Text Extractor.

Parses HTML documents using BeautifulSoup4, removes boilerplate and non-content elements,
and normalizes readable text bounded by Requirements v1.2 limits.
"""

from bs4 import BeautifulSoup
from typing import Tuple
from app.config import settings
from app.services.fetcher import FetchError


class ExtractionError(FetchError):
    """Raised when HTML parsing or extraction fails."""
    pass


class InsufficientContentError(FetchError):
    """Raised when page has empty or insufficient readable text."""
    def __init__(self, message: str = "This page contains insufficient readable text to generate a summary."):
        super().__init__("INSUFFICIENT_CONTENT", message, 422)


def extract_readable_text(html_content: str) -> Tuple[str, int]:
    """Parse HTML and extract clean, bounded readable text.

    Returns:
        Tuple[clean_text, original_character_count]
    Raises:
        InsufficientContentError if readable text is below MIN_EXTRACTED_CHARS
    """
    if not html_content or not html_content.strip():
        raise InsufficientContentError()

    soup = BeautifulSoup(html_content, "html.parser")

    # Remove non-content tags
    unwanted_tags = [
        "script",
        "style",
        "noscript",
        "nav",
        "footer",
        "header",
        "aside",
        "svg",
        "iframe",
        "form",
        "button",
        "input",
    ]
    for tag in soup.find_all(unwanted_tags):
        tag.decompose()

    # Prioritize main article containers if present, otherwise body, otherwise whole doc
    main_content = soup.find("article") or soup.find("main") or soup.find(id="content") or soup.body or soup

    # Extract text with space separator
    raw_text = main_content.get_text(separator=" ", strip=True)

    # Normalize whitespace (collapse multiple spaces, tabs, newlines into single spaces)
    normalized_words = raw_text.split()
    clean_text = " ".join(normalized_words)

    char_count = len(clean_text)

    if char_count < settings.MIN_EXTRACTED_CHARS:
        raise InsufficientContentError(
            f"Page contains only {char_count} readable characters, which is insufficient to summarize."
        )

    # Truncate to maximum bound approved in Requirements v1.2 (20,000 characters)
    if char_count > settings.MAX_EXTRACTED_CHARS:
        bounded_text = clean_text[: settings.MAX_EXTRACTED_CHARS]
    else:
        bounded_text = clean_text

    return bounded_text, char_count
