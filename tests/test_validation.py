"""
Test cases for the validation module.

Tests cover:
- HTML lang attribute validation
- Meta tags validation
- Open Graph validation
- JSON-LD extraction
- fetch_page (mocked)
- Accessibility checks (via check_accessibility)
"""

import pytest
from bs4 import BeautifulSoup
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio
import aiohttp

from ehri_metadata_check.validation import (
    validate_html_lang,
    validate_meta_tags,
    validate_opengraph,
    extract_jsonld,
    fetch_page,
    check_html_validity,
)


# --- Fixtures ---


@pytest.fixture
def html_with_lang():
    """HTML with proper lang attribute."""
    return BeautifulSoup(
        '<html lang="en"><head></head><body></body></html>', "html.parser"
    )


@pytest.fixture
def html_without_lang():
    """HTML without lang attribute."""
    return BeautifulSoup("<html><head></head><body></body></html>", "html.parser")


@pytest.fixture
def html_with_meta_tags():
    """HTML with required meta tags."""
    return BeautifulSoup(
        """
        <html lang="en">
        <head>
            <meta charset="utf-8">
            <meta name="description" content="Test description">
            <meta name="viewport" content="width=device-width, initial-scale=1">
        </head>
        <body></body>
        </html>
        """,
        "html.parser",
    )


@pytest.fixture
def html_missing_meta_tags():
    """HTML missing some required meta tags."""
    return BeautifulSoup(
        """
        <html lang="en">
        <head>
            <meta charset="utf-8">
        </head>
        <body></body>
        </html>
        """,
        "html.parser",
    )


@pytest.fixture
def html_with_opengraph():
    """HTML with all required Open Graph tags."""
    return BeautifulSoup(
        """
        <html lang="en">
        <head>
            <meta property="og:title" content="Test Title">
            <meta property="og:type" content="website">
            <meta property="og:url" content="https://example.com">
            <meta property="og:image" content="https://example.com/image.jpg">
        </head>
        <body></body>
        </html>
        """,
        "html.parser",
    )


@pytest.fixture
def html_missing_opengraph():
    """HTML with some missing Open Graph tags."""
    return BeautifulSoup(
        """
        <html lang="en">
        <head>
            <meta property="og:title" content="Test Title">
        </head>
        <body></body>
        </html>
        """,
        "html.parser",
    )


@pytest.fixture
def html_with_jsonld():
    """HTML with JSON-LD structured data."""
    return """
    <html lang="en">
    <head>
        <script type="application/ld+json">
        {
            "@context": "https://schema.org",
            "@type": "Organization",
            "name": "Test Organization"
        }
        </script>
    </head>
    <body></body>
    </html>
    """


@pytest.fixture
def html_without_jsonld():
    """HTML without JSON-LD structured data."""
    return """
    <html lang="en">
    <head></head>
    <body></body>
    </html>
    """


# --- validate_html_lang tests ---


class TestValidateHtmlLang:
    """Tests for validate_html_lang function."""

    def test_html_with_lang_attribute(self, html_with_lang):
        """Test that HTML with lang attribute passes."""
        result = validate_html_lang(html_with_lang)
        assert result["status"] == "PASS"
        assert result["value"] == "en"
        assert "en" in result["message"]

    def test_html_without_lang_attribute(self, html_without_lang):
        """Test that HTML without lang attribute fails."""
        result = validate_html_lang(html_without_lang)
        assert result["status"] == "FAIL"
        assert result["value"] is None
        assert "missing" in result["message"].lower()

    def test_empty_html(self):
        """Test handling of empty HTML."""
        soup = BeautifulSoup("", "html.parser")
        result = validate_html_lang(soup)
        assert result["status"] == "FAIL"

    def test_html_with_empty_lang(self):
        """Test HTML with empty lang attribute."""
        soup = BeautifulSoup('<html lang=""><body></body></html>', "html.parser")
        result = validate_html_lang(soup)
        # Empty string is falsy, so should fail
        assert result["status"] == "FAIL"


# --- validate_meta_tags tests ---


class TestValidateMetaTags:
    """Tests for validate_meta_tags function."""

    def test_all_meta_tags_present(self, html_with_meta_tags):
        """Test that all required meta tags are found."""
        result = validate_meta_tags(html_with_meta_tags)
        assert len(result) == 3  # description, viewport, charset

        # Check each required tag
        for tag_result in result:
            assert tag_result["status"] == "PASS"
            assert tag_result["message"] == "Found"

    def test_missing_meta_tags(self, html_missing_meta_tags):
        """Test that missing meta tags are reported."""
        result = validate_meta_tags(html_missing_meta_tags)

        # Charset should pass
        charset_result = next(r for r in result if r["tag"] == "meta charset")
        assert charset_result["status"] == "PASS"

        # Description should fail
        desc_result = next(r for r in result if "description" in r["tag"])
        assert desc_result["status"] == "FAIL"
        assert desc_result["message"] == "Missing"

        # Viewport should fail
        viewport_result = next(r for r in result if "viewport" in r["tag"])
        assert viewport_result["status"] == "FAIL"
        assert viewport_result["message"] == "Missing"

    def test_empty_html(self):
        """Test handling of empty HTML."""
        soup = BeautifulSoup("", "html.parser")
        result = validate_meta_tags(soup)
        assert len(result) == 3
        for tag_result in result:
            assert tag_result["status"] == "FAIL"


# --- validate_opengraph tests ---


class TestValidateOpengraph:
    """Tests for validate_opengraph function."""

    def test_all_og_tags_present(self, html_with_opengraph):
        """Test that all required Open Graph tags pass."""
        result = validate_opengraph(html_with_opengraph)
        assert result["status"] == "PASS"
        assert len(result["missing"]) == 0
        assert "og:title" in result["found"]
        assert "og:type" in result["found"]
        assert "og:url" in result["found"]
        assert "og:image" in result["found"]

    def test_missing_og_tags(self, html_missing_opengraph):
        """Test that missing Open Graph tags are reported."""
        result = validate_opengraph(html_missing_opengraph)
        assert result["status"] == "FAIL"
        assert "og:type" in result["missing"]
        assert "og:url" in result["missing"]
        assert "og:image" in result["missing"]
        assert "og:title" not in result["missing"]

    def test_no_og_tags(self):
        """Test HTML with no Open Graph tags."""
        soup = BeautifulSoup("<html><head></head><body></body></html>", "html.parser")
        result = validate_opengraph(soup)
        assert result["status"] == "FAIL"
        assert len(result["missing"]) == 4

    def test_extra_og_tags(self):
        """Test that additional OG tags are captured."""
        soup = BeautifulSoup(
            """
            <html>
            <head>
                <meta property="og:title" content="Title">
                <meta property="og:type" content="website">
                <meta property="og:url" content="https://example.com">
                <meta property="og:image" content="https://example.com/image.jpg">
                <meta property="og:description" content="Description">
                <meta property="og:site_name" content="Site Name">
            </head>
            </html>
            """,
            "html.parser",
        )
        result = validate_opengraph(soup)
        assert result["status"] == "PASS"
        assert "og:description" in result["found"]
        assert "og:site_name" in result["found"]


# --- extract_jsonld tests ---


class TestExtractJsonld:
    """Tests for extract_jsonld function."""

    def test_extract_jsonld_present(self, html_with_jsonld):
        """Test extraction of JSON-LD data."""
        result = extract_jsonld(html_with_jsonld, "https://example.com")
        assert len(result) > 0
        assert result[0]["@type"] == "Organization"
        assert result[0]["name"] == "Test Organization"

    def test_extract_jsonld_not_present(self, html_without_jsonld):
        """Test extraction when no JSON-LD is present."""
        result = extract_jsonld(html_without_jsonld, "https://example.com")
        assert result == []

    def test_extract_multiple_jsonld(self):
        """Test extraction of multiple JSON-LD blocks."""
        html = """
        <html>
        <head>
            <script type="application/ld+json">
            {"@context": "https://schema.org", "@type": "Organization", "name": "Org1"}
            </script>
            <script type="application/ld+json">
            {"@context": "https://schema.org", "@type": "Person", "name": "Person1"}
            </script>
        </head>
        </html>
        """
        result = extract_jsonld(html, "https://example.com")
        assert len(result) == 2

    def test_extract_jsonld_invalid(self):
        """Test handling of invalid JSON-LD."""
        html = """
        <html>
        <head>
            <script type="application/ld+json">
            {invalid json}
            </script>
        </head>
        </html>
        """
        result = extract_jsonld(html, "https://example.com")
        # Should return empty list on error
        assert result == []


# --- fetch_page tests (async, mocked) ---


class TestFetchPage:
    """Tests for fetch_page function."""

    @pytest.mark.asyncio
    async def test_fetch_page_success(self):
        """Test successful page fetch."""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.ok = True
        mock_response.read = AsyncMock(return_value=b"<html></html>")
        mock_response.text = AsyncMock(return_value="<html></html>")

        mock_session = MagicMock()
        mock_session.get = MagicMock(
            return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_response))
        )

        with patch.object(mock_session, "get") as mock_get:
            mock_get.return_value.__aenter__ = AsyncMock(return_value=mock_response)
            mock_get.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await fetch_page(mock_session, "https://example.com")

            assert result["url"] == "https://example.com"
            assert result["status_code"] == 200
            assert result["ok"] is True

    @pytest.mark.asyncio
    async def test_fetch_page_timeout(self):
        """Test timeout handling."""
        mock_session = MagicMock()
        mock_session.get = MagicMock(side_effect=asyncio.TimeoutError())

        result = await fetch_page(mock_session, "https://example.com")

        assert result["url"] == "https://example.com"
        assert "error" in result
        assert "timed out" in result["error"]

    @pytest.mark.asyncio
    async def test_fetch_page_client_error(self):
        """Test client error handling."""
        mock_session = MagicMock()
        mock_session.get = MagicMock(
            side_effect=aiohttp.ClientError("Connection failed")
        )

        result = await fetch_page(mock_session, "https://example.com")

        assert result["url"] == "https://example.com"
        assert "error" in result
        assert "Client error" in result["error"]


# --- check_html_validity tests (async, mocked) ---


class TestCheckHtmlValidity:
    """Tests for check_html_validity function."""

    @pytest.mark.asyncio
    async def test_html_validity_pass(self):
        """Test valid HTML passes validation."""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.ok = True
        mock_response.json = AsyncMock(return_value={"messages": []})

        mock_session = MagicMock()
        mock_session.post = MagicMock()
        mock_session.post.return_value.__aenter__ = AsyncMock(
            return_value=mock_response
        )
        mock_session.post.return_value.__aexit__ = AsyncMock(return_value=None)

        with patch("asyncio.sleep", new_callable=AsyncMock):
            result = await check_html_validity(mock_session, "<html></html>")

        assert result["status"] == "PASS"
        assert result["error_count"] == 0

    @pytest.mark.asyncio
    async def test_html_validity_fail(self):
        """Test invalid HTML fails validation."""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.ok = True
        mock_response.json = AsyncMock(
            return_value={
                "messages": [
                    {"type": "error", "message": "Error 1"},
                    {"type": "error", "message": "Error 2"},
                    {"type": "info", "message": "Warning 1"},
                ]
            }
        )

        mock_session = MagicMock()
        mock_session.post = MagicMock()
        mock_session.post.return_value.__aenter__ = AsyncMock(
            return_value=mock_response
        )
        mock_session.post.return_value.__aexit__ = AsyncMock(return_value=None)

        with patch("asyncio.sleep", new_callable=AsyncMock):
            result = await check_html_validity(mock_session, "<html></html>")

        assert result["status"] == "FAIL"
        assert result["error_count"] == 2
        assert result["warning_count"] == 1

    @pytest.mark.asyncio
    async def test_html_validity_rate_limited(self):
        """Test handling of rate limiting (429)."""
        mock_response = AsyncMock()
        mock_response.status = 429

        mock_session = MagicMock()
        mock_session.post = MagicMock()
        mock_session.post.return_value.__aenter__ = AsyncMock(
            return_value=mock_response
        )
        mock_session.post.return_value.__aexit__ = AsyncMock(return_value=None)

        with patch("asyncio.sleep", new_callable=AsyncMock):
            result = await check_html_validity(mock_session, "<html></html>")

        assert result["status"] == "ERROR"
        assert "429" in result["message"]


# --- Integration-style tests using real parsing ---


class TestValidationIntegration:
    """Integration tests that use real HTML parsing."""

    def test_complete_valid_html(self):
        """Test a complete, valid HTML document."""
        html = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="utf-8">
            <meta name="description" content="A test page">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <meta property="og:title" content="Test Page">
            <meta property="og:type" content="website">
            <meta property="og:url" content="https://example.com">
            <meta property="og:image" content="https://example.com/image.jpg">
            <title>Test Page</title>
        </head>
        <body>
            <h1>Welcome</h1>
            <p>Content here.</p>
        </body>
        </html>
        """
        soup = BeautifulSoup(html, "html.parser")

        lang_result = validate_html_lang(soup)
        assert lang_result["status"] == "PASS"

        meta_result = validate_meta_tags(soup)
        assert all(r["status"] == "PASS" for r in meta_result)

        og_result = validate_opengraph(soup)
        assert og_result["status"] == "PASS"

    def test_minimal_html(self):
        """Test minimal HTML document with failures."""
        html = "<html><body>Hello</body></html>"
        soup = BeautifulSoup(html, "html.parser")

        lang_result = validate_html_lang(soup)
        assert lang_result["status"] == "FAIL"

        meta_result = validate_meta_tags(soup)
        assert all(r["status"] == "FAIL" for r in meta_result)

        og_result = validate_opengraph(soup)
        assert og_result["status"] == "FAIL"
