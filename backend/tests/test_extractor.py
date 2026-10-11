"""Tests for HTML content extraction, cleaning, and text bounding."""

import pytest
from app.services.extractor import extract_readable_text, InsufficientContentError
from app.config import settings


def test_clean_html_and_strip_scripts_styles():
    """Verify scripts, styles, navs, and boilerplate are stripped."""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test Page</title>
        <style>body { font-size: 14px; } .hidden { display: none; }</style>
        <script>console.log("malicious or tracker script");</script>
    </head>
    <body>
        <nav><a href="/">Home</a><a href="/about">About</a></nav>
        <main>
            <h1>Artificial Intelligence in Modern Computing</h1>
            <p>Artificial intelligence continues to accelerate technological evolution across multiple disciplines.</p>
            <p>Engineers and researchers are deploying language models for real-world document comprehension and analysis.</p>
        </main>
        <footer><p>Copyright 2026. All rights reserved.</p></footer>
    </body>
    </html>
    """
    text, count = extract_readable_text(html)

    assert "console.log" not in text
    assert "font-size" not in text
    assert "Copyright 2026" not in text
    assert "Artificial Intelligence in Modern Computing" in text
    assert "language models for real-world document comprehension" in text
    assert count == len(text)


def test_reject_insufficient_content():
    """Verify that pages with fewer than MIN_EXTRACTED_CHARS raise 422 error."""
    sparse_html = "<html><body><p>Too short.</p></body></html>"
    with pytest.raises(InsufficientContentError) as exc_info:
        extract_readable_text(sparse_html)
    assert exc_info.value.code == "INSUFFICIENT_CONTENT"
    assert exc_info.value.status_code == 422


def test_truncate_overlong_text():
    """Verify text exceeding 20,000 characters is capped at MAX_EXTRACTED_CHARS."""
    repeated_paragraph = "<p>" + "This is a comprehensive analytical discussion about modern systems engineering. " * 500 + "</p>"
    large_html = f"<html><body><article>{repeated_paragraph}</article></body></html>"

    text, original_count = extract_readable_text(large_html)

    assert original_count > settings.MAX_EXTRACTED_CHARS
    assert len(text) == settings.MAX_EXTRACTED_CHARS
