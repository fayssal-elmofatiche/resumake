"""Import command — convert external formats to resumake cv.yaml."""

import json
from pathlib import Path
from typing import Annotated, Optional

import typer
import yaml

from .console import console, err_console


def import_(
    format: Annotated[str, typer.Argument(help="Import format: jsonresume or linkedin.")],
    file: Annotated[Path, typer.Argument(help="Path to the source file.")],
    output: Annotated[
        Optional[Path], typer.Option("--output", "-o", help="Output YAML path. Defaults to cv.yaml.")
    ] = None,
):
    """Import a CV from an external format into resumake cv.yaml."""
    format = format.lower()

    if format == "jsonresume":
        _import_jsonresume(file, output)
    elif format == "linkedin":
        _import_linkedin(file, output)
    else:
        err_console.print(f"[red]Error:[/] Unknown import format '{format}'. Use: jsonresume or linkedin.")
        raise typer.Exit(1)


def _import_jsonresume(file: Path, output: Path | None):
    from .jsonresume import json_resume_to_cv, validate_json_resume

    if not file.exists():
        err_console.print(f"[red]Error:[/] File not found: {file}")
        raise typer.Exit(1)

    data = json.loads(file.read_text(encoding="utf-8"))
    issues = validate_json_resume(data)
    if issues:
        for issue in issues:
            err_console.print(f"[yellow]Warning:[/] {issue}")

    cv = json_resume_to_cv(data)
    out_path = output or Path("cv.yaml")
    out_path.write_text(yaml.dump(cv, allow_unicode=True, default_flow_style=False, sort_keys=False), encoding="utf-8")
    console.print(f"Imported: [cyan]{out_path}[/]")


def _import_linkedin(file: Path, output: Path | None):
    try:
        from .linkedin import import_linkedin
    except ImportError:
        err_console.print("[red]Error:[/] LinkedIn import requires 'pdfplumber'.")
        err_console.print("Install with: [bold]uv tool install resumakeai --with pdfplumber[/]")
        raise typer.Exit(1)

    if not file.exists():
        err_console.print(f"[red]Error:[/] File not found: {file}")
        raise typer.Exit(1)

    cv = import_linkedin(file)
    out_path = output or Path("cv.yaml")
    out_path.write_text(yaml.dump(cv, allow_unicode=True, default_flow_style=False, sort_keys=False), encoding="utf-8")
    console.print(f"Imported: [cyan]{out_path}[/]")
