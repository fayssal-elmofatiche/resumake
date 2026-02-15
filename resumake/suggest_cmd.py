"""Suggest command — AI-powered CV content improvement suggestions."""

import json
from pathlib import Path
from typing import Annotated, Optional

import typer
import yaml

from .console import console, err_console
from .utils import DEFAULT_YAML, load_cv


def suggest_improvements(cv: dict) -> dict:
    """Analyze CV via LLM and return improvement suggestions.

    Returns: {suggestions: [{section, original, suggested, reason}], general: [str]}
    """
    from .llm import get_provider, strip_yaml_fences

    try:
        provider = get_provider()
    except RuntimeError:
        err_console.print("[red]Error:[/] Content suggestions require an LLM provider.")
        err_console.print("Set ANTHROPIC_API_KEY or OPENAI_API_KEY.")
        raise SystemExit(1)

    cv_yaml = yaml.dump(cv, allow_unicode=True, default_flow_style=False, sort_keys=False)

    with console.status("Analyzing CV for improvements..."):
        response = provider.complete(
            "Analyze the following CV and suggest improvements. Focus on:\n"
            "1. Quantifying achievements (add numbers, percentages, metrics)\n"
            "2. Using stronger action verbs (led, architected, delivered vs worked on, helped)\n"
            "3. Removing vague language\n"
            "4. ATS readability improvements\n"
            "5. Any missing or weak sections\n\n"
            "Return ONLY valid JSON with this structure:\n"
            '{"suggestions": [{"section": "experience", "original": "original text", '
            '"suggested": "improved text", "reason": "why this is better"}], '
            '"general": ["general advice 1", "general advice 2"]}\n\n'
            f"CV:\n{cv_yaml}",
            max_tokens=4096,
        )

    # Parse JSON response
    clean = strip_yaml_fences(response).strip()
    try:
        return json.loads(clean)
    except json.JSONDecodeError:
        # Try to extract JSON from response
        start = clean.find("{")
        end = clean.rfind("}") + 1
        if start >= 0 and end > start:
            try:
                return json.loads(clean[start:end])
            except json.JSONDecodeError:
                pass
        return {"suggestions": [], "general": ["Could not parse LLM response. Try again."]}


def suggest(
    source: Annotated[Optional[Path], typer.Option(help="Path to source YAML.")] = None,
):
    """Analyze your CV and suggest improvements using AI."""
    source = source or DEFAULT_YAML
    cv = load_cv(source)
    result = suggest_improvements(cv)

    suggestions = result.get("suggestions", [])
    general = result.get("general", [])

    if suggestions:
        console.print(f"\n[bold]Specific Suggestions ({len(suggestions)}):[/]\n")
        for i, s in enumerate(suggestions, 1):
            console.print(f"  [bold cyan]{i}.[/] [{s.get('section', '')}]")
            if s.get("original"):
                console.print(f"     [red]- {s['original']}[/]")
            if s.get("suggested"):
                console.print(f"     [green]+ {s['suggested']}[/]")
            if s.get("reason"):
                console.print(f"     [dim]{s['reason']}[/]")
            console.print()

    if general:
        console.print("[bold]General Advice:[/]\n")
        for advice in general:
            console.print(f"  [dim]•[/] {advice}")
        console.print()

    if not suggestions and not general:
        console.print("[green]Your CV looks great! No suggestions at this time.[/]")
