"""Preview command — generate HTML and open in browser."""

import tempfile
from pathlib import Path
from typing import Annotated

import typer

from .console import console
from .export_cmd import _cv_to_html
from .utils import DEFAULT_YAML, load_cv, open_file


def preview(
    source: Annotated[Path, typer.Option(help="Path to source YAML.")] = DEFAULT_YAML,
):
    """Generate an HTML preview of your CV and open it in the browser."""
    cv = load_cv(source)
    html = _cv_to_html(cv)

    preview_path = Path(tempfile.mktemp(suffix=".html", prefix="resumake_preview_"))
    preview_path.write_text(html, encoding="utf-8")
    console.print(f"Preview: [cyan]{preview_path}[/]")
    open_file(preview_path)
