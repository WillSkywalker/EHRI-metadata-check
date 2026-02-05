"""
EHRI Metadata Validator Dashboard

A Streamlit dashboard to validate website metadata, HTML5 compliance, accessibility, and preview social media cards for EHRI websites.
"""

import streamlit as st
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import threading
import time
import asyncio

from ehri_metadata_check.validation import validate_urls


# --- Constants ---
EXAMPLE_URLS = [
    "https://blog.ehri-project.eu",
    "https://training.ehri-project.eu",
    "https://diplomatic-reports.ehri-project.eu",
    "https://early-testimony.ehri-project.eu",
    "https://the-sunflower.ehri-project.eu",
    "https://documentation-campaign.ehri-project.eu",
    "https://nisko-transports.ehri-project.eu",
    "https://ehri-nl.org",
    "https://ehri-kg.ehri-project.eu",
]


@dataclass
class ValidationStatus:
    """Represents the overall validation status."""

    PASS = "PASS"
    WARN = "WARN"
    ERROR = "ERROR"
    PENDING = "PENDING"
    RUNNING = "RUNNING"

    ICONS = {
        "PASS": "🟢",
        "WARN": "🟠",
        "ERROR": "🔴",
        "PENDING": "⚪",
        "RUNNING": "🔄",
    }


class StatusCalculator:
    """Calculates the overall status icon for a set of validation results."""

    @staticmethod
    def get_icon(results: Optional[Dict[str, Any]], is_running: bool = False) -> str:
        """Determine the status icon based on validation results."""
        if is_running:
            return ValidationStatus.ICONS["RUNNING"]
        if results is None:
            return ValidationStatus.ICONS["PENDING"]

        meta = results.get("metadata", {})
        if "error" in meta:
            return ValidationStatus.ICONS["ERROR"]

        validity = results.get("html_validity", {})
        if validity.get("status") != ValidationStatus.PASS:
            return ValidationStatus.ICONS["WARN"]

        acc = results.get("accessibility", {})
        if acc.get("status") == ValidationStatus.ERROR:
            return ValidationStatus.ICONS["ERROR"]
        if acc.get("status") != ValidationStatus.PASS or acc.get("issues"):
            return ValidationStatus.ICONS["WARN"]

        return ValidationStatus.ICONS["PASS"]


@st.cache_resource
def get_validation_state():
    """Get the cached validation state singleton."""
    return {
        "results": {},
        "is_validating": False,
        "urls_being_validated": [],
    }


def _run_validation_in_thread(urls: List[str], state: dict):
    """Run async validation in a background thread."""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        results = loop.run_until_complete(validate_urls(urls))

        state["results"].update(results)

        loop.close()
    except Exception as e:
        for url in urls:
            state["results"][url] = {"metadata": {"error": str(e)}}
    finally:
        state["is_validating"] = False
        state["urls_being_validated"] = []


class ValidationWorker:
    """Manages validation state using cached state for persistence."""

    @staticmethod
    def start_validation(urls: List[str]):
        """Start validating URLs in a background thread."""
        state = get_validation_state()

        if state["is_validating"]:
            return

        state["is_validating"] = True
        state["urls_being_validated"] = urls.copy()

        thread = threading.Thread(
            target=_run_validation_in_thread, args=(urls, state), daemon=True
        )
        thread.start()

    @staticmethod
    def get_results(url: str) -> Optional[Dict]:
        """Get results for a URL from cached state."""
        state = get_validation_state()
        return state["results"].get(url)

    @staticmethod
    def is_validating() -> bool:
        """Check if validation is in progress."""
        state = get_validation_state()
        return state["is_validating"]

    @staticmethod
    def get_urls_being_validated() -> List[str]:
        """Get list of URLs currently being validated."""
        state = get_validation_state()
        return state["urls_being_validated"] if state["is_validating"] else []

    @staticmethod
    def clear_results():
        """Clear all results."""
        state = get_validation_state()
        state["results"].clear()


class AppState:
    """Manages Streamlit session state for the dashboard."""

    @staticmethod
    def init():
        """Initialize session state variables."""
        if "url_list" not in st.session_state:
            st.session_state.url_list = EXAMPLE_URLS.copy()
        if "selected_url" not in st.session_state:
            st.session_state.selected_url = None

    @staticmethod
    def get_url_list() -> List[str]:
        return st.session_state.url_list

    @staticmethod
    def add_url(url: str):
        if url and url not in st.session_state.url_list:
            st.session_state.url_list.append(url)

    @staticmethod
    def remove_url(url: str):
        if url in st.session_state.url_list:
            st.session_state.url_list.remove(url)
        if st.session_state.selected_url == url:
            st.session_state.selected_url = None

    @staticmethod
    def set_selected_url(url: Optional[str]):
        st.session_state.selected_url = url

    @staticmethod
    def get_selected_url() -> Optional[str]:
        return st.session_state.selected_url


class SidebarUI:
    """Renders the sidebar UI."""

    @staticmethod
    def render():
        """Render the sidebar."""
        with st.sidebar:
            st.header("EHRI Validator")
            st.markdown(
                "Validate website metadata, HTML5 compliance, accessibility, and preview social media cards for EHRI websites."
            )

            st.divider()
            SidebarUI._render_url_list()
            SidebarUI._render_add_url_section()

            st.divider()

            SidebarUI._render_validate_button()

    @staticmethod
    def _render_add_url_section():
        """Render the add URL input and button."""
        new_url = st.text_input(
            "Add URL", placeholder="https://example.com", key="new_url_input"
        )
        is_validating = ValidationWorker.is_validating()

        if st.button("➕ Add URL", use_container_width=True, disabled=is_validating):
            if new_url:
                AppState.add_url(new_url)
                st.rerun()

    @staticmethod
    def _render_url_list():
        """Render the list of URLs in the sidebar."""
        st.subheader("URLs to Validate")
        url_list = AppState.get_url_list()
        is_validating = ValidationWorker.is_validating()
        urls_being_validated = ValidationWorker.get_urls_being_validated()

        if not url_list:
            st.caption("No URLs added yet.")
            return

        for url in url_list:
            is_running = url in urls_being_validated
            results = ValidationWorker.get_results(url)
            icon = StatusCalculator.get_icon(results, is_running)
            # Show full URL without http(s):// prefix
            display_url = url.replace("https://", "").replace("http://", "").rstrip("/")

            col_icon, col_url, col_del = st.columns([0.5, 5, 0.8])
            with col_icon:
                st.markdown(
                    f"<div style='padding-top: 8px; font-size: 1.2em;'>{icon}</div>",
                    unsafe_allow_html=True,
                )
            with col_url:
                if st.button(display_url, key=f"url_{url}", use_container_width=True):
                    AppState.set_selected_url(url)
            with col_del:
                if st.button(
                    "✕", key=f"del_{url}", help="Remove URL", disabled=is_validating
                ):
                    AppState.remove_url(url)
                    st.rerun()

    @staticmethod
    def _render_validate_button():
        """Render the 'Validate All' button."""
        is_validating = ValidationWorker.is_validating()

        if is_validating:
            st.info("Validating all URLs...")
            st.button("Validating...", disabled=True, use_container_width=True)
            time.sleep(0.3)
            st.rerun()
        else:
            clicked = st.button(
                "Validate All", type="primary", use_container_width=True
            )
            if clicked:
                url_list = AppState.get_url_list()
                if url_list:
                    ValidationWorker.start_validation(url_list)
                    st.rerun()

    @staticmethod
    def _format_url_for_display(url: str, max_len: int = 22) -> str:
        """Format a URL for display in the sidebar."""
        display = url.replace("https://", "").replace("http://", "").rstrip("/")
        if len(display) > max_len:
            display = display[: max_len - 3] + "..."
        return display


class MainUI:
    """Renders the main content area."""

    @staticmethod
    def render():
        """Render the main content."""
        st.title("EHRI Website Metadata Validator")

        selected_url = AppState.get_selected_url()

        if not selected_url:
            st.info(
                "Add URLs in the sidebar and click **Validate All** to start. Then click a URL to view its results."
            )
            return

        urls_being_validated = ValidationWorker.get_urls_being_validated()
        if selected_url in urls_being_validated:
            st.warning(f"Validating `{selected_url}`...")
            return

        results = ValidationWorker.get_results(selected_url)
        if results is None:
            st.warning(
                f"URL `{selected_url}` has not been validated yet. Click **Validate All** in the sidebar."
            )
            return

        st.markdown(f"## Results for `{selected_url}`")
        ResultsUI.render(results)


class ResultsUI:
    """Renders the validation results in tabs."""

    @staticmethod
    def render(data: Dict[str, Any]):
        """Render the tabbed results view."""
        tab1, tab2, tab3, tab4, tab5 = st.tabs(
            [
                "Metadata",
                "HTML5 Validity",
                "Accessibility",
                "JSON-LD",
                "Social Media Preview",
            ]
        )

        with tab1:
            ResultsUI._render_metadata_tab(data)
        with tab2:
            ResultsUI._render_html_validity_tab(data)
        with tab3:
            ResultsUI._render_accessibility_tab(data)
        with tab4:
            ResultsUI._render_jsonld_tab(data)
        with tab5:
            ResultsUI._render_social_preview_tab(data)

    @staticmethod
    def _render_metadata_tab(data: Dict):
        """Render the metadata tab."""
        meta = data["metadata"]

        if "error" in meta:
            st.error(f"Failed to fetch metadata: {meta['error']}")
            return

        st.subheader("HTML Lang")
        lang = meta.get("html_lang", {})
        if lang.get("status") == "PASS":
            st.success(f"{lang.get('message', '')}")
        else:
            st.error(f"{lang.get('message', 'Missing HTML lang attribute')}")

        st.subheader("Meta Tags")
        for tag in meta.get("meta_tags", []):
            if tag["status"] == "PASS":
                st.success(f"**{tag['tag']}**: {tag['content']}")
            else:
                st.error(f"**{tag['tag']}**: Missing")

        st.subheader("Open Graph")
        og = meta.get("open_graph", {})
        if og.get("status") == "PASS":
            st.success("All required OG tags found")
        else:
            st.error(f"Missing OG tags: {', '.join(og.get('missing', []))}")
        st.json(og.get("found", {}))

    @staticmethod
    def _render_html_validity_tab(data: Dict):
        """Render the HTML validity tab."""
        res = data.get("html_validity", {})
        if res.get("status") == "PASS":
            st.success(
                f"Pass! (Errors: {res.get('error_count', 0)}, Warnings: {res.get('warning_count', 0)})"
            )
        elif res.get("status") == "FAIL":
            st.error(
                f"Fail! (Errors: {res.get('error_count', 0)}, Warnings: {res.get('warning_count', 0)})"
            )
        elif res.get("status") == "ERROR":
            error_msg = res.get("message", "Unknown error")
            st.warning(f"Could not check validity: {error_msg}")
        else:
            st.warning("Could not check validity.")

        if "messages" in res:
            with st.expander("See full W3C Validator messages"):
                st.json(res["messages"])

    @staticmethod
    def _render_accessibility_tab(data: Dict):
        """Render the accessibility tab."""
        acc_data = data.get("accessibility", {})
        issues = acc_data.get("issues", [])
        error_count = acc_data.get("error_count", 0)
        warning_count = acc_data.get("warning_count", 0)

        if acc_data.get("status") == "PASS":
            st.success("No accessibility issues found.")
        elif acc_data.get("status") == "ERROR":
            st.warning(acc_data.get("message", "Unknown error"))
        else:
            st.error(f"Found {error_count} errors, {warning_count} warnings.")

            for issue in issues:
                severity = issue.get("severity", "error")
                wcag = issue.get("wcag", "")
                message = issue.get("message", "Unknown issue")
                element = issue.get("element")

                display_text = f"**[{wcag}]** {message}"
                if element:
                    display_text += f"\n\n`{element}`"

                if severity == "error":
                    st.error(display_text)
                else:
                    st.warning(display_text)

    @staticmethod
    def _render_jsonld_tab(data: Dict):
        """Render the JSON-LD tab."""
        meta = data.get("metadata", {})
        if "error" in meta:
            st.error("Cannot show JSON-LD - metadata fetch failed.")
            return
        json_ld = meta.get("json_ld", [])
        if json_ld:
            st.success(f"Found {len(json_ld)} items")
            st.json(json_ld)
        else:
            st.warning("No JSON-LD found")

    @staticmethod
    def _render_social_preview_tab(data: Dict):
        """Render the social media preview tab."""
        st.subheader("OpenGraph Preview")
        meta = data.get("metadata", {})
        if "error" in meta:
            st.error("Cannot show preview - metadata fetch failed.")
            return
        og_data = meta.get("open_graph", {}).get("found", {})

        og_image = og_data.get("og:image")
        og_title = og_data.get("og:title", "No Title")
        og_desc = og_data.get("og:description", "")
        og_url_host = (
            og_data.get("og:url", "").split("//")[-1].split("/")[0]
            if og_data.get("og:url")
            else ""
        )

        if og_image:
            card_html = f"""
            <div style="border: 1px solid #e1e8ed; border-radius: 12px; overflow: hidden; max-width: 600px; background-color: white; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                <div style="width: 100%; height: 260px; background-image: url('{og_image}'); background-size: cover; background-position: center; background-color: #f5f8fa;"></div>
                <div style="padding: 12px;">
                    <div style="font-size: 0.9em; color: #536471; text-transform: uppercase; margin-bottom: 4px;">{og_url_host}</div>
                    <div style="font-size: 1.1em; font-weight: bold; color: #0f1419; margin-bottom: 4px; line-height: 1.3;">{og_title}</div>
                    <div style="font-size: 0.95em; color: #536471; line-height: 1.3;">{og_desc or ""}</div>
                </div>
            </div>
            """
            st.markdown(card_html, unsafe_allow_html=True)
        else:
            st.info("No og:image found to generate preview.")


def main():
    """Main entry point for the dashboard."""
    st.set_page_config(page_title="EHRI Metadata Validator", layout="wide")
    AppState.init()
    SidebarUI.render()
    MainUI.render()


if __name__ == "__main__":
    main()
