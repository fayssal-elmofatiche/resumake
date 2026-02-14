"""CV translation from English to German via LLM."""

import yaml

from .console import console, err_console
from .llm import get_provider, strip_yaml_fences
from .utils import CACHE_FILE, OUTPUT_DIR, load_cv


def translate_cv(cv: dict, retranslate: bool = False) -> dict:
    """Translate CV content from English to German using an LLM.
    Uses cached translation if available, unless retranslate is True."""
    if not retranslate and CACHE_FILE.exists():
        console.print(f"[dim]Using cached translation from {CACHE_FILE}[/]")
        return load_cv(CACHE_FILE, validate=False)

    try:
        provider = get_provider()
    except RuntimeError:
        if CACHE_FILE.exists():
            console.print("[yellow]No LLM provider available — falling back to cached translation.[/]")
            return load_cv(CACHE_FILE, validate=False)
        err_console.print("[red]Error:[/] No LLM provider available and no cached translation found.")
        err_console.print("Set ANTHROPIC_API_KEY or install with: [bold]uv tool install resumake --with anthropic[/]")
        raise SystemExit(1)

    cv_yaml = yaml.dump(cv, allow_unicode=True, default_flow_style=False, sort_keys=False)

    with console.status("Translating CV to German via LLM..."):
        response = provider.complete(
            "Translate the following CV from English to German. "
            "Return ONLY the translated YAML — no explanation, no code fences. "
            "Keep the YAML structure and keys exactly the same (keys stay in English). "
            "Translate all values that are natural language text (descriptions, bullets, titles, skills, etc.). "
            "Do NOT translate: names, organization names, technology/tool names, URLs, email, phone, dates, "
            "publication titles, degree program names that are commonly kept in English. "
            "Use professional German suitable for a senior-level CV. "
            f"Here is the YAML:\n\n{cv_yaml}",
            max_tokens=8192,
        )

    translated_yaml = strip_yaml_fences(response)
    translated_cv = yaml.safe_load(translated_yaml)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        yaml.dump(translated_cv, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
    console.print(f"[dim]Cached translation to {CACHE_FILE}[/]")

    return translated_cv
