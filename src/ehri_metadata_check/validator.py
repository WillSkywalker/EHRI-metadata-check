import typer
from rich.console import Console
import requests

app = typer.Typer()
console = Console()


@app.command()
def validate(
    urls: list[str] = typer.Argument(..., help="List of URLs to validate"),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose output"
    ),
):
    """
    Validate metadata for the given website URLs.
    """
    console.print(f"[bold blue]Starting validation for {len(urls)} URLs...[/bold blue]")

    for url in urls:
        console.print(f"\n[bold blue]{'=' * 60}[/bold blue]")
        console.print(f"[bold]Validating: {url}[/bold]")
        console.print(f"[bold blue]{'=' * 60}[/bold blue]")

        try:
            from ehri_metadata_check.metadata import get_metadata_results

            data = get_metadata_results(url)
            if "error" in data:
                console.print(f"[bold red]{data['error']}[/bold red]")
                continue

            # 1. HTML Lang
            lang_result = data["html_lang"]
            console.print(
                f"HTML Lang Check: [{'green' if lang_result['status'] == 'PASS' else 'red'}]{lang_result['status']}[/] - {lang_result['message']}"
            )

            # 2. Meta Tags
            console.print("\n[bold]Standard Meta Tags:[/bold]")
            for res in data["meta_tags"]:
                console.print(
                    f"  {res['tag']}: [{'green' if res['status'] == 'PASS' else 'red'}]{res['status']}[/] ({res.get('content') or 'N/A'})"
                )

            # 3. Open Graph
            console.print("\n[bold]Open Graph Metadata:[/bold]")
            og_result = data["open_graph"]
            console.print(
                f"  Status: [{'green' if og_result['status'] == 'PASS' else 'red'}]{og_result['status']}[/]"
            )
            if og_result["missing"]:
                console.print(f"  Missing: {', '.join(og_result['missing'])}")
            for prop, val in og_result["found"].items():
                console.print(f"  {prop}: {val}")

            # 4. JSON-LD
            console.print("\n[bold]JSON-LD Structured Data:[/bold]")
            if data["json_ld"]:
                console.print(f"  Found {len(data['json_ld'])} JSON-LD items.")
                for item in data["json_ld"]:
                    console.print(f"  - Type: {item.get('@type', 'Unknown')}")
            else:
                console.print("  [yellow]No JSON-LD found.[/yellow]")

            from ehri_metadata_check.html_validity import check_html_validity

            # Simple re-fetch for now to decouple checks
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                console.print("\n[bold]HTML5 Validity (W3C API):[/bold]")
                val_result = check_html_validity(response.text)
                status_color = "green" if val_result["status"] == "PASS" else "red"
                console.print(f"  Status: [{status_color}]{val_result['status']}[/]")
                if val_result.get("status") != "ERROR":
                    console.print(
                        f"  Errors: {val_result.get('error_count', 0)}, Warnings: {val_result.get('warning_count', 0)}"
                    )

            from ehri_metadata_check.accessibility import run_accessibility_checks

            run_accessibility_checks(response.text)
        except Exception as e:
            console.print(f"[bold red]An unexpected error occurred: {e}[/bold red]")
            if verbose:
                import traceback

                traceback.print_exc()


if __name__ == "__main__":
    app()
