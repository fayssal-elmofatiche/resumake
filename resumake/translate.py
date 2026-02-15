"""CV translation via LLM — supports any target language."""

import hashlib

import yaml

from .console import console, err_console
from .llm import get_provider, strip_yaml_fences
from .utils import LABELS, OUTPUT_DIR, cache_file_for, load_cv


def _source_hash(cv: dict) -> str:
    """Compute a hash of the source CV to detect changes."""
    cv_yaml = yaml.dump(cv, allow_unicode=True, default_flow_style=False, sort_keys=True)
    return hashlib.sha256(cv_yaml.encode()).hexdigest()[:16]


def _validate_translation(source: dict, translated: dict) -> list[str]:
    """Check that the translation covers all top-level keys and list sections."""
    missing = []
    for key in source:
        if key not in translated:
            missing.append(key)
        elif isinstance(source[key], list) and isinstance(translated.get(key), list):
            if len(translated[key]) < len(source[key]):
                missing.append(f"{key} ({len(translated[key])}/{len(source[key])} items)")
    return missing


def _cache_is_valid(cv: dict, lang: str) -> bool:
    """Check if the cached translation matches the current source CV."""
    cache = cache_file_for(lang)
    if not cache.exists():
        return False
    cached = load_cv(cache, validate=False)
    stored_hash = cached.pop("_source_hash", None)
    cached.pop("_labels", None)
    if stored_hash != _source_hash(cv):
        console.print("[yellow]Source CV has changed since last translation — re-translating.[/]")
        return False
    problems = _validate_translation(cv, cached)
    if problems:
        console.print(f"[yellow]Cached translation is incomplete (missing: {', '.join(problems)}) — re-translating.[/]")
        return False
    return True


def _labels_yaml() -> str:
    """Build the English labels YAML block for the LLM to translate."""
    return yaml.dump(LABELS["en"], allow_unicode=True, default_flow_style=False, sort_keys=False)


def _parse_yaml_response(response: str, provider, lang: str) -> dict:
    """Parse YAML from LLM response, retrying once if malformed."""
    translated_yaml = strip_yaml_fences(response)
    try:
        return yaml.safe_load(translated_yaml)
    except yaml.YAMLError as e:
        console.print("[yellow]LLM returned malformed YAML, retrying...[/]")
        # Ask the LLM to fix its own output
        with console.status(f"Fixing YAML for {lang.upper()} translation..."):
            fixed = provider.complete(
                "The following YAML is malformed and cannot be parsed. "
                "Fix the YAML syntax errors and return ONLY the corrected YAML. "
                "Common issues: unquoted strings containing colons or special characters "
                "need to be wrapped in double quotes. Multi-line text should use the > or | "
                "YAML block scalar syntax. Do NOT add any explanation.\n\n"
                f"{translated_yaml}",
                max_tokens=16384,
            )
        fixed_yaml = strip_yaml_fences(fixed)
        try:
            return yaml.safe_load(fixed_yaml)
        except yaml.YAMLError:
            err_console.print("[red]Error:[/] Could not parse translated YAML after retry.")
            err_console.print("[dim]Run [bold]resumake build[/] to try again.[/]")
            raise SystemExit(1) from e


def translate_cv(cv: dict, lang: str = "de", retranslate: bool = False) -> dict:
    """Translate CV content to a target language using an LLM.
    Uses cached translation if available, unless retranslate is True."""
    cache = cache_file_for(lang)

    if not retranslate and _cache_is_valid(cv, lang):
        console.print(f"[dim]Using cached translation from {cache}[/]")
        cached = load_cv(cache, validate=False)
        cached.pop("_source_hash", None)
        cached.pop("_labels", None)
        return cached

    try:
        provider = get_provider()
    except RuntimeError:
        if cache.exists():
            console.print("[yellow]No LLM provider available — falling back to cached translation.[/]")
            cached = load_cv(cache, validate=False)
            cached.pop("_source_hash", None)
            cached.pop("_labels", None)
            return cached
        err_console.print("[red]Error:[/] No LLM provider available and no cached translation found.")
        err_console.print("Set ANTHROPIC_API_KEY or OPENAI_API_KEY to enable AI features.")
        raise SystemExit(1)

    cv_yaml = yaml.dump(cv, allow_unicode=True, default_flow_style=False, sort_keys=False)
    labels_yaml = _labels_yaml()

    with console.status(f"Translating CV to {lang.upper()} via LLM..."):
        response = provider.complete(
            f"Translate the following CV from English to {lang.upper()}. "
            "Return ONLY the translated YAML — no explanation, no code fences. "
            "Keep the YAML structure and ALL keys exactly the same (keys stay in English). "
            "You MUST include every section and every list item from the original. "
            "IMPORTANT: Preserve the exact same YAML formatting as the input. "
            "Use quoted strings where the input uses them. Use > or | block scalars for "
            "multi-line text. Strings containing colons MUST be quoted. "
            "Translate all values that are natural language text "
            "(descriptions, bullets, titles, skills, etc.). "
            "Do NOT translate or remove: photo filename, names, organization names, "
            "technology/tool names, URLs, email, phone, dates, publication titles, "
            "degree program names that are commonly kept in English. "
            f"Use professional {lang.upper()} suitable for a senior-level CV.\n\n"
            "IMPORTANT: At the end of the YAML, add a top-level key `_labels` "
            "with translated UI labels. "
            f"Here are the English labels to translate:\n\n_labels:\n{labels_yaml}\n"
            f"Here is the CV YAML:\n\n{cv_yaml}",
            max_tokens=16384,
        )

    translated_cv = _parse_yaml_response(response, provider, lang)

    # Extract labels before validation
    translated_labels = translated_cv.pop("_labels", None)

    # Preserve non-translatable fields the LLM may have dropped or altered
    for key in cv:
        if key not in translated_cv:
            translated_cv[key] = cv[key]
    # Always keep these from source (filenames, contact details, URLs)
    _PASSTHROUGH_KEYS = ("photo",)
    for key in _PASSTHROUGH_KEYS:
        if key in cv:
            translated_cv[key] = cv[key]
    if "contact" in cv and "contact" in translated_cv:
        for field in ("email", "phone"):
            if field in cv["contact"]:
                translated_cv["contact"][field] = cv["contact"][field]
    if "links" in cv and "links" in translated_cv:
        for i, link in enumerate(cv.get("links", [])):
            if i < len(translated_cv["links"]) and "url" in link:
                translated_cv["links"][i]["url"] = link["url"]

    # Validate completeness
    problems = _validate_translation(cv, translated_cv)
    if problems:
        console.print(f"[yellow]Warning:[/] Translation incomplete — missing: {', '.join(problems)}")
        console.print("[dim]Run [bold]resumake build[/] to try again.[/]")

    # Save with source hash and labels for cache
    cache_data = dict(translated_cv)
    cache_data["_source_hash"] = _source_hash(cv)
    if translated_labels:
        cache_data["_labels"] = translated_labels
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(cache, "w", encoding="utf-8") as f:
        yaml.dump(cache_data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
    console.print(f"[dim]Cached translation to {cache}[/]")

    return translated_cv
