"""Shared constants, paths, colors, labels, and helpers."""

import os
import platform
import re
import subprocess
from pathlib import Path

import yaml

# ── Paths ──
PACKAGE_DIR = Path(__file__).resolve().parent
BUILTIN_ASSETS_DIR = PACKAGE_DIR / "assets"

BASE_DIR = Path.cwd()
DEFAULT_YAML = BASE_DIR / "cv.yaml"
OUTPUT_DIR = BASE_DIR / "output"
CACHE_FILE = OUTPUT_DIR / ".cv_de_cache.yaml"
ASSETS_DIR = BASE_DIR / "assets"

# ── Section icons ──
SECTION_ICONS = {
    "Profile": "icon_profile.png",
    "Project / Employment History": "icon_experience.png",
    "Education": "icon_education.png",
    "Volunteering": "icon_volunteering.png",
    "Certifications": "icon_certifications.png",
    "Publications": "icon_publications.png",
    "References": "icon_profile.png",
    "Testimonials": "icon_testimonials.png",
}

# ── i18n labels ──
LABELS = {
    "en": {
        "details": "details",
        "nationality": "Nationality",
        "links": "Links",
        "skills": "skills",
        "leadership_skills": "Leadership Skills",
        "languages": "Languages",
        "profile": "Profile",
        "experience": "Project / Employment History",
        "education": "Education",
        "volunteering": "Volunteering",
        "references": "References",
        "certifications": "Certifications",
        "publications": "Publications",
        "testimonials_heading": "WHAT CLIENTS SAY:",
    },
    "de": {
        "details": "Kontakt",
        "nationality": "Nationalität",
        "links": "Links",
        "skills": "Kompetenzen",
        "leadership_skills": "Führungskompetenzen",
        "languages": "Sprachen",
        "profile": "Profil",
        "experience": "Projekt- / Berufserfahrung",
        "education": "Ausbildung",
        "volunteering": "Ehrenamt",
        "references": "Referenzen",
        "certifications": "Zertifizierungen",
        "publications": "Publikationen",
        "testimonials_heading": "WAS KUNDEN SAGEN:",
    },
}

# ── Date parsing for sorting ──

MONTH_MAP = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
    # German months
    "januar": 1,
    "februar": 2,
    "märz": 3,
    "mai": 5,
    "juni": 6,
    "juli": 7,
    "oktober": 10,
    "dezember": 12,
}


def parse_start_date(date_str: str) -> tuple:
    """Parse a start date string into (year, month) for sorting. Higher = more recent."""
    parts = date_str.strip().lower().split()
    if len(parts) == 2:
        month_str, year_str = parts
        month = MONTH_MAP.get(month_str, 0)
        try:
            year = int(year_str)
        except ValueError:
            year = 0
        return (year, month)
    if len(parts) == 1:
        try:
            return (int(parts[0]), 0)
        except ValueError:
            return (0, 0)
    return (0, 0)


def load_cv(yaml_path: Path, validate: bool = True) -> dict:
    """Load CV data from a YAML file, optionally validating against the schema."""
    if not yaml_path.exists():
        from .console import err_console

        err_console.print(f"[red]Error:[/] CV file not found: [bold]{yaml_path}[/]")
        err_console.print("\nTo get started, run: [bold]resumake init[/]")
        raise SystemExit(1)
    with open(yaml_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if validate:
        from .schema import validate_cv

        validate_cv(data)
    return data


def open_file(path: Path):
    """Open a file with the system default application."""
    if platform.system() == "Darwin":
        subprocess.Popen(["open", str(path)])
    elif platform.system() == "Windows":
        os.startfile(str(path))
    else:
        subprocess.Popen(["xdg-open", str(path)])


def convert_to_pdf(docx_path: Path) -> Path:
    """Convert a .docx file to PDF."""
    try:
        from docx2pdf import convert
    except ImportError:
        from .console import err_console

        err_console.print("[red]Error:[/] 'docx2pdf' package required for PDF generation.")
        err_console.print("Install with: [bold]uv tool install resumake --with docx2pdf[/]")
        raise SystemExit(1)
    pdf_path = docx_path.with_suffix(".pdf")
    convert(str(docx_path), str(pdf_path))
    return pdf_path


def slugify_name(name: str) -> str:
    """Convert a name like 'Jane Doe, PhD' into 'Jane_Doe_PhD'."""
    slug = re.sub(r"[^\w\s]", "", name)
    return re.sub(r"\s+", "_", slug).strip("_")


def resolve_asset(filename: str) -> Path | None:
    """Find an asset file, checking user's assets/ first, then built-in package assets."""
    user_path = ASSETS_DIR / filename
    if user_path.exists():
        return user_path
    builtin_path = BUILTIN_ASSETS_DIR / filename
    if builtin_path.exists():
        return builtin_path
    return None
