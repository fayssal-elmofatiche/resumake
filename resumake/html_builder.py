"""HTML builder — generates print-optimized, themed HTML matching the DOCX layout."""

import base64

from .schema import get_custom_sections
from .theme import Theme, load_theme
from .utils import get_labels, resolve_asset


def _encode_photo_base64(photo_ref: str | None) -> str | None:
    """Resolve a photo reference and return a base64 data URL, or None."""
    if not photo_ref:
        return None
    path = resolve_asset(photo_ref)
    if not path or not path.exists():
        return None
    suffix = path.suffix.lower().lstrip(".")
    mime = {"jpg": "jpeg", "jpeg": "jpeg", "png": "png", "gif": "gif"}.get(suffix, "png")
    data = base64.b64encode(path.read_bytes()).decode()
    return f"data:image/{mime};base64,{data}"


def _esc(text: str) -> str:
    """HTML-escape a string."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def _build_css(theme: Theme) -> str:
    """Generate CSS from theme settings."""
    c = theme.colors
    f = theme.fonts
    s = theme.sizes
    lay = theme.layout
    return f"""
    @page {{
        size: A4;
        margin: {lay.page_top_margin_cm}cm {lay.page_right_margin_cm}cm
                {lay.page_bottom_margin_cm}cm {lay.page_left_margin_cm}cm;
    }}
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{
        font-family: {f.body}, Calibri, Arial, sans-serif;
        font-size: {s.body_pt}pt;
        color: #{c.text_body};
        line-height: 1.4;
        -webkit-print-color-adjust: exact;
        print-color-adjust: exact;
    }}
    .cv-container {{
        display: flex;
        min-height: 100vh;
    }}
    .sidebar {{
        width: {lay.sidebar_width_cm}cm;
        min-width: {lay.sidebar_width_cm}cm;
        background-color: #{c.primary};
        color: #{c.text_light};
        padding: 0.8cm 0.5cm;
        text-align: center;
    }}
    .main {{
        flex: 1;
        padding: 0.6cm 0.6cm 1cm 0.8cm;
    }}
    .photo {{ width: 2.8cm; height: 2.8cm; border-radius: 50%; object-fit: cover; margin-bottom: 0.4cm; }}
    .sidebar h1 {{
        font-family: {f.heading}, Arial Narrow, sans-serif;
        font-size: {s.name_pt}pt;
        color: #{c.text_light};
        margin-bottom: 0.2cm;
        font-weight: bold;
    }}
    .sidebar .title {{
        font-size: {s.small_pt}pt;
        color: #{c.text_muted};
        font-style: italic;
        margin-bottom: 0.6cm;
    }}
    .sidebar-section-title {{
        font-family: {f.heading}, Arial Narrow, sans-serif;
        font-size: {s.subheading_pt}pt;
        color: #{c.text_light};
        font-weight: bold;
        margin-top: 0.4cm;
        margin-bottom: 0.2cm;
    }}
    .sidebar-label {{
        font-size: {s.body_pt}pt;
        color: #{c.text_muted};
        font-weight: bold;
        margin-bottom: 0.1cm;
    }}
    .sidebar-text {{
        font-size: {s.small_pt}pt;
        color: #{c.text_light};
        margin-bottom: 0.1cm;
    }}
    .sidebar a {{
        color: #{c.accent};
        text-decoration: underline;
        font-size: {s.small_pt}pt;
    }}
    .section-heading {{
        font-family: {f.heading}, Arial Narrow, sans-serif;
        font-size: {s.heading_pt}pt;
        color: #{c.primary};
        font-weight: bold;
        margin-top: 0.5cm;
        margin-bottom: 0.1cm;
        padding-bottom: 0.1cm;
        border-bottom: 1.5px solid #{c.accent};
    }}
    .entry-title {{
        font-family: {f.heading}, Arial Narrow, sans-serif;
        font-size: {s.body_pt}pt;
        color: #{c.primary};
        font-weight: bold;
        margin-top: 0.3cm;
    }}
    .entry-dates {{
        font-size: {s.small_pt}pt;
        color: #{c.text_muted};
        margin-bottom: 0.1cm;
    }}
    .entry-desc {{
        font-size: {s.body_pt}pt;
        color: #{c.text_muted};
        font-style: italic;
        margin-bottom: 0.1cm;
    }}
    .body-text {{
        font-size: {s.body_pt}pt;
        color: #{c.text_body};
        margin-bottom: 0.1cm;
    }}
    ul.bullets {{
        padding-left: 0.5cm;
        margin: 0.05cm 0;
    }}
    ul.bullets li {{
        font-size: {s.small_pt}pt;
        color: #{c.text_body};
        margin-bottom: 0.05cm;
    }}
    .meta-line {{
        font-size: {s.small_pt}pt;
        margin-bottom: 0.02cm;
    }}
    .meta-label {{
        color: #{c.accent};
        font-weight: bold;
    }}
    .meta-value {{
        color: #{c.text_muted};
    }}
    .testimonial-quote {{
        font-size: {s.body_pt}pt;
        color: #{c.text_muted};
        font-style: italic;
        margin-bottom: 0.1cm;
    }}
    .testimonial-author {{
        font-size: {s.body_pt}pt;
        color: #{c.primary};
        font-weight: bold;
    }}
    .testimonial-role {{
        font-size: {s.small_pt}pt;
        color: #{c.text_muted};
    }}
    @media print {{
        .cv-container {{ min-height: auto; }}
        .entry-title {{ page-break-inside: avoid; }}
    }}
    """


def _render_sidebar_html(cv: dict, theme: Theme, lang: str) -> str:
    """Render the sidebar column."""
    L = get_labels(lang)
    parts = []

    # Photo
    photo_url = _encode_photo_base64(cv.get("photo"))
    if photo_url:
        parts.append(f'<img class="photo" src="{photo_url}" alt="Photo">')

    # Name
    parts.append(f'<h1>{_esc(cv["name"])}</h1>')
    parts.append(f'<div class="title">{_esc(cv["title"])}</div>')

    # Contact
    contact = cv.get("contact", {})
    parts.append(f'<div class="sidebar-section-title">{_esc(L["details"])}</div>')
    for field in ("address", "phone", "email"):
        if contact.get(field):
            parts.append(f'<div class="sidebar-text">{_esc(contact[field])}</div>')
    if contact.get("nationality"):
        parts.append(f'<div class="sidebar-label">{_esc(L["nationality"])}</div>')
        parts.append(f'<div class="sidebar-text">{_esc(contact["nationality"])}</div>')

    # Links
    links = cv.get("links", [])
    if links:
        parts.append(f'<div class="sidebar-section-title">{_esc(L["links"])}</div>')
        for lk in links:
            if lk.get("url"):
                parts.append(f'<a href="{_esc(lk["url"])}">{_esc(lk["label"])}</a><br>')
            else:
                parts.append(f'<div class="sidebar-text">{_esc(lk["label"])}</div>')

    # Skills
    skills = cv.get("skills", {})
    if skills:
        parts.append(f'<div class="sidebar-section-title">{_esc(L["skills"])}</div>')
        if skills.get("leadership"):
            parts.append(f'<div class="sidebar-label">{_esc(L["leadership_skills"])}</div>')
            for s in skills["leadership"]:
                parts.append(f'<div class="sidebar-text">{_esc(s)}</div>')
        if skills.get("technical"):
            for s in skills["technical"]:
                parts.append(f'<div class="sidebar-text">{_esc(s)}</div>')

    # Languages
    languages = skills.get("languages", [])
    if languages:
        parts.append(f'<div class="sidebar-section-title">{_esc(L["languages"])}</div>')
        for lg in languages:
            level = lg.get("level", "")
            parts.append(f'<div class="sidebar-text">{_esc(lg["name"])} ({_esc(level)})</div>')

    return "\n".join(parts)


def _render_main_html(cv: dict, theme: Theme, lang: str) -> str:
    """Render the main content column."""
    L = get_labels(lang)
    parts = []

    # Profile
    if cv.get("profile"):
        parts.append(f'<div class="section-heading">{_esc(L["profile"])}</div>')
        parts.append(f'<div class="body-text">{_esc(cv["profile"].strip())}</div>')

        # Testimonials under profile
        if cv.get("testimonials"):
            parts.append(f'<div class="entry-title">{_esc(L["testimonials_heading"])}</div>')
            for t in cv["testimonials"]:
                if t.get("quote"):
                    parts.append(f'<div class="testimonial-quote">"{_esc(t["quote"])}"</div>')
                parts.append(f'<div class="testimonial-author">{_esc(t["name"])}</div>')
                parts.append(f'<div class="testimonial-role">{_esc(t["role"])}, {_esc(t["org"])}</div>')

    # Experience
    if cv.get("experience"):
        parts.append(f'<div class="section-heading">{_esc(L["experience"])}</div>')
        for exp in cv["experience"]:
            title_text = exp["title"]
            if exp.get("org"):
                title_text += f' — {exp["org"]}'
            parts.append(f'<div class="entry-title">{_esc(title_text)}</div>')
            parts.append(f'<div class="entry-dates">{_esc(exp["start"])} — {_esc(exp["end"])}</div>')
            if exp.get("description"):
                parts.append(f'<div class="entry-desc">{_esc(exp["description"])}</div>')
            if exp.get("bullets"):
                parts.append('<ul class="bullets">')
                for b in exp["bullets"]:
                    parts.append(f"<li>{_esc(b)}</li>")
                parts.append("</ul>")
            # Meta fields
            skip = {"title", "org", "start", "end", "description", "bullets"}
            for key, val in exp.items():
                if key in skip:
                    continue
                if isinstance(val, list) and val:
                    parts.append(
                        f'<div class="meta-line"><span class="meta-label">'
                        f'{_esc(key.replace("_", " ").title())}:</span> '
                        f'<span class="meta-value">{_esc(", ".join(str(v) for v in val))}</span></div>'
                    )
                elif isinstance(val, str):
                    parts.append(
                        f'<div class="meta-line"><span class="meta-label">'
                        f'{_esc(key.replace("_", " ").title())}:</span> '
                        f'<span class="meta-value">{_esc(val)}</span></div>'
                    )

    # Education
    if cv.get("education"):
        parts.append(f'<div class="section-heading">{_esc(L["education"])}</div>')
        for edu in cv["education"]:
            parts.append(f'<div class="entry-title">{_esc(edu["degree"])}, {_esc(edu["institution"])}</div>')
            parts.append(f'<div class="entry-dates">{_esc(edu["start"])} — {_esc(edu["end"])}</div>')
            if edu.get("description"):
                parts.append(f'<div class="body-text">{_esc(edu["description"])}</div>')
            if edu.get("details"):
                parts.append(f'<div class="entry-desc">{_esc(edu["details"])}</div>')

    # Volunteering
    if cv.get("volunteering"):
        parts.append(f'<div class="section-heading">{_esc(L["volunteering"])}</div>')
        for vol in cv["volunteering"]:
            parts.append(f'<div class="entry-title">{_esc(vol["title"])} — {_esc(vol["org"])}</div>')
            parts.append(f'<div class="entry-dates">{_esc(vol["start"])} — {_esc(vol["end"])}</div>')
            if vol.get("description"):
                parts.append(f'<div class="body-text">{_esc(vol["description"])}</div>')

    # References
    if cv.get("references"):
        parts.append(f'<div class="section-heading">{_esc(L["references"])}</div>')
        parts.append(f'<div class="body-text">{_esc(cv["references"])}</div>')

    # Certifications
    if cv.get("certifications"):
        parts.append(f'<div class="section-heading">{_esc(L["certifications"])}</div>')
        for cert in cv["certifications"]:
            title_text = cert["name"]
            if cert.get("org"):
                title_text += f', {cert["org"]}'
            parts.append(f'<div class="entry-title">{_esc(title_text)}</div>')
            parts.append(f'<div class="entry-dates">{_esc(cert["start"])} — {_esc(cert["end"])}</div>')
            if cert.get("description"):
                parts.append(f'<div class="body-text">{_esc(cert["description"])}</div>')

    # Publications
    if cv.get("publications"):
        parts.append(f'<div class="section-heading">{_esc(L["publications"])}</div>')
        for pub in cv["publications"]:
            parts.append(f'<div class="entry-title">{_esc(pub["title"])}</div>')
            parts.append(f'<div class="entry-dates">{pub["year"]}: {_esc(pub["venue"])}</div>')

    # Custom sections
    for section_key, items in get_custom_sections(cv).items():
        heading = section_key.replace("_", " ").title()
        parts.append(f'<div class="section-heading">{_esc(heading)}</div>')
        for item in items:
            if isinstance(item, str):
                parts.append(f'<div class="body-text">• {_esc(item)}</div>')
            elif isinstance(item, dict):
                label = item.get("title") or item.get("name") or ""
                org = item.get("org", "")
                if label:
                    title_text = label
                    if org:
                        title_text += f", {org}"
                    parts.append(f'<div class="entry-title">{_esc(title_text)}</div>')
                if item.get("start"):
                    dates = f'{item["start"]} — {item.get("end", "")}'
                    parts.append(f'<div class="entry-dates">{_esc(dates)}</div>')
                if item.get("description"):
                    parts.append(f'<div class="body-text">{_esc(item["description"])}</div>')

    return "\n".join(parts)


def _render_single_column_header_html(cv: dict, theme: Theme, lang: str) -> str:
    """Render an inline header for single-column layouts."""
    parts = []
    parts.append('<div style="text-align:center;margin-bottom:0.5cm">')
    parts.append(f'<div style="font-size:{theme.sizes.name_pt}pt;font-weight:bold;'
                 f'color:#{theme.colors.primary}">{_esc(cv["name"])}</div>')
    parts.append(f'<div style="font-size:{theme.sizes.body_pt}pt;color:#{theme.colors.text_muted};'
                 f'font-style:italic">{_esc(cv["title"])}</div>')

    contact = cv.get("contact", {})
    contact_parts = [v for v in [contact.get("email"), contact.get("phone"), contact.get("address")] if v]
    if contact_parts:
        parts.append(f'<div style="font-size:{theme.sizes.small_pt}pt;color:#{theme.colors.text_muted};'
                     f'margin-top:0.2cm">{_esc(" | ".join(contact_parts))}</div>')

    links = cv.get("links", [])
    if links:
        link_strs = [f'<a href="{_esc(lk["url"])}" style="color:#{theme.colors.accent}">{_esc(lk["label"])}</a>'
                     for lk in links if lk.get("url")]
        if link_strs:
            parts.append(f'<div style="font-size:{theme.sizes.small_pt}pt;margin-top:0.1cm">'
                         f'{" | ".join(link_strs)}</div>')

    parts.append('</div>')
    return "\n".join(parts)


def build_html(cv: dict, lang: str, theme: Theme | None = None) -> str:
    """Build a print-optimized, themed HTML document from CV data."""
    theme = theme or load_theme()
    css = _build_css(theme)
    layout_type = theme.layout.layout_type
    name = _esc(cv.get("name", "CV"))

    if layout_type in ("single-column", "academic"):
        header = _render_single_column_header_html(cv, theme, lang)
        main = _render_main_html(cv, theme, lang)
        body = f"""<div style="max-width:18cm;margin:0 auto">
  {header}
  {main}
</div>"""
    elif layout_type == "compact":
        sidebar = _render_sidebar_html(cv, theme, lang)
        main = _render_main_html(cv, theme, lang)
        body = f"""<div class="cv-container">
  <div class="sidebar">
    {sidebar}
  </div>
  <div class="main">
    {main}
  </div>
</div>"""
    else:
        sidebar = _render_sidebar_html(cv, theme, lang)
        main = _render_main_html(cv, theme, lang)
        body = f"""<div class="cv-container">
  <div class="sidebar">
    {sidebar}
  </div>
  <div class="main">
    {main}
  </div>
</div>"""

    return f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{name} — CV</title>
<style>{css}</style>
</head>
<body>
{body}
</body>
</html>"""
