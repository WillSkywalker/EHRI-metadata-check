from bs4 import BeautifulSoup
from rich.console import Console
from typing import Dict, Any, List

console = Console()


def check_accessibility(html_content: str) -> List[Dict[str, Any]]:
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
    img_issues = 0
    for img in images:
        if not img.has_attr("alt"):
            img_issues += 1
            issues.append(
                {
                    "type": "image_alt_missing",
                    "element": str(img)[:50] + "...",
                    "message": "Image missing alt attribute",
                }
            )
        elif not (img.get("alt") or "").strip():
            # Empty alt is fine for decorative images usually, but worth noting if not marked role="presentation"
            pass

    # Check buttons
    buttons = soup.find_all("button")
    btn_issues = 0
    for btn in buttons:
        text = btn.get_text(strip=True)
        aria_label = btn.get("aria-label")
        aria_labelledby = btn.get("aria-labelledby")

        if not text and not aria_label and not aria_labelledby:
            btn_issues += 1
            issues.append(
                {
                    "type": "empty_button",
                    "element": str(btn)[:50] + "...",
                    "message": "Button has no text and no accessible label",
                }
            )

    return issues


def run_accessibility_checks(html_content: str):
    issues = check_accessibility(html_content)
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
