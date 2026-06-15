"""Tests for PDF conversion module."""

import pytest

from resumake.pdf import convert_to_pdf_auto, convert_to_pdf_docx2pdf, convert_to_pdf_weasyprint


def _multi_role_cv():
    """A CV long enough to overflow a single page (12 roles + trailing sections)."""
    return {
        "name": "Jane Doe",
        "title": "Engineer",
        "photo": "",
        "contact": {"address": "Berlin", "phone": "+49", "email": "j@x.com", "nationality": "German"},
        "links": [{"label": "GitHub", "url": "https://github.com/janedoe"}],
        "skills": {
            "leadership": ["Lead"] * 5,
            "technical": ["Python", "TypeScript"] * 5,
            "languages": [{"name": "English", "level": "fluent"}],
        },
        "profile": "Experienced engineer. " * 30,
        "experience": [
            {
                "title": f"Role {i}",
                "org": f"Org {i}",
                "start": "2010",
                "end": "2012",
                "description": "Did things. " * 10,
                "bullets": [f"Accomplishment {i}-{j} with plenty of detail to fill space" for j in range(6)],
            }
            for i in range(12)
        ],
        "education": [{"degree": "MSc", "institution": "TU Berlin", "start": "2014", "end": "2016"}],
        "certifications": [{"name": "ZZZ_LAST_SECTION_MARKER cert", "org": "Issuer", "start": "2020", "end": "2020"}],
    }


def _collect_pdf_text(box, out):
    """Recursively collect text from a WeasyPrint document box tree."""
    if getattr(box, "text", None):
        out.append(box.text)
    for child in getattr(box, "children", []) or []:
        _collect_pdf_text(child, out)


def test_weasyprint_multipage_not_truncated():
    """Regression: a multi-role CV must paginate across pages without dropping
    content. The two-column layout previously used `display: flex` + `min-height:
    100vh`, which WeasyPrint cannot fragment across pages, so everything after
    page 1 was silently clipped.
    """
    try:
        import weasyprint
    except ImportError:
        pytest.skip("weasyprint not installed")
    except OSError as exc:  # native libs (pango/gobject) unavailable at import time
        pytest.skip(f"WeasyPrint native dependencies unavailable: {exc}")

    from resumake.html_builder import build_html
    from resumake.theme import Theme

    html = build_html(_multi_role_cv(), "en", theme=Theme())
    try:
        document = weasyprint.HTML(string=html).render()
    except OSError as exc:  # native libs (pango/gobject) unavailable in this env
        pytest.skip(f"WeasyPrint native dependencies unavailable: {exc}")

    texts: list[str] = []
    for page in document.pages:
        _collect_pdf_text(page._page_box, texts)
    rendered = " ".join(texts)

    assert len(document.pages) > 1, "multi-role CV should span more than one page"
    assert "Role 0" in rendered, "first role missing from rendered PDF"
    assert "Role 11" in rendered, "last role dropped — content truncated after page 1"
    assert "ZZZ_LAST_SECTION_MARKER" in rendered, "trailing section dropped from rendered PDF"


def test_weasyprint_import_error(tmp_path, monkeypatch):
    """WeasyPrint raises SystemExit with install instructions when not available."""
    original_import = __builtins__.__import__ if hasattr(__builtins__, "__import__") else __import__

    def mock_import(name, *args, **kwargs):
        if name == "weasyprint":
            raise ImportError("No module named 'weasyprint'")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr("builtins.__import__", mock_import)
    with pytest.raises(SystemExit):
        convert_to_pdf_weasyprint("<html></html>", tmp_path / "out.pdf")


def test_docx2pdf_import_error(tmp_path, monkeypatch):
    """docx2pdf raises SystemExit with install instructions when not available."""
    original_import = __builtins__.__import__ if hasattr(__builtins__, "__import__") else __import__

    def mock_import(name, *args, **kwargs):
        if name == "docx2pdf":
            raise ImportError("No module named 'docx2pdf'")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr("builtins.__import__", mock_import)
    with pytest.raises(SystemExit):
        convert_to_pdf_docx2pdf(tmp_path / "input.docx")


def test_auto_engine_fallback(tmp_path, monkeypatch):
    """Auto engine falls back to docx2pdf when weasyprint is not installed."""
    original_import = __builtins__.__import__ if hasattr(__builtins__, "__import__") else __import__
    calls = []

    def mock_import(name, *args, **kwargs):
        if name == "weasyprint":
            raise ImportError("No module named 'weasyprint'")
        if name == "docx2pdf":
            calls.append("docx2pdf")
            raise ImportError("No module named 'docx2pdf'")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr("builtins.__import__", mock_import)
    with pytest.raises(SystemExit):
        convert_to_pdf_auto(tmp_path / "input.docx", engine="auto", html_content="<html></html>")
    # Should have attempted docx2pdf as fallback
    assert "docx2pdf" in calls
