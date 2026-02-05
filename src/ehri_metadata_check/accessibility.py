"""
Accessibility Module

Provides comprehensive accessibility checks based on WCAG criteria.
Can be used as a standalone module or as part of the validation pipeline.
"""

from bs4 import BeautifulSoup
from typing import Dict, Any, List


def check_accessibility(html_content: str) -> Dict[str, Any]:
    """
    Perform comprehensive accessibility checks based on WCAG criteria.

    Args:
        html_content: HTML content as a string.

    Returns:
        Dictionary with status, error/warning counts, issues list, and message.
    """
    soup = BeautifulSoup(html_content, "html.parser")
    issues: List[Dict[str, Any]] = []

    # --- 3.1.1 H57: Document language ---
    html_tag = soup.find("html")
    if not html_tag or not html_tag.get("lang"):
        issues.append(
            {
                "wcag": "3.1.1 H57",
                "type": "missing_lang",
                "severity": "error",
                "message": "HTML element missing lang attribute",
            }
        )

    # --- 1.1.1 H37: Images must have alt text ---
    for img in soup.find_all("img"):
        alt = img.get("alt")
        # alt="" is valid for decorative images, but missing alt is not
        if alt is None:
            issues.append(
                {
                    "wcag": "1.1.1 H37",
                    "type": "image_alt_missing",
                    "severity": "error",
                    "element": str(img)[:80],
                    "message": "Image missing alt attribute",
                }
            )

    # --- 1.3.1 H44 & ARIA16: Input elements must have labels ---
    for inp in soup.find_all("input"):
        input_type = inp.get("type", "text")
        # Skip hidden, submit, button, reset, image (handled separately)
        if input_type in ["hidden", "submit", "button", "reset", "image"]:
            continue

        input_id = inp.get("id")
        aria_label = inp.get("aria-label")
        aria_labelledby = inp.get("aria-labelledby")
        title = inp.get("title")

        has_label = False
        if input_id:
            label = soup.find("label", attrs={"for": input_id})
            if label:
                has_label = True

        if not has_label and not aria_label and not aria_labelledby and not title:
            issues.append(
                {
                    "wcag": "1.3.1 H44/ARIA16",
                    "type": "input_missing_label",
                    "severity": "error",
                    "element": str(inp)[:80],
                    "message": f"Input ({input_type}) has no associated label",
                }
            )

    # Check select elements
    for sel in soup.find_all("select"):
        sel_id = sel.get("id")
        aria_label = sel.get("aria-label")
        aria_labelledby = sel.get("aria-labelledby")

        has_label = False
        if sel_id:
            label = soup.find("label", attrs={"for": sel_id})
            if label:
                has_label = True

        if not has_label and not aria_label and not aria_labelledby:
            issues.append(
                {
                    "wcag": "1.3.1 H44/ARIA16",
                    "type": "select_missing_label",
                    "severity": "error",
                    "element": str(sel)[:80],
                    "message": "Select element has no associated label",
                }
            )

    # Check textarea elements
    for ta in soup.find_all("textarea"):
        ta_id = ta.get("id")
        aria_label = ta.get("aria-label")
        aria_labelledby = ta.get("aria-labelledby")

        has_label = False
        if ta_id:
            label = soup.find("label", attrs={"for": ta_id})
            if label:
                has_label = True

        if not has_label and not aria_label and not aria_labelledby:
            issues.append(
                {
                    "wcag": "1.3.1 H44/ARIA16",
                    "type": "textarea_missing_label",
                    "severity": "error",
                    "element": str(ta)[:80],
                    "message": "Textarea has no associated label",
                }
            )

    # --- 1.1.1 & 2.4.4: Buttons must have accessible content ---
    for btn in soup.find_all("button"):
        text = btn.get_text(strip=True)
        aria_label = btn.get("aria-label")
        aria_labelledby = btn.get("aria-labelledby")
        title = btn.get("title")
        # Check for image with alt inside button
        img = btn.find("img")
        img_alt = img.get("alt") if img else None

        if (
            not text
            and not aria_label
            and not aria_labelledby
            and not title
            and not img_alt
        ):
            issues.append(
                {
                    "wcag": "1.1.1 & 2.4.4",
                    "type": "empty_button",
                    "severity": "error",
                    "element": str(btn)[:80],
                    "message": "Button has no accessible name",
                }
            )

    # Check input type=submit, button, reset
    for inp in soup.find_all("input", attrs={"type": ["submit", "button", "reset"]}):
        value = inp.get("value")
        aria_label = inp.get("aria-label")
        aria_labelledby = inp.get("aria-labelledby")
        title = inp.get("title")

        if not value and not aria_label and not aria_labelledby and not title:
            issues.append(
                {
                    "wcag": "1.1.1 & 2.4.4",
                    "type": "empty_input_button",
                    "severity": "error",
                    "element": str(inp)[:80],
                    "message": f"Input type={inp.get('type')} has no accessible name",
                }
            )

    # --- 2.4.4 G91 & H30: Links must have accessible content ---
    for link in soup.find_all("a", href=True):
        text = link.get_text(strip=True)
        aria_label = link.get("aria-label")
        aria_labelledby = link.get("aria-labelledby")
        title = link.get("title")
        # Check for image with alt inside link
        img = link.find("img")
        img_alt = img.get("alt") if img else None

        if (
            not text
            and not aria_label
            and not aria_labelledby
            and not title
            and not img_alt
        ):
            issues.append(
                {
                    "wcag": "2.4.4 G91/H30",
                    "type": "empty_link",
                    "severity": "error",
                    "element": str(link)[:80],
                    "message": "Link has no accessible name",
                }
            )

    # --- 1.3.1 H42: Heading structure ---
    headings = soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])
    h1_count = len(soup.find_all("h1"))
    if h1_count == 0:
        issues.append(
            {
                "wcag": "1.3.1 H42",
                "type": "missing_h1",
                "severity": "warning",
                "message": "Page has no H1 heading",
            }
        )
    elif h1_count > 1:
        issues.append(
            {
                "wcag": "1.3.1 H42",
                "type": "multiple_h1",
                "severity": "warning",
                "message": f"Page has {h1_count} H1 headings (should typically have one)",
            }
        )

    # Check heading order (no skipped levels)
    prev_level = 0
    for h in headings:
        level = int(h.name[1])
        if prev_level > 0 and level > prev_level + 1:
            issues.append(
                {
                    "wcag": "1.3.1 H42",
                    "type": "heading_skip",
                    "severity": "warning",
                    "element": str(h)[:80],
                    "message": f"Heading level skipped from H{prev_level} to H{level}",
                }
            )
        prev_level = level

    # --- 1.3.1 H51: Tables should have headers ---
    for table in soup.find_all("table"):
        has_th = table.find("th")
        if not has_th:
            issues.append(
                {
                    "wcag": "1.3.1 H51",
                    "type": "table_missing_headers",
                    "severity": "warning",
                    "element": str(table)[:80],
                    "message": "Data table has no header cells (th)",
                }
            )

    # Count errors vs warnings
    errors = [i for i in issues if i.get("severity") == "error"]
    warnings = [i for i in issues if i.get("severity") == "warning"]

    return {
        "status": "PASS" if not errors else "FAIL",
        "error_count": len(errors),
        "warning_count": len(warnings),
        "issues": issues,
        "message": f"Found {len(errors)} errors, {len(warnings)} warnings"
        if issues
        else "No issues found",
    }
