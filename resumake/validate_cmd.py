"""Validate command — check CV YAML against the schema."""

from pathlib import Path
from typing import Annotated

import typer

from .console import console, err_console
from .schema import validate_cv
from .utils import DEFAULT_YAML, load_cv


def validate(
    source: Annotated[Path, typer.Option(help="Path to source YAML.")] = DEFAULT_YAML,
):
    """Validate a CV YAML file against the schema."""
    if not source.exists():
        err_console.print(f"[red]Error:[/] File not found: {source}")
        raise typer.Exit(1)

    data = load_cv(source, validate=False)

    try:
        validate_cv(data)
        console.print(f"[green]Valid:[/] {source}")

        # Photo validation (warnings only)
        from .utils import validate_photo

        photo_ref = data.get("photo")
        if photo_ref:
            for w in validate_photo(photo_ref):
                console.print(f"  [yellow]Warning:[/] {w}")
    except Exception as e:
        err_console.print(f"[red]Validation errors in {source}:[/]\n")
        from pydantic import ValidationError

        if isinstance(e, ValidationError):
            for err in e.errors():
                loc = " -> ".join(str(x) for x in err["loc"])
                err_console.print(f"  [yellow]{loc}[/]: {err['msg']}")
        else:
            err_console.print(f"  {e}")
        raise typer.Exit(1)
