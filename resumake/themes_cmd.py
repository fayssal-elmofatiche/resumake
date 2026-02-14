"""Themes command — list available themes with color previews."""

from rich.table import Table
from rich.text import Text

from .console import console
from .theme import list_themes, load_theme


def themes():
    """List available built-in themes."""
    names = list_themes()
    if not names:
        console.print("[yellow]No built-in themes found.[/]")
        return

    table = Table(title="Built-in Themes", show_lines=True)
    table.add_column("Theme", style="bold")
    table.add_column("Primary")
    table.add_column("Accent")
    table.add_column("Fonts")
    table.add_column("Layout")

    for name in names:
        t = load_theme(name)
        primary_swatch = Text(f"  #{t.colors.primary}  ", style=f"on #{t.colors.primary} bold white")
        accent_swatch = Text(f"  #{t.colors.accent}  ", style=f"on #{t.colors.accent} bold white")
        fonts = f"{t.fonts.heading} / {t.fonts.body}"
        layout = f"{t.layout.sidebar_width_cm}cm + {t.layout.main_width_cm}cm"
        label = f"{name} (default)" if name == "classic" else name
        table.add_row(label, primary_swatch, accent_swatch, fonts, layout)

    console.print(table)
    console.print("\nUsage: [bold]resumake build --theme <name>[/]")
    console.print("Custom: place a [cyan]theme.yaml[/] in your project directory.")
