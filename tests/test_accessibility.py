"""
Test cases for the accessibility module.

Tests cover WCAG-based accessibility checks:
- 3.1.1 H57: Document language
- 1.1.1 H37: Image alt text
- 1.3.1 H44/ARIA16: Input labels
- 1.1.1 & 2.4.4: Button content
- 2.4.4 G91/H30: Link content
- 1.3.1 H42: Heading structure
- 1.3.1 H51: Table headers
"""

from ehri_metadata_check.accessibility import check_accessibility


# --- Helper to run check and find specific issue types ---


def get_issues_by_type(html: str, issue_type: str) -> list:
    """Helper to run accessibility check and filter issues by type."""
    result = check_accessibility(html)
    return [i for i in result["issues"] if i["type"] == issue_type]


# --- Document Language (3.1.1 H57) ---


class TestDocumentLanguage:
    """Tests for HTML lang attribute check."""

    def test_lang_present(self):
        """HTML with lang attribute should pass."""
        html = '<html lang="en"><body></body></html>'
        issues = get_issues_by_type(html, "missing_lang")
        assert len(issues) == 0

    def test_lang_missing(self):
        """HTML without lang attribute should fail."""
        html = "<html><body></body></html>"
        issues = get_issues_by_type(html, "missing_lang")
        assert len(issues) == 1
        assert issues[0]["wcag"] == "3.1.1 H57"
        assert issues[0]["severity"] == "error"

    def test_empty_html(self):
        """Empty HTML should report missing lang."""
        html = ""
        issues = get_issues_by_type(html, "missing_lang")
        assert len(issues) == 1


# --- Image Alt Text (1.1.1 H37) ---


class TestImageAlt:
    """Tests for image alt attribute check."""

    def test_image_with_alt(self):
        """Image with alt attribute should pass."""
        html = (
            '<html lang="en"><body><img src="test.jpg" alt="Test image"></body></html>'
        )
        issues = get_issues_by_type(html, "image_alt_missing")
        assert len(issues) == 0

    def test_image_with_empty_alt(self):
        """Image with empty alt (decorative) should pass."""
        html = '<html lang="en"><body><img src="decoration.jpg" alt=""></body></html>'
        issues = get_issues_by_type(html, "image_alt_missing")
        assert len(issues) == 0

    def test_image_without_alt(self):
        """Image without alt attribute should fail."""
        html = '<html lang="en"><body><img src="test.jpg"></body></html>'
        issues = get_issues_by_type(html, "image_alt_missing")
        assert len(issues) == 1
        assert issues[0]["wcag"] == "1.1.1 H37"
        assert issues[0]["severity"] == "error"

    def test_multiple_images_mixed(self):
        """Multiple images with some missing alt."""
        html = """
        <html lang="en">
        <body>
            <img src="a.jpg" alt="Image A">
            <img src="b.jpg">
            <img src="c.jpg">
            <img src="d.jpg" alt="Image D">
        </body>
        </html>
        """
        issues = get_issues_by_type(html, "image_alt_missing")
        assert len(issues) == 2


# --- Input Labels (1.3.1 H44/ARIA16) ---


class TestInputLabels:
    """Tests for input element label checks."""

    def test_input_with_label_for(self):
        """Input with associated label should pass."""
        html = """
        <html lang="en">
        <body>
            <label for="name">Name</label>
            <input type="text" id="name">
        </body>
        </html>
        """
        issues = get_issues_by_type(html, "input_missing_label")
        assert len(issues) == 0

    def test_input_with_aria_label(self):
        """Input with aria-label should pass."""
        html = '<html lang="en"><body><input type="text" aria-label="Search"></body></html>'
        issues = get_issues_by_type(html, "input_missing_label")
        assert len(issues) == 0

    def test_input_with_aria_labelledby(self):
        """Input with aria-labelledby should pass."""
        html = """
        <html lang="en">
        <body>
            <span id="label1">Enter name</span>
            <input type="text" aria-labelledby="label1">
        </body>
        </html>
        """
        issues = get_issues_by_type(html, "input_missing_label")
        assert len(issues) == 0

    def test_input_with_title(self):
        """Input with title should pass."""
        html = '<html lang="en"><body><input type="text" title="Search field"></body></html>'
        issues = get_issues_by_type(html, "input_missing_label")
        assert len(issues) == 0

    def test_input_without_label(self):
        """Input without any label should fail."""
        html = '<html lang="en"><body><input type="text"></body></html>'
        issues = get_issues_by_type(html, "input_missing_label")
        assert len(issues) == 1
        assert issues[0]["wcag"] == "1.3.1 H44/ARIA16"

    def test_hidden_input_ignored(self):
        """Hidden inputs should be ignored."""
        html = '<html lang="en"><body><input type="hidden" name="token" value="abc"></body></html>'
        issues = get_issues_by_type(html, "input_missing_label")
        assert len(issues) == 0

    def test_submit_button_ignored_in_input_check(self):
        """Submit buttons checked separately, not as inputs."""
        html = '<html lang="en"><body><input type="submit"></body></html>'
        issues = get_issues_by_type(html, "input_missing_label")
        assert len(issues) == 0  # Checked as button, not as regular input


class TestSelectLabels:
    """Tests for select element label checks."""

    def test_select_with_label(self):
        """Select with label should pass."""
        html = """
        <html lang="en">
        <body>
            <label for="country">Country</label>
            <select id="country"><option>USA</option></select>
        </body>
        </html>
        """
        issues = get_issues_by_type(html, "select_missing_label")
        assert len(issues) == 0

    def test_select_without_label(self):
        """Select without label should fail."""
        html = (
            '<html lang="en"><body><select><option>USA</option></select></body></html>'
        )
        issues = get_issues_by_type(html, "select_missing_label")
        assert len(issues) == 1


class TestTextareaLabels:
    """Tests for textarea element label checks."""

    def test_textarea_with_label(self):
        """Textarea with label should pass."""
        html = """
        <html lang="en">
        <body>
            <label for="msg">Message</label>
            <textarea id="msg"></textarea>
        </body>
        </html>
        """
        issues = get_issues_by_type(html, "textarea_missing_label")
        assert len(issues) == 0

    def test_textarea_without_label(self):
        """Textarea without label should fail."""
        html = '<html lang="en"><body><textarea></textarea></body></html>'
        issues = get_issues_by_type(html, "textarea_missing_label")
        assert len(issues) == 1


# --- Button Content (1.1.1 & 2.4.4) ---


class TestButtonContent:
    """Tests for button accessible name checks."""

    def test_button_with_text(self):
        """Button with text content should pass."""
        html = '<html lang="en"><body><button>Submit</button></body></html>'
        issues = get_issues_by_type(html, "empty_button")
        assert len(issues) == 0

    def test_button_with_aria_label(self):
        """Button with aria-label should pass."""
        html = (
            '<html lang="en"><body><button aria-label="Close"></button></body></html>'
        )
        issues = get_issues_by_type(html, "empty_button")
        assert len(issues) == 0

    def test_button_with_title(self):
        """Button with title should pass."""
        html = (
            '<html lang="en"><body><button title="Close dialog"></button></body></html>'
        )
        issues = get_issues_by_type(html, "empty_button")
        assert len(issues) == 0

    def test_button_with_image(self):
        """Button with image with alt should pass."""
        html = '<html lang="en"><body><button><img src="icon.png" alt="Close"></button></body></html>'
        issues = get_issues_by_type(html, "empty_button")
        assert len(issues) == 0

    def test_empty_button(self):
        """Empty button should fail."""
        html = '<html lang="en"><body><button></button></body></html>'
        issues = get_issues_by_type(html, "empty_button")
        assert len(issues) == 1
        assert issues[0]["wcag"] == "1.1.1 & 2.4.4"

    def test_button_with_only_whitespace(self):
        """Button with only whitespace should fail."""
        html = '<html lang="en"><body><button>   </button></body></html>'
        issues = get_issues_by_type(html, "empty_button")
        assert len(issues) == 1


class TestInputButtonContent:
    """Tests for input type=submit/button/reset."""

    def test_submit_with_value(self):
        """Input submit with value should pass."""
        html = '<html lang="en"><body><input type="submit" value="Send"></body></html>'
        issues = get_issues_by_type(html, "empty_input_button")
        assert len(issues) == 0

    def test_submit_without_value(self):
        """Input submit without value should fail."""
        html = '<html lang="en"><body><input type="submit"></body></html>'
        issues = get_issues_by_type(html, "empty_input_button")
        assert len(issues) == 1

    def test_button_input_with_aria_label(self):
        """Input button with aria-label should pass."""
        html = '<html lang="en"><body><input type="button" aria-label="Action"></body></html>'
        issues = get_issues_by_type(html, "empty_input_button")
        assert len(issues) == 0

    def test_reset_without_value(self):
        """Input reset without value should fail."""
        html = '<html lang="en"><body><input type="reset"></body></html>'
        issues = get_issues_by_type(html, "empty_input_button")
        assert len(issues) == 1


# --- Link Content (2.4.4 G91/H30) ---


class TestLinkContent:
    """Tests for link accessible name checks."""

    def test_link_with_text(self):
        """Link with text content should pass."""
        html = '<html lang="en"><body><a href="/">Home</a></body></html>'
        issues = get_issues_by_type(html, "empty_link")
        assert len(issues) == 0

    def test_link_with_aria_label(self):
        """Link with aria-label should pass."""
        html = (
            '<html lang="en"><body><a href="/" aria-label="Go home"></a></body></html>'
        )
        issues = get_issues_by_type(html, "empty_link")
        assert len(issues) == 0

    def test_link_with_image(self):
        """Link with image with alt should pass."""
        html = '<html lang="en"><body><a href="/"><img src="home.png" alt="Home"></a></body></html>'
        issues = get_issues_by_type(html, "empty_link")
        assert len(issues) == 0

    def test_empty_link(self):
        """Empty link should fail."""
        html = '<html lang="en"><body><a href="/"></a></body></html>'
        issues = get_issues_by_type(html, "empty_link")
        assert len(issues) == 1
        assert issues[0]["wcag"] == "2.4.4 G91/H30"

    def test_link_with_only_whitespace(self):
        """Link with only whitespace should fail."""
        html = '<html lang="en"><body><a href="/">   </a></body></html>'
        issues = get_issues_by_type(html, "empty_link")
        assert len(issues) == 1

    def test_anchor_without_href_ignored(self):
        """Anchor without href (not a link) should be ignored."""
        html = '<html lang="en"><body><a name="section1"></a></body></html>'
        issues = get_issues_by_type(html, "empty_link")
        assert len(issues) == 0


# --- Heading Structure (1.3.1 H42) ---


class TestHeadingStructure:
    """Tests for heading structure checks."""

    def test_single_h1(self):
        """Page with single H1 should pass."""
        html = '<html lang="en"><body><h1>Title</h1><h2>Subtitle</h2></body></html>'
        issues = get_issues_by_type(html, "missing_h1")
        assert len(issues) == 0
        issues = get_issues_by_type(html, "multiple_h1")
        assert len(issues) == 0

    def test_missing_h1(self):
        """Page without H1 should warn."""
        html = '<html lang="en"><body><h2>Subtitle</h2></body></html>'
        issues = get_issues_by_type(html, "missing_h1")
        assert len(issues) == 1
        assert issues[0]["severity"] == "warning"

    def test_multiple_h1(self):
        """Page with multiple H1s should warn."""
        html = '<html lang="en"><body><h1>Title 1</h1><h1>Title 2</h1></body></html>'
        issues = get_issues_by_type(html, "multiple_h1")
        assert len(issues) == 1
        assert issues[0]["severity"] == "warning"

    def test_heading_skip(self):
        """Skipped heading levels should warn."""
        html = '<html lang="en"><body><h1>Title</h1><h3>Skip H2</h3></body></html>'
        issues = get_issues_by_type(html, "heading_skip")
        assert len(issues) == 1
        assert "H1 to H3" in issues[0]["message"]

    def test_heading_order_correct(self):
        """Proper heading order should pass."""
        html = """
        <html lang="en">
        <body>
            <h1>Title</h1>
            <h2>Section 1</h2>
            <h3>Subsection</h3>
            <h2>Section 2</h2>
        </body>
        </html>
        """
        issues = get_issues_by_type(html, "heading_skip")
        assert len(issues) == 0

    def test_multiple_heading_skips(self):
        """Multiple heading level skips should all be reported."""
        html = """
        <html lang="en">
        <body>
            <h1>Title</h1>
            <h3>Skip 1</h3>
            <h6>Skip 2</h6>
        </body>
        </html>
        """
        issues = get_issues_by_type(html, "heading_skip")
        assert len(issues) == 2


# --- Table Headers (1.3.1 H51) ---


class TestTableHeaders:
    """Tests for table header checks."""

    def test_table_with_headers(self):
        """Table with th elements should pass."""
        html = """
        <html lang="en">
        <body>
            <table>
                <tr><th>Name</th><th>Age</th></tr>
                <tr><td>Alice</td><td>30</td></tr>
            </table>
        </body>
        </html>
        """
        issues = get_issues_by_type(html, "table_missing_headers")
        assert len(issues) == 0

    def test_table_without_headers(self):
        """Table without th elements should warn."""
        html = """
        <html lang="en">
        <body>
            <table>
                <tr><td>Alice</td><td>30</td></tr>
            </table>
        </body>
        </html>
        """
        issues = get_issues_by_type(html, "table_missing_headers")
        assert len(issues) == 1
        assert issues[0]["severity"] == "warning"

    def test_multiple_tables_mixed(self):
        """Multiple tables with some missing headers."""
        html = """
        <html lang="en">
        <body>
            <table><tr><th>Header</th></tr><tr><td>Data</td></tr></table>
            <table><tr><td>No header</td></tr></table>
            <table><tr><td>Also no header</td></tr></table>
        </body>
        </html>
        """
        issues = get_issues_by_type(html, "table_missing_headers")
        assert len(issues) == 2


# --- Result Structure ---


class TestResultStructure:
    """Tests for the result dictionary structure."""

    def test_result_structure_pass(self):
        """Verify result structure when all checks pass."""
        html = """
        <html lang="en">
        <body>
            <h1>Title</h1>
            <p>Content</p>
        </body>
        </html>
        """
        result = check_accessibility(html)

        assert "status" in result
        assert "error_count" in result
        assert "warning_count" in result
        assert "issues" in result
        assert "message" in result

        assert result["status"] == "PASS"
        assert result["error_count"] == 0
        assert isinstance(result["issues"], list)

    def test_result_structure_fail(self):
        """Verify result structure when checks fail."""
        html = "<html><body><img src='x.jpg'></body></html>"
        result = check_accessibility(html)

        assert result["status"] == "FAIL"
        assert result["error_count"] > 0
        assert len(result["issues"]) > 0

    def test_issue_structure(self):
        """Verify individual issue structure."""
        html = "<html><body></body></html>"  # Missing lang
        result = check_accessibility(html)
        issue = result["issues"][0]

        assert "wcag" in issue
        assert "type" in issue
        assert "severity" in issue
        assert "message" in issue


# --- Integration Tests ---


class TestIntegration:
    """Integration tests with complete HTML documents."""

    def test_accessible_page(self):
        """A well-structured accessible page should have minimal issues."""
        html = """
        <!DOCTYPE html>
        <html lang="en">
        <head><title>Accessible Page</title></head>
        <body>
            <h1>Welcome</h1>
            <nav>
                <a href="/">Home</a>
                <a href="/about">About</a>
            </nav>
            <main>
                <h2>Content</h2>
                <p>Some text.</p>
                <img src="photo.jpg" alt="A descriptive photo">
                <form>
                    <label for="email">Email</label>
                    <input type="email" id="email">
                    <button type="submit">Subscribe</button>
                </form>
            </main>
        </body>
        </html>
        """
        result = check_accessibility(html)
        assert result["status"] == "PASS"
        assert result["error_count"] == 0

    def test_inaccessible_page(self):
        """A poorly structured page should have multiple issues."""
        html = """
        <html>
        <body>
            <h3>Skipped headings</h3>
            <img src="a.jpg">
            <a href="/"></a>
            <button></button>
            <input type="text">
            <table><tr><td>No headers</td></tr></table>
        </body>
        </html>
        """
        result = check_accessibility(html)
        assert result["status"] == "FAIL"
        assert (
            result["error_count"] >= 4
        )  # lang, img alt, empty link, empty button, input label
        assert result["warning_count"] >= 2  # missing h1, table headers
