"""Shared Rich console for consistent styled output."""

from rich.console import Console

console = Console()
err_console = Console(stderr=True)
