from bs4 import BeautifulSoup
from rich.console import Console
from typing import Dict, Any

console = Console()


def check_accessibility(html_content: str) -> Dict[str, Any]:
    """
    Performs basic static accessibility checks.
    Currently checks:
    - Images have alt attributes
    - Buttons have content or aria-label
    """
    soup = BeautifulSoup(html_content, "html.parser")
    issues = []

    # Check images
    images = soup.find_all("img")
    for img in images:
        if not img.has_attr("alt"):
            issues.append(
                {
                    "type": "image_alt_missing",
                    "element": str(img)[:50] + "...",
                    "message": "Image missing alt attribute",
                }
            )
        else:
            alt_val = img.get("alt")
            # In some BS4 configurations/versions, attributes can be lists
            if isinstance(alt_val, list):
                alt_val = " ".join(alt_val)

            if not (alt_val or "").strip():
                # Empty alt is fine for decorative images usually
                pass

    # Check buttons
    buttons = soup.find_all("button")
    for btn in buttons:
        text = btn.get_text(strip=True)
        aria_label = btn.get("aria-label")
        aria_labelledby = btn.get("aria-labelledby")

        if not text and not aria_label and not aria_labelledby:
            issues.append(
                {
                    "type": "empty_button",
                    "element": str(btn)[:50] + "...",
                    "message": "Button has no text and no accessible label",
                }
            )

    return {
        "status": "PASS" if not issues else "FAIL",
        "issues": issues,
        "message": f"Found {len(issues)} issues" if issues else "No issues found",
    }


def run_accessibility_checks(html_content: str):
    result = check_accessibility(html_content)
    issues = result["issues"]
    console.print("\n[bold]Accessibility Checks (Basic):[/bold]")
    if not issues:
        console.print("  [green]No basic issues found (Images/Buttons).[/green]")
    else:
        console.print(f"  [red]Found {len(issues)} potential issues:[/red]")
        for issue in issues[:5]:  # Show first 5
            console.print(
                f"  - {issue['message']}: [italic]{issue['element']}[/italic]"
            )
        if len(issues) > 5:
            console.print(f"  ...and {len(issues) - 5} more.")
