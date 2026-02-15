"""LinkedIn PDF import — parse a LinkedIn profile PDF export into cv.yaml."""

from pathlib import Path


def extract_linkedin_text(pdf_path: Path) -> str:
    """Extract text from a LinkedIn profile PDF using pdfplumber."""
    try:
        import pdfplumber
    except ImportError:
        from .console import err_console

        err_console.print("[red]Error:[/] 'pdfplumber' package required for LinkedIn import.")
        err_console.print("Install with: [bold]uv tool install resumakeai --with pdfplumber[/]")
        raise SystemExit(1)

    text_parts = []
    with pdfplumber.open(str(pdf_path)) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                text_parts.append(text)

    if not text_parts:
        from .console import err_console

        err_console.print("[red]Error:[/] Could not extract text from LinkedIn PDF.")
        raise SystemExit(1)

    return "\n\n".join(text_parts)


def linkedin_to_cv(text: str) -> dict:
    """Structure LinkedIn PDF text into a CV dict using an LLM."""
    from .llm import get_provider

    try:
        provider = get_provider()
    except RuntimeError:
        from .console import err_console

        err_console.print("[red]Error:[/] LinkedIn import requires an LLM provider to structure the data.")
        err_console.print("Set ANTHROPIC_API_KEY or OPENAI_API_KEY.")
        raise SystemExit(1)

    import yaml

    from .console import console

    with console.status("Structuring LinkedIn profile via LLM..."):
        response = provider.complete(
            "Convert the following LinkedIn profile text into a structured YAML CV. "
            "Return ONLY valid YAML with these top-level keys (omit any that don't apply): "
            "name, title, contact (with address, email, phone, nationality), "
            "links (list of label+url), skills (with leadership, technical, languages lists), "
            "profile (summary text), experience (list with title, org, start, end, description, bullets), "
            "education (list with degree, institution, start, end), "
            "certifications (list with name, org, start, end), "
            "volunteering (list with title, org, start, end, description). "
            "Use professional English. Do NOT add any explanation.\n\n"
            f"LinkedIn profile text:\n\n{text}",
            max_tokens=8192,
        )

    from .llm import strip_yaml_fences

    yaml_text = strip_yaml_fences(response)
    try:
        return yaml.safe_load(yaml_text)
    except yaml.YAMLError:
        from .console import err_console

        err_console.print("[red]Error:[/] Could not parse LLM response as YAML.")
        raise SystemExit(1)


def import_linkedin(pdf_path: Path) -> dict:
    """Full pipeline: extract text from LinkedIn PDF and structure into CV dict."""
    text = extract_linkedin_text(pdf_path)
    return linkedin_to_cv(text)
