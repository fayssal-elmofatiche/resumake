"""resumake web — Launch the interactive web frontend."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Annotated

import typer


def web(
    project: Annotated[
        str,
        typer.Argument(help="Path to the resumake project directory (containing cv.yaml)."),
    ] = ".",
    port: Annotated[int, typer.Option(help="Server port.")] = 3000,
    host: Annotated[str, typer.Option(help="Server host.")] = "127.0.0.1",
    no_open: Annotated[bool, typer.Option("--no-open", help="Don't open browser automatically.")] = False,
):
    """Launch the interactive web frontend for editing and previewing your CV."""
    import uvicorn

    project_dir = Path(project).resolve()
    if not project_dir.is_dir():
        project_dir.mkdir(parents=True, exist_ok=True)
        typer.echo(f"Created project directory: {project_dir}")

    # Ensure the web package is importable
    repo_root = Path(__file__).resolve().parent.parent
    web_dir = repo_root / "web"
    if not web_dir.is_dir():
        typer.echo("Error: web/ directory not found. Is resumake installed correctly?", err=True)
        raise typer.Exit(1)

    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    os.chdir(project_dir)
    url = f"http://{host}:{port}"
    typer.echo(f"Project directory: {project_dir}")
    typer.echo(f"Starting server at {url}")
    typer.echo(f"API docs at {url}/api/docs")

    if not no_open:
        import threading
        import webbrowser
        threading.Timer(1.0, webbrowser.open, args=[url]).start()

    from web.server import app as web_app

    uvicorn.run(web_app, host=host, port=port)
