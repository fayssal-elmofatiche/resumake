"""Tailor command — produce a CV variant emphasizing relevant experience for a project/job."""

import re
from pathlib import Path
from typing import Annotated, Optional

import typer
import yaml

from .config import load_config, resolve
from .console import console, err_console
from .docx_builder import build_docx
from .llm import get_provider, strip_yaml_fences
from .theme import load_theme
from .translate import translate_cv
from .utils import DEFAULT_YAML, OUTPUT_DIR, convert_to_pdf, load_cv, open_file, slugify_name


def tailor_cv(cv: dict, description_text: str) -> dict:
    """Use an LLM to tailor the CV for a specific project/job description."""
    provider = get_provider()

    cv_yaml = yaml.dump(cv, allow_unicode=True, default_flow_style=False, sort_keys=False)

    with console.status("Tailoring CV via LLM..."):
        response = provider.complete(
            "You are a professional CV consultant. Given a CV in YAML format and a project/job description, "
            "produce a tailored version of the CV that highlights the most relevant experience and skills.\n\n"
            "Rules:\n"
            "- Return ONLY the tailored YAML — no explanation, no code fences.\n"
            "- Keep the exact same YAML structure and keys.\n"
            "- Do NOT invent, fabricate, or add any new content that isn't in the original CV.\n"
            "- Rewrite the profile summary to emphasize relevance to the description.\n"
            "- Reorder the experience entries so the most relevant ones come first.\n"
            "- For each experience entry, you may reorder bullets to foreground relevant ones.\n"
            "- You may slightly rephrase bullets to better highlight relevance, but do not change facts.\n"
            "- Keep all experience entries — do not remove any.\n"
            "- Reorder skills to foreground the most relevant ones.\n"
            "- Keep education, certifications, publications, volunteering, and references unchanged.\n\n"
            f"PROJECT/JOB DESCRIPTION:\n{description_text}\n\n"
            f"CV YAML:\n{cv_yaml}",
            max_tokens=8192,
        )

    tailored_yaml = strip_yaml_fences(response)
    return yaml.safe_load(tailored_yaml)


def _slugify(text: str, max_len: int = 30) -> str:
    """Create a filesystem-safe slug from text."""
    slug = re.sub(r"[^\w\s-]", "", text.lower())
    slug = re.sub(r"[\s_]+", "_", slug).strip("_")
    return slug[:max_len]


def tailor(
    description_file: Annotated[
        Path,
        typer.Argument(help="Path to a .txt or .md file with the project/job description."),
    ],
    lang: Annotated[Optional[str], typer.Option(help="Output language code (e.g. en, de, fr). Default: en.")] = None,
    source: Annotated[Optional[Path], typer.Option(help="Path to source YAML.")] = None,
    pdf: Annotated[Optional[bool], typer.Option("--pdf/--no-pdf", help="Also generate PDF.")] = None,
    open: Annotated[Optional[bool], typer.Option("--open/--no-open", help="Open the generated file.")] = None,
    theme: Annotated[
        Optional[str],
        typer.Option(help="Theme name (classic, minimal, modern) or path to theme.yaml."),
    ] = None,
):
    """Produce a tailored CV variant for a specific project or job description."""
    cfg = load_config()
    lang = resolve(lang, cfg.lang, "en")
    source = Path(resolve(source, cfg.source, str(DEFAULT_YAML)))
    pdf = resolve(pdf, cfg.pdf, False)
    open = resolve(open, cfg.open, True)
    theme = resolve(theme, cfg.theme, None)

    if not description_file.exists():
        err_console.print(f"[red]Error:[/] File not found: {description_file}")
        raise typer.Exit(1)

    description_text = description_file.read_text(encoding="utf-8").strip()
    if not description_text:
        err_console.print("[red]Error:[/] Description file is empty.")
        raise typer.Exit(1)

    # Load and tailor the EN CV
    cv_en = load_cv(source)
    tailored_cv = tailor_cv(cv_en, description_text)

    # Translate if needed
    if lang != "en":
        tailored_cv = translate_cv(tailored_cv, lang=lang, retranslate=True)

    # Build the docx — use a custom output filename
    resolved_theme = load_theme(theme)
    slug = _slugify(description_file.stem)
    output_path = build_docx(tailored_cv, lang, theme=resolved_theme)

    # Rename to tailored filename
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    name_slug = slugify_name(cv_en["name"])
    tailored_filename = f"{name_slug}_CV_{lang.upper()}_tailored_{slug}.docx"
    tailored_path = OUTPUT_DIR / tailored_filename
    output_path.rename(tailored_path)

    console.print(f"Generated: [cyan]{tailored_path}[/]")

    outputs = [tailored_path]
    if pdf:
        pdf_path = convert_to_pdf(tailored_path)
        console.print(f"Generated: [cyan]{pdf_path}[/]")
        outputs.append(pdf_path)

    if open:
        for p in outputs:
            open_file(p)
