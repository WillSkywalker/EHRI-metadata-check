"""
Validation Module

Provides async validation of URLs using aiohttp for parallel HTTP requests.
"""

import asyncio
import aiohttp
from bs4 import BeautifulSoup
import extruct
from typing import Dict, Any, List

from ehri_metadata_check.accessibility import check_accessibility


# --- HTTP Fetching ---
async def fetch_page(session: aiohttp.ClientSession, url: str) -> Dict[str, Any]:
    """Fetch a page asynchronously and return content and status."""
    try:
        async with session.get(
            url, timeout=aiohttp.ClientTimeout(total=15)
        ) as response:
            content = await response.read()
            text = await response.text()
            return {
                "url": url,
                "status_code": response.status,
                "content": content,
                "text": text,
                "ok": response.ok,
            }
    except asyncio.TimeoutError:
        return {"url": url, "error": "Request timed out"}
    except aiohttp.ClientError as e:
        return {"url": url, "error": f"Client error: {e}"}
    except Exception as e:
        return {"url": url, "error": f"Unexpected error: {e}"}


# --- Metadata Validation ---
def validate_html_lang(soup: BeautifulSoup) -> Dict[str, Any]:
    """Check if HTML has a lang attribute."""
    html_tag = soup.find("html")
    lang = html_tag.get("lang") if html_tag else None
    return {
        "status": "PASS" if lang else "FAIL",
        "value": lang,
        "message": f"HTML lang attribute is '{lang}'"
        if lang
        else "HTML lang attribute is missing",
    }


def validate_meta_tags(soup: BeautifulSoup) -> List[Dict[str, Any]]:
    """Check for required meta tags."""
    results = []
    required_meta = ["description", "viewport"]

    for name in required_meta:
        tag = soup.find("meta", attrs={"name": name})
        content = tag.get("content") if tag else None
        results.append(
            {
                "tag": f"meta name='{name}'",
                "status": "PASS" if content else "FAIL",
                "content": content,
                "message": "Found" if content else "Missing",
            }
        )

    charset_tag = soup.find("meta", attrs={"charset": True})
    results.append(
        {
            "tag": "meta charset",
            "status": "PASS" if charset_tag else "FAIL",
            "content": charset_tag.get("charset") if charset_tag else None,
            "message": "Found" if charset_tag else "Missing",
        }
    )

    return results


def validate_opengraph(soup: BeautifulSoup) -> Dict[str, Any]:
    """Check for Open Graph meta tags."""
    og_tags = soup.find_all(
        "meta", attrs={"property": lambda x: isinstance(x, str) and x.startswith("og:")}
    )
    found_props = {tag.get("property"): tag.get("content") for tag in og_tags}

    required_props = ["og:title", "og:type", "og:image", "og:url"]
    missing = [p for p in required_props if p not in found_props]

    return {
        "status": "PASS" if not missing else "FAIL",
        "found": found_props,
        "missing": missing,
        "message": f"Missing properties: {', '.join(missing)}"
        if missing
        else "All required Open Graph tags found",
    }


def extract_jsonld(html_content: str, url: str) -> List[Dict[str, Any]]:
    """Extract JSON-LD structured data."""
    try:
        data = extruct.extract(
            html_content, base_url=url, uniform=True, syntaxes=["json-ld"]
        )
        return data.get("json-ld", [])
    except Exception:
        return []


# --- HTML Validity (W3C API) ---
async def check_html_validity(
    session: aiohttp.ClientSession, html_content: str
) -> Dict[str, Any]:
    """Validate HTML using W3C Validator API."""
    api_url = "https://validator.w3.org/nu/?out=json"
    headers = {"Content-Type": "text/html; charset=utf-8"}

    try:
        # Add delay to avoid overwhelming the W3C API
        await asyncio.sleep(0.5)

        async with session.post(
            api_url,
            headers=headers,
            data=html_content.encode("utf-8"),
            timeout=aiohttp.ClientTimeout(total=30),  # Increased timeout
        ) as response:
            if response.status == 429:
                return {
                    "status": "ERROR",
                    "message": "W3C API rate limited (429). Try again later.",
                }
            if not response.ok:
                return {
                    "status": "ERROR",
                    "message": f"W3C API returned {response.status}",
                }

            result = await response.json()
            messages = result.get("messages", [])
            errors = [m for m in messages if m.get("type") == "error"]
            warnings = [m for m in messages if m.get("type") == "info"]

            return {
                "status": "PASS" if not errors else "FAIL",
                "error_count": len(errors),
                "warning_count": len(warnings),
                "messages": messages,
            }
    except asyncio.TimeoutError:
        return {"status": "ERROR", "message": "W3C API request timed out (30s)"}
    except Exception as e:
        return {"status": "ERROR", "message": str(e)}


# --- Full Validation Pipeline ---
async def validate_url(session: aiohttp.ClientSession, url: str) -> Dict[str, Any]:
    """Validate a single URL."""
    # Fetch page
    fetch_result = await fetch_page(session, url)

    if "error" in fetch_result:
        return {"metadata": {"error": fetch_result["error"]}}

    html_text = fetch_result["text"]
    html_content = fetch_result["content"]

    # Parse with BeautifulSoup
    soup = BeautifulSoup(html_content, "html.parser")

    # Metadata validation (synchronous, fast)
    metadata = {
        "url": url,
        "html_lang": validate_html_lang(soup),
        "meta_tags": validate_meta_tags(soup),
        "open_graph": validate_opengraph(soup),
        "json_ld": extract_jsonld(html_text, url),
    }

    # HTML validity check (async, network I/O)
    html_validity = await check_html_validity(session, html_text)

    # Accessibility check (synchronous, CPU-bound)
    accessibility = check_accessibility(html_text)

    return {
        "metadata": metadata,
        "html_validity": html_validity,
        "accessibility": accessibility,
    }


async def validate_urls(urls: List[str]) -> Dict[str, Dict[str, Any]]:
    """Validate multiple URLs in parallel."""
    results = {}

    async with aiohttp.ClientSession() as session:
        tasks = {url: validate_url(session, url) for url in urls}
        completed = await asyncio.gather(*tasks.values(), return_exceptions=True)

        for url, result in zip(tasks.keys(), completed):
            if isinstance(result, Exception):
                results[url] = {"metadata": {"error": str(result)}}
            else:
                results[url] = result

    return results
