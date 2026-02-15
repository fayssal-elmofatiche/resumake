"""ATS command — keyword match analysis between CV and a job description."""

import json
from pathlib import Path
from typing import Annotated, Optional

import typer
import yaml

from .console import console, err_console
from .utils import DEFAULT_YAML, load_cv


def analyze_ats_match(cv: dict, job_description: str) -> dict:
    """Analyze keyword match between CV and job description via LLM.

    Returns: {score: int, matched_keywords: [str], missing_keywords: [str],
              suggestions: [{keyword, where_to_add, phrasing}], summary: str}
    """
    from .llm import get_provider, strip_yaml_fences

    try:
        provider = get_provider()
    except RuntimeError:
        err_console.print("[red]Error:[/] ATS analysis requires an LLM provider.")
        err_console.print("Set ANTHROPIC_API_KEY or OPENAI_API_KEY.")
        raise SystemExit(1)

    cv_yaml = yaml.dump(cv, allow_unicode=True, default_flow_style=False, sort_keys=False)

    with console.status("Analyzing ATS keyword match..."):
        response = provider.complete(
            "Compare the following CV with the job description. Analyze keyword matching "
            "for Applicant Tracking Systems (ATS). Return ONLY valid JSON with:\n"
            '{"score": 0-100, '
            '"matched_keywords": ["keyword1", "keyword2"], '
            '"missing_keywords": ["keyword3", "keyword4"], '
            '"suggestions": [{"keyword": "keyword", "where_to_add": "section name", '
            '"phrasing": "suggested phrasing"}], '
            '"summary": "brief summary of match quality"}\n\n'
            f"Job Description:\n{job_description}\n\n"
            f"CV:\n{cv_yaml}",
            max_tokens=4096,
        )

    clean = strip_yaml_fences(response).strip()
    try:
        return json.loads(clean)
    except json.JSONDecodeError:
        start = clean.find("{")
        end = clean.rfind("}") + 1
        if start >= 0 and end > start:
            try:
                return json.loads(clean[start:end])
            except json.JSONDecodeError:
                pass
        return {
            "score": 0,
            "matched_keywords": [],
            "missing_keywords": [],
            "suggestions": [],
            "summary": "Could not parse analysis. Try again.",
        }


def ats(
    description_file: Annotated[Path, typer.Argument(help="Path to job description text file.")],
    source: Annotated[Optional[Path], typer.Option(help="Path to source YAML.")] = None,
):
    """Analyze ATS keyword match between your CV and a job description."""
    source = source or DEFAULT_YAML

    if not description_file.exists():
        err_console.print(f"[red]Error:[/] File not found: {description_file}")
        raise typer.Exit(1)

    job_text = description_file.read_text(encoding="utf-8").strip()
    if not job_text:
        err_console.print("[red]Error:[/] Job description file is empty.")
        raise typer.Exit(1)

    cv = load_cv(source)
    result = analyze_ats_match(cv, job_text)

    score = result.get("score", 0)
    # Color-coded score
    if score >= 80:
        color = "green"
    elif score >= 60:
        color = "yellow"
    else:
        color = "red"

    console.print(f"\n[bold]ATS Match Score:[/] [{color}]{score}/100[/]")
    console.print()

    matched = result.get("matched_keywords", [])
    if matched:
        console.print(f"[bold green]Matched Keywords ({len(matched)}):[/]")
        console.print(f"  {', '.join(matched)}")
        console.print()

    missing = result.get("missing_keywords", [])
    if missing:
        console.print(f"[bold red]Missing Keywords ({len(missing)}):[/]")
        console.print(f"  {', '.join(missing)}")
        console.print()

    suggestions = result.get("suggestions", [])
    if suggestions:
        console.print(f"[bold]Suggestions ({len(suggestions)}):[/]")
        for s in suggestions:
            console.print(f"  [cyan]{s.get('keyword', '')}[/] → {s.get('where_to_add', '')}")
            if s.get("phrasing"):
                console.print(f"    [dim]{s['phrasing']}[/]")
        console.print()

    summary = result.get("summary", "")
    if summary:
        console.print(f"[dim]{summary}[/]")
