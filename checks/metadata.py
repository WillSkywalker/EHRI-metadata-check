import requests
from bs4 import BeautifulSoup
import extruct
from rich.console import Console
from typing import Dict, Any, List, Optional

console = Console()


def fetch_page(url: str) -> Optional[requests.Response]:
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response
    except requests.RequestException as e:
        console.print(f"[bold red]Error fetching {url}: {e}[/bold red]")
        return None


def validate_html_lang(soup: BeautifulSoup) -> Dict[str, Any]:
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
    results = []
    required_meta = ["description", "viewport"]  # Basic list

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

    # Check charset
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
    og_tags = soup.find_all(
        "meta", attrs={"property": lambda x: x and x.startswith("og:")}
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
    try:
        data = extruct.extract(
            html_content, base_url=url, uniform=True, syntaxes=["json-ld"]
        )
        return data.get("json-ld", [])
    except Exception as e:
        console.print(f"[bold red]Error extracting JSON-LD: {e}[/bold red]")
        return []


def get_metadata_results(
    url: str, response: Optional[requests.Response] = None
) -> Dict[str, Any]:
    if not response:
        response = fetch_page(url)

    if not response:
        return {"error": f"Could not fetch {url}"}

    soup = BeautifulSoup(response.content, "html.parser")

    return {
        "url": url,
        "html_lang": validate_html_lang(soup),
        "meta_tags": validate_meta_tags(soup),
        "open_graph": validate_opengraph(soup),
        "json_ld": extract_jsonld(response.text, url),
        "response": response,  # Return response object for further checks (html validity etc) if needed, but maybe just text is enough.
        # Actually, let's not return response object in the dict to avoid serialization issues later if passed around,
        # but needed for other checks.
        # Better design: The caller handles response fetching if they want to optimize.
        # `get_metadata_results` will accept response (optional) or fetch it.
    }
