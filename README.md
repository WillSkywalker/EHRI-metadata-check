# EHRI Metadata Check

[![Test Matrix](https://github.com/WillSkywalker/EHRI-metadata-check/actions/workflows/test.yaml/badge.svg)](https://github.com/WillSkywalker/EHRI-metadata-check/actions/workflows/test.yaml)
A tool for validating whether EHRI websites have correct metadata, accessibility compliance, and OpenGraph information.

## Installation

```bash
# Clone the repository
git clone https://github.com/EHRI/EHRI-metadata-check.git
cd EHRI-metadata-check

# Install with uv
uv sync
```

## Usage

### Import in your project

```python

# Check the accessability of a HTML file
from ehri_metadata_check.accessibility import check_accessibility
results = await check_accessibility(html_content: str)

# Validate a single URL
from ehri_metadata_check.validation import validate_url
result = await validate_url(url: str)

# Validate multiple URLs
from ehri_metadata_check.validation import validate_url
results = await validate_urls([url1, url2, url3])
```

### Streamlit Dashboard

```bash
uv run streamlit run src/ehri_metadata_check/dashboard.py
```

## License

Apache-2.0
