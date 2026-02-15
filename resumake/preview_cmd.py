"""Preview command — generate HTML and open in browser, with optional live reload."""

import tempfile
from pathlib import Path
from typing import Annotated, Optional

import typer

from .console import console
from .html_builder import build_html
from .theme import load_theme
from .utils import DEFAULT_YAML, load_cv, open_file


def preview(
    source: Annotated[Path, typer.Option(help="Path to source YAML.")] = DEFAULT_YAML,
    theme: Annotated[Optional[str], typer.Option(help="Theme name or path to theme.yaml.")] = None,
    live: Annotated[bool, typer.Option("--live", help="Start a live-reloading preview server.")] = False,
    port: Annotated[int, typer.Option(help="Port for the live preview server.")] = 8642,
):
    """Generate an HTML preview of your CV and open it in the browser."""
    if live:
        from .live_server import start_live_server

        start_live_server(source, theme_name=theme, port=port)
    else:
        cv = load_cv(source)
        resolved_theme = load_theme(theme)
        html = build_html(cv, "en", theme=resolved_theme)

        preview_path = Path(tempfile.mktemp(suffix=".html", prefix="resumake_preview_"))
        preview_path.write_text(html, encoding="utf-8")
        console.print(f"Preview: [cyan]{preview_path}[/]")
        open_file(preview_path)
