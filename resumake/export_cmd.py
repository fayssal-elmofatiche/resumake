"""Export command — convert CV to Markdown, HTML, or JSON."""

import json
from pathlib import Path
from typing import Annotated, Optional

import typer

from .console import console
from .utils import DEFAULT_YAML, OUTPUT_DIR, load_cv, open_file, slugify_name


def _cv_to_markdown(cv: dict) -> str:
    """Convert CV dict to Markdown."""
    lines = []
    lines.append(f"# {cv['name']}")
    lines.append(f"**{cv['title']}**\n")

    contact = cv.get("contact", {})
    contact_parts = []
    if contact.get("email"):
        contact_parts.append(contact["email"])
    if contact.get("phone"):
        contact_parts.append(contact["phone"])
    if contact.get("address"):
        contact_parts.append(contact["address"])
    if contact_parts:
        lines.append(" | ".join(contact_parts) + "\n")

    links = cv.get("links", [])
    if links:
        lines.append(" | ".join(f"[{lk['label']}]({lk['url']})" for lk in links) + "\n")

    if cv.get("profile"):
        lines.append("## Profile\n")
        lines.append(cv["profile"].strip() + "\n")

    skills = cv.get("skills", {})
    if skills:
        lines.append("## Skills\n")
        if skills.get("leadership"):
            lines.append(f"**Leadership:** {', '.join(skills['leadership'])}\n")
        if skills.get("technical"):
            lines.append(f"**Technical:** {', '.join(skills['technical'])}\n")
        if skills.get("languages"):
            lang_strs = [f"{lg['name']} ({lg['level']})" for lg in skills["languages"]]
            lines.append(f"**Languages:** {', '.join(lang_strs)}\n")

    if cv.get("experience"):
        lines.append("## Experience\n")
        for exp in cv["experience"]:
            org_part = f" — {exp['org']}" if exp.get("org") else ""
            lines.append(f"### {exp['title']}{org_part}")
            lines.append(f"*{exp['start']} — {exp['end']}*\n")
            if exp.get("description"):
                lines.append(f"{exp['description']}\n")
            for bullet in exp.get("bullets", []):
                lines.append(f"- {bullet}")
            lines.append("")

    if cv.get("education"):
        lines.append("## Education\n")
        for edu in cv["education"]:
            lines.append(f"### {edu['degree']}, {edu['institution']}")
            lines.append(f"*{edu['start']} — {edu['end']}*\n")
            if edu.get("description"):
                lines.append(f"{edu['description']}\n")

    if cv.get("certifications"):
        lines.append("## Certifications\n")
        for cert in cv["certifications"]:
            org_part = f", {cert['org']}" if cert.get("org") else ""
            lines.append(f"- **{cert['name']}**{org_part} ({cert['start']} — {cert['end']})")
        lines.append("")

    if cv.get("publications"):
        lines.append("## Publications\n")
        for pub in cv["publications"]:
            lines.append(f"- **{pub['title']}** — {pub['venue']}, {pub['year']}")
        lines.append("")

    if cv.get("volunteering"):
        lines.append("## Volunteering\n")
        for vol in cv["volunteering"]:
            lines.append(f"### {vol['title']} — {vol['org']}")
            lines.append(f"*{vol['start']} — {vol['end']}*\n")
            if vol.get("description"):
                lines.append(f"{vol['description']}\n")

    if cv.get("references"):
        lines.append("## References\n")
        lines.append(cv["references"] + "\n")

    return "\n".join(lines)


def _cv_to_html(cv: dict) -> str:
    """Convert CV dict to a self-contained HTML page."""
    md = _cv_to_markdown(cv)
    # Simple markdown-to-html conversion for the most common elements
    import re

    html_body = md
    # Headers
    html_body = re.sub(r"^### (.+)$", r"<h3>\1</h3>", html_body, flags=re.MULTILINE)
    html_body = re.sub(r"^## (.+)$", r"<h2>\1</h2>", html_body, flags=re.MULTILINE)
    html_body = re.sub(r"^# (.+)$", r"<h1>\1</h1>", html_body, flags=re.MULTILINE)
    # Bold and italic
    html_body = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", html_body)
    html_body = re.sub(r"\*(.+?)\*", r"<em>\1</em>", html_body)
    # Links
    html_body = re.sub(r"\[(.+?)\]\((.+?)\)", r'<a href="\2">\1</a>', html_body)
    # List items
    html_body = re.sub(r"^- (.+)$", r"<li>\1</li>", html_body, flags=re.MULTILINE)
    # Wrap consecutive <li> in <ul>
    html_body = re.sub(r"((?:<li>.+</li>\n?)+)", r"<ul>\1</ul>", html_body)
    # Paragraphs for remaining lines
    lines = html_body.split("\n")
    result = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            result.append("")
        elif stripped.startswith("<"):
            result.append(stripped)
        else:
            result.append(f"<p>{stripped}</p>")
    html_body = "\n".join(result)

    name = cv.get("name", "CV")
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{name} — CV</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
         max-width: 800px; margin: 2rem auto; padding: 0 1rem; line-height: 1.6; color: #333; }}
  h1 {{ color: #0F141F; margin-bottom: 0.2rem; }}
  h2 {{ color: #0F141F; border-bottom: 2px solid #0AA8A7; padding-bottom: 0.3rem; margin-top: 1.5rem; }}
  h3 {{ color: #333; margin-bottom: 0.2rem; }}
  a {{ color: #0AA8A7; }}
  ul {{ padding-left: 1.5rem; }}
  em {{ color: #7A8599; }}
  strong {{ color: #0F141F; }}
</style>
</head>
<body>
{html_body}
</body>
</html>"""


def export(
    format: Annotated[str, typer.Argument(help="Output format: md, html, or json.")],
    source: Annotated[Path, typer.Option(help="Path to source YAML.")] = DEFAULT_YAML,
    output: Annotated[
        Optional[Path], typer.Option("--output", "-o", help="Output file path. Defaults to output/<name>_CV.<ext>.")
    ] = None,
    open: Annotated[bool, typer.Option("--open/--no-open", help="Open the generated file.")] = True,
):
    """Export CV to Markdown, HTML, or JSON format."""
    format = format.lower().lstrip(".")
    if format not in ("md", "markdown", "html", "json"):
        console.print(f"[red]Error:[/] Unknown format '{format}'. Use: md, html, or json.")
        raise typer.Exit(1)

    cv = load_cv(source)
    slug = slugify_name(cv["name"])

    if format in ("md", "markdown"):
        content = _cv_to_markdown(cv)
        ext = "md"
    elif format == "html":
        content = _cv_to_html(cv)
        ext = "html"
    else:
        content = json.dumps(cv, indent=2, ensure_ascii=False)
        ext = "json"

    if output is None:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        output = OUTPUT_DIR / f"{slug}_CV.{ext}"

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(content, encoding="utf-8")
    console.print(f"Exported: [cyan]{output}[/]")

    if open:
        open_file(output)
