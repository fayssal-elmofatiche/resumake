"""Diff command — compare two CV YAML files."""

from pathlib import Path
from typing import Annotated

import typer
import yaml

from .console import console, err_console


def _flatten(data: dict, prefix: str = "") -> dict[str, str]:
    """Flatten a nested dict into dot-separated key-value pairs."""
    result = {}
    for key, value in data.items():
        full_key = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            result.update(_flatten(value, full_key))
        elif isinstance(value, list):
            for i, item in enumerate(value):
                if isinstance(item, dict):
                    # Use a readable label if available
                    label = item.get("title") or item.get("name") or item.get("label") or str(i)
                    result.update(_flatten(item, f"{full_key}[{label}]"))
                else:
                    result[f"{full_key}[{i}]"] = str(item)
        else:
            result[full_key] = str(value)
    return result


def diff(
    file_a: Annotated[Path, typer.Argument(help="First YAML file (e.g. original CV).")],
    file_b: Annotated[Path, typer.Argument(help="Second YAML file (e.g. tailored CV).")],
):
    """Compare two CV YAML files and show differences."""
    for f in (file_a, file_b):
        if not f.exists():
            err_console.print(f"[red]Error:[/] File not found: {f}")
            raise typer.Exit(1)

    with open(file_a, "r", encoding="utf-8") as f:
        data_a = yaml.safe_load(f)
    with open(file_b, "r", encoding="utf-8") as f:
        data_b = yaml.safe_load(f)

    flat_a = _flatten(data_a)
    flat_b = _flatten(data_b)
    all_keys = sorted(set(flat_a.keys()) | set(flat_b.keys()))

    added = []
    removed = []
    changed = []

    for key in all_keys:
        in_a = key in flat_a
        in_b = key in flat_b
        if in_a and not in_b:
            removed.append((key, flat_a[key]))
        elif not in_a and in_b:
            added.append((key, flat_b[key]))
        elif flat_a[key] != flat_b[key]:
            changed.append((key, flat_a[key], flat_b[key]))

    if not added and not removed and not changed:
        console.print("[green]No differences found.[/]")
        return

    console.print(f"\nComparing [cyan]{file_a}[/] -> [cyan]{file_b}[/]\n")

    if changed:
        console.print(f"[yellow]Changed ({len(changed)}):[/]")
        for key, old, new in changed:
            console.print(f"  [dim]{key}[/]")
            console.print(f"    [red]- {old}[/]")
            console.print(f"    [green]+ {new}[/]")
        console.print()

    if added:
        console.print(f"[green]Added ({len(added)}):[/]")
        for key, val in added:
            console.print(f"  [green]+ {key}: {val}[/]")
        console.print()

    if removed:
        console.print(f"[red]Removed ({len(removed)}):[/]")
        for key, val in removed:
            console.print(f"  [red]- {key}: {val}[/]")
