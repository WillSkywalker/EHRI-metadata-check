import requests
from rich.console import Console
from typing import Dict, Any, List

console = Console()


def check_html_validity(html_content: str) -> Dict[str, Any]:
    """
    Validates HTML content using the W3C Validator API (checking 'nu' validator).
    """
    api_url = "https://validator.w3.org/nu/?out=json"
    headers = {"Content-Type": "text/html; charset=utf-8"}

    try:
        response = requests.post(
            api_url, headers=headers, data=html_content.encode("utf-8"), timeout=15
        )
        response.raise_for_status()
        result = response.json()

        messages = result.get("messages", [])
        errors = [m for m in messages if m.get("type") == "error"]
        warnings = [
            m for m in messages if m.get("type") == "info"
        ]  # 'info' usually includes warnings

        return {
            "status": "PASS" if not errors else "FAIL",
            "error_count": len(errors),
            "warning_count": len(warnings),
            "messages": messages,
        }
    except Exception as e:
        console.print(f"[bold red]Error checking HTML validity: {e}[/bold red]")
        return {"status": "ERROR", "message": str(e)}
