"""CV translation via LLM — supports any target language.

Architecture: extract-translate-merge
1. Extract only translatable text from the CV (titles, descriptions, bullets, skills)
2. Send that subset to the LLM — non-text fields (photo, URLs, dates, emails) never leave
3. Merge translated text back into the original CV skeleton
"""

import copy
import hashlib

import yaml

from .console import console, err_console
from .llm import get_provider, strip_yaml_fences
from .schema import get_custom_sections
from .utils import LABELS, OUTPUT_DIR, cache_file_for, load_cv


def _source_hash(cv: dict) -> str:
    """Compute a hash of the source CV to detect changes."""
    cv_yaml = yaml.dump(cv, allow_unicode=True, default_flow_style=False, sort_keys=True)
    return hashlib.sha256(cv_yaml.encode()).hexdigest()[:16]


def _extract_translatable(cv: dict) -> dict:
    """Extract only translatable text from the CV.

    Non-text fields (photo, name, URLs, emails, phones, dates, org names)
    are excluded so the LLM cannot drop or alter them.
    """
    t: dict = {}

    if cv.get("title"):
        t["title"] = cv["title"]
    if cv.get("profile"):
        t["profile"] = cv["profile"]
    if cv.get("references"):
        t["references"] = cv["references"]

    # Contact: only address and nationality need translation
    contact = cv.get("contact", {})
    t_contact = {}
    for key in ("address", "nationality"):
        if contact.get(key):
            t_contact[key] = contact[key]
    if t_contact:
        t["contact"] = t_contact

    # Skills
    skills = cv.get("skills", {})
    if skills:
        t_skills: dict = {}
        if skills.get("leadership"):
            t_skills["leadership"] = skills["leadership"]
        if skills.get("technical"):
            t_skills["technical"] = skills["technical"]
        if skills.get("languages"):
            t_skills["languages"] = [{"name": lg["name"]} for lg in skills["languages"]]
        if t_skills:
            t["skills"] = t_skills

    # Testimonials: translate quote and role, not name/org
    if cv.get("testimonials"):
        t["testimonials"] = [{"quote": te["quote"], "role": te["role"]} for te in cv["testimonials"]]

    # Experience: everything except org, start, end (dates and org names stay)
    if cv.get("experience"):
        _skip = {"org", "start", "end"}
        t["experience"] = [{k: v for k, v in exp.items() if k not in _skip} for exp in cv["experience"]]

    # Education: degree, description, details (not institution, dates)
    if cv.get("education"):
        t["education"] = [
            {k: edu[k] for k in ("degree", "description", "details") if edu.get(k)} for edu in cv["education"]
        ]

    # Volunteering: title, description (not org, dates)
    if cv.get("volunteering"):
        t["volunteering"] = [{k: v[k] for k in ("title", "description") if v.get(k)} for v in cv["volunteering"]]

    # Certifications: name, description (not org, dates)
    if cv.get("certifications"):
        t["certifications"] = [{k: c[k] for k in ("name", "description") if c.get(k)} for c in cv["certifications"]]

    # Custom sections: extract translatable string values from each item
    _skip_translate = {"org", "start", "end", "url", "email", "phone"}
    for section_key, items in get_custom_sections(cv).items():
        t_items = []
        for item in items:
            if isinstance(item, str):
                t_items.append(item)
            elif isinstance(item, dict):
                t_item = {}
                for k, v in item.items():
                    if k in _skip_translate:
                        continue
                    if isinstance(v, str):
                        t_item[k] = v
                    elif isinstance(v, list) and v and isinstance(v[0], str):
                        t_item[k] = v
                if t_item:
                    t_items.append(t_item)
        if t_items:
            t[section_key] = t_items

    return t


def _merge_translation(cv: dict, translated: dict) -> dict:
    """Merge translated text back into the original CV.

    The original CV provides the full skeleton (photo, URLs, dates, etc.).
    Only the translated text fields are overwritten.
    """
    result = copy.deepcopy(cv)

    # Top-level strings
    for key in ("title", "profile", "references"):
        if key in translated:
            result[key] = translated[key]

    # Contact
    if "contact" in translated:
        for key in ("address", "nationality"):
            if key in translated["contact"]:
                result["contact"][key] = translated["contact"][key]

    # Skills
    if "skills" in translated:
        ts = translated["skills"]
        rs = result.get("skills", {})
        for key in ("leadership", "technical"):
            if key in ts:
                rs[key] = ts[key]
        if "languages" in ts and "languages" in rs:
            for i, tl in enumerate(ts["languages"]):
                if i < len(rs["languages"]) and "name" in tl:
                    rs["languages"][i]["name"] = tl["name"]

    # List sections: merge by index, only overwrite translatable fields
    _list_fields = {
        "testimonials": ("quote", "role"),
        "education": ("degree", "description", "details"),
        "volunteering": ("title", "description"),
        "certifications": ("name", "description"),
    }
    for section, fields in _list_fields.items():
        if section in translated and section in result:
            for i, item_t in enumerate(translated[section]):
                if i < len(result[section]):
                    for key in fields:
                        if key in item_t:
                            result[section][i][key] = item_t[key]

    # Experience: merge all translated keys (title, description, bullets, extra fields)
    if "experience" in translated and "experience" in result:
        for i, item_t in enumerate(translated["experience"]):
            if i < len(result["experience"]):
                for key, val in item_t.items():
                    result["experience"][i][key] = val

    # Custom sections: merge translated values by index
    for section_key in get_custom_sections(cv):
        if section_key in translated and section_key in result:
            for i, item_t in enumerate(translated[section_key]):
                if i < len(result[section_key]):
                    if isinstance(item_t, str):
                        result[section_key][i] = item_t
                    elif isinstance(item_t, dict) and isinstance(result[section_key][i], dict):
                        for key, val in item_t.items():
                            result[section_key][i][key] = val

    return result


def _validate_translation(source: dict, translated: dict) -> list[str]:
    """Check that the translation covers all sections and list items."""
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

    Uses an extract-translate-merge approach:
    1. Extract only translatable text (titles, descriptions, bullets, skills)
    2. Send that subset to the LLM (photo, URLs, dates, etc. never leave)
    3. Merge translated text back into the original CV skeleton

    Uses cached translation if available, unless retranslate is True.
    """
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

    # Send ONLY translatable text to the LLM
    translatable = _extract_translatable(cv)
    translatable_yaml = yaml.dump(translatable, allow_unicode=True, default_flow_style=False, sort_keys=False)
    labels_yaml = _labels_yaml()

    with console.status(f"Translating CV to {lang.upper()} via LLM..."):
        response = provider.complete(
            f"Translate the following CV content from English to {lang.upper()}. "
            "Return ONLY the translated YAML — no explanation, no code fences. "
            "Keep the YAML structure and ALL keys exactly the same (keys stay in English). "
            "You MUST include every section and every list item from the original. "
            "Preserve the exact same YAML formatting as the input. "
            "Use quoted strings where the input uses them. Use > or | block scalars for "
            "multi-line text. Strings containing colons MUST be quoted. "
            "Translate all text values to professional {lang} suitable for a senior-level CV. "
            "Do NOT translate technology names, tool names, or framework names.\n\n"
            "IMPORTANT: At the end of the YAML, add a top-level key `_labels` "
            "with translated UI labels. "
            f"Here are the English labels to translate:\n\n_labels:\n{labels_yaml}\n"
            f"Here is the CV content to translate:\n\n{translatable_yaml}",
            max_tokens=16384,
        )

    translated_text = _parse_yaml_response(response, provider, lang)

    # Extract labels before merging
    translated_labels = translated_text.pop("_labels", None)

    # Validate the translated text covers all sections
    problems = _validate_translation(translatable, translated_text)
    if problems:
        console.print(f"[yellow]Warning:[/] Translation incomplete — missing: {', '.join(problems)}")
        console.print("[dim]Run [bold]resumake build[/] to try again.[/]")

    # Merge translated text back into the full CV (preserves photo, URLs, dates, etc.)
    translated_cv = _merge_translation(cv, translated_text)

    # Save full translated CV with source hash and labels for cache
    cache_data = dict(translated_cv)
    cache_data["_source_hash"] = _source_hash(cv)
    if translated_labels:
        cache_data["_labels"] = translated_labels
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(cache, "w", encoding="utf-8") as f:
        yaml.dump(cache_data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
    console.print(f"[dim]Cached translation to {cache}[/]")

    return translated_cv
