import streamlit as st
from ehri_metadata_check.metadata import get_metadata_results
from ehri_metadata_check.html_validity import check_html_validity
from ehri_metadata_check.accessibility import check_accessibility

st.set_page_config(page_title="EHRI Metadata Validator", layout="wide")

# Initialize session state
if "validated_urls" not in st.session_state:
    st.session_state.validated_urls = {}  # URL -> Results
if "selected_url" not in st.session_state:
    st.session_state.selected_url = None

# Sidebar mostly for info or settings if needed
with st.sidebar:
    st.image(
        "https://portal.ehri-project.eu/assets/ehri-logo-8a6e4e8357f07755866782250269f8c6bcecf39775924769994270275529f796.png",
        width=200,
    )
    st.header("EHRI Validator")
    st.markdown("Validate metadata, HTML5 compliance, and basic accessibility.")

    st.subheader("Premade Examples")
    examples = [
        "https://blog.ehri-project.eu",
        "https://training.ehri-project.eu",
        "https://begrenzte-flucht.ehri-project.eu",
        "https://diplomatic-reports.ehri-project.eu",
        "https://early-testimony.ehri-project.eu",
        "https://the-sunflower.ehri-project.eu",
        "https://documentation-campaign.ehri-project.eu",
        "https://nisko-transports.ehri-project.eu",
        "https://ehri-nl.org",
        "https://ehri-kg.ehri-project.eu",
    ]

    selected_example = st.selectbox("Choose an example", [""] + examples)
    if st.button("Add Example"):
        if selected_example and selected_example not in st.session_state.validated_urls:
            st.session_state.url_input = (
                selected_example  # Hint for main input or just add directly
            )
            # Better UI: just populate the main input
            pass

st.title("🔍 Website Metadata Validator")

# Input Section
col1, col2 = st.columns([3, 1])
with col1:
    new_url = st.text_input(
        "Enter URL to validate",
        key="url_input",
        value=selected_example if selected_example else "",
    )
with col2:
    validate_btn = st.button("Validate", type="primary", use_container_width=True)

if validate_btn and new_url:
    if new_url not in st.session_state.validated_urls:
        with st.spinner(f"Validating {new_url}..."):
            try:
                # 1. Metadata
                meta_res = get_metadata_results(new_url)

                # 2. HTML Validity & Accessibility (Need response content again or reuse from meta_res if refactor allowed)
                # Current design: simple fetch again or hacky grab from meta_res if I stored response object (I did!)
                # Warning: Response object usage requires handling potential errors if meta_res failed

                results = {"metadata": meta_res}

                if (
                    "error" not in meta_res
                    and "response" in meta_res
                    and meta_res["response"]
                ):
                    resp = meta_res["response"]
                    html_text = resp.text

                    # 2. HTML5
                    with st.status("Checking HTML5 Validity...", expanded=False):
                        results["html_validity"] = check_html_validity(html_text)

                    # 3. Accessibility
                    with st.status("Checking Accessibility...", expanded=False):
                        results["accessibility"] = check_accessibility(html_text)
                else:
                    results["html_validity"] = {
                        "status": "ERROR",
                        "message": "Could not fetch content for validation",
                    }
                    results["accessibility"] = {
                        "status": "ERROR",
                        "issues": [],
                        "message": "Could not fetch content for validation",
                    }

                st.session_state.validated_urls[new_url] = results
                st.session_state.selected_url = new_url  # Auto-select new result
                st.success(f"Validated {new_url}")
            except Exception as e:
                st.error(f"Error validating {new_url}: {e}")
    else:
        st.session_state.selected_url = new_url
        st.info("URL already validated. Showing results.")


# Main Layout: List vs Details
st.divider()

# List of inspected URLs
if st.session_state.validated_urls:
    st.subheader("Inspected URLs")

    # Create a nice clickable list using columns or just buttons
    cols = st.columns(4)
    for i, url in enumerate(st.session_state.validated_urls.keys()):
        with cols[i % 4]:
            if st.button(f"📄 {url.replace('https://', '')}", key=f"btn_{url}"):
                st.session_state.selected_url = url

# Details View
if st.session_state.selected_url:
    url = st.session_state.selected_url
    data = st.session_state.validated_urls[url]

    st.markdown(f"## Results for `{url}`")

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
        st.subheader("HTML Lang")
        lang = data["metadata"]["html_lang"]
        if lang["status"] == "PASS":
            st.success(f"{lang['message']}")
        else:
            st.error(f"{lang['message']}")

        st.subheader("Meta Tags")
        for tag in data["metadata"]["meta_tags"]:
            if tag["status"] == "PASS":
                st.success(f"**{tag['tag']}**: {tag['content']}")
            else:
                st.error(f"**{tag['tag']}**: Missing")

        st.subheader("Open Graph")
        og = data["metadata"]["open_graph"]
        if og["status"] == "PASS":
            st.success("All required OG tags found")
        else:
            st.error(f"Missing OG tags: {', '.join(og['missing'])}")

        st.json(og["found"])

    with tab2:
        res = data.get("html_validity", {})
        if res.get("status") == "PASS":
            st.success(
                f"Pass! (Errors: {res.get('error_count', 0)}, Warnings: {res.get('warning_count', 0)})"
            )
        elif res.get("status") == "FAIL":
            st.error(
                f"Fail! (Errors: {res.get('error_count', 0)}, Warnings: {res.get('warning_count', 0)})"
            )
        else:
            st.warning("Could not check validity.")

        if "messages" in res:
            with st.expander("See full W3C Validator messages"):
                st.json(res["messages"])

    with tab3:
        acc_data = data.get("accessibility", {})
        issues = acc_data.get("issues", [])

        if acc_data.get("status") == "PASS":
            st.success("No basic accessibility issues found (Alt tags, buttons).")
        elif acc_data.get("status") == "ERROR":
            st.warning(acc_data.get("message", "Unknown error"))
        else:
            st.error(f"Found {len(issues)} potential issues.")
            for issue in issues:
                st.warning(f"**{issue['message']}**\n\n Element: `{issue['element']}`")

    with tab4:
        json_ld = data["metadata"].get("json_ld", [])
        if json_ld:
            st.success(f"Found {len(json_ld)} items")
            st.json(json_ld)
        else:
            st.warning("No JSON-LD found")

    with tab5:
        st.subheader("OpenGraph Preview")
        og_data = data["metadata"]["open_graph"]["found"]

        # Extract fields with defaults
        og_image = og_data.get("og:image")
        og_title = og_data.get("og:title", "No Title")
        og_desc = og_data.get("og:description", "")
        og_site = og_data.get("og:site_name", "")
        og_url_host = (
            og_data.get("og:url", "").split("//")[-1].split("/")[0]
            if og_data.get("og:url")
            else ""
        )

        if og_image:
            # Simple card styling
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
