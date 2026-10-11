"""Tests for URL syntax, scheme validation, and IP classification."""

import pytest
from app.services.fetcher import (
    is_public_ip,
    validate_url_and_resolve,
    SSRFValidationError,
    FetchError,
)


def test_public_ip_filtering():
    """Verify that private, loopback, link-local, and reserved IPs are rejected."""
    # Loopback
    assert not is_public_ip("127.0.0.1")
    assert not is_public_ip("127.0.1.1")
    assert not is_public_ip("::1")

    # RFC 1918 Private
    assert not is_public_ip("10.0.0.1")
    assert not is_public_ip("192.168.1.1")
    assert not is_public_ip("172.16.0.1")
    assert not is_public_ip("172.31.255.255")

    # Link-local & Cloud metadata (AWS / GCP / Azure)
    assert not is_public_ip("169.254.169.254")
    assert not is_public_ip("169.254.1.1")
    assert not is_public_ip("fe80::1")

    # Unspecified & Multicast
    assert not is_public_ip("0.0.0.0")
    assert not is_public_ip("224.0.0.1")
    assert not is_public_ip("240.0.0.1")

    # CGNAT (RFC 6598) & Documentation ranges
    assert not is_public_ip("100.64.0.1")
    assert not is_public_ip("192.0.2.1")
    assert not is_public_ip("198.51.100.1")
    assert not is_public_ip("203.0.113.1")

    # IPv4-mapped IPv6 equivalents
    assert not is_public_ip("::ffff:127.0.0.1")
    assert not is_public_ip("::ffff:10.0.0.1")
    assert not is_public_ip("::ffff:169.254.169.254")
    assert not is_public_ip("::ffff:100.64.0.1")

    # Valid public IPs
    assert is_public_ip("93.184.216.34")  # example.com
    assert is_public_ip("8.8.8.8")
    assert is_public_ip("1.1.1.1")


def test_reject_unsupported_schemes():
    """Verify non-HTTP/HTTPS schemes are rejected."""
    for scheme in ["ftp://example.com", "file:///etc/passwd", "gopher://example.com", "javascript:alert(1)"]:
        with pytest.raises(SSRFValidationError):
            validate_url_and_resolve(scheme)


def test_reject_embedded_credentials():
    """Verify embedded credentials in URLs are rejected."""
    with pytest.raises(SSRFValidationError):
        validate_url_and_resolve("http://admin:secret@example.com/login")


def test_reject_overlong_urls():
    """Verify URLs exceeding 2048 characters are rejected."""
    long_url = "https://example.com/" + "a" * 2050
    with pytest.raises(FetchError) as exc_info:
        validate_url_and_resolve(long_url)
    assert exc_info.value.code == "INVALID_URL"
    assert exc_info.value.status_code == 400


def test_reject_localhost_destination():
    """Verify localhost resolution is blocked."""
    with pytest.raises(SSRFValidationError):
        validate_url_and_resolve("http://localhost/admin")
    with pytest.raises(SSRFValidationError):
        validate_url_and_resolve("http://127.0.0.1:8000/api")
