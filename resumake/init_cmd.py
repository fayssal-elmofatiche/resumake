"""Init command — scaffold a new resumake project."""

import shutil
from pathlib import Path
from typing import Annotated, Optional

import typer

from .console import console
from .utils import PACKAGE_DIR, BUILTIN_ASSETS_DIR


TEMPLATES_DIR = PACKAGE_DIR / "templates"


def init(
    directory: Annotated[Optional[Path], typer.Argument(help="Directory to initialize. Defaults to current directory.")] = None,
):
    """Scaffold a new resumake project with an example CV and assets."""
    target = (directory or Path.cwd()).resolve()
    target.mkdir(parents=True, exist_ok=True)

    # Copy example CV
    example_src = TEMPLATES_DIR / "cv.example.yaml"
    cv_dest = target / "cv.yaml"
    if cv_dest.exists():
        console.print(f"[yellow]Skipping:[/] {cv_dest} already exists.")
    else:
        shutil.copy2(str(example_src), str(cv_dest))
        console.print(f"[green]Created:[/] {cv_dest}")

    # Copy built-in icons to assets/
    assets_dest = target / "assets"
    assets_dest.mkdir(parents=True, exist_ok=True)
    if BUILTIN_ASSETS_DIR.exists():
        for icon in BUILTIN_ASSETS_DIR.glob("*.png"):
            dest = assets_dest / icon.name
            if not dest.exists():
                shutil.copy2(str(icon), str(dest))
        console.print(f"[green]Copied icons to:[/] {assets_dest}")

    # Create output/ and .gitignore
    output_dir = target / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    gitignore = target / ".gitignore"
    if not gitignore.exists():
        gitignore.write_text(
            "output/\n"
            "assets/profile.*\n"
            ".venv/\n"
            "__pycache__/\n"
            "*.pyc\n"
        )
        console.print(f"[green]Created:[/] {gitignore}")

    console.print(f"\n[bold]Project ready at {target}[/]")
    console.print("Next steps:")
    console.print("  1. Edit [cyan]cv.yaml[/] with your information")
    console.print("  2. (Optional) Add [cyan]assets/profile.jpeg[/] for your photo")
    console.print("  3. Run: [bold]resumake build[/]")
