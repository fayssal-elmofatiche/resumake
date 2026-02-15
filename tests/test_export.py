"""Tests for export command."""

from resumake.export_cmd import _cv_to_html, _cv_to_markdown, _cv_to_plaintext


def test_cv_to_markdown(sample_cv):
    md = _cv_to_markdown(sample_cv)
    assert "# Jane Doe" in md
    assert "Software Engineer" in md
    assert "## Profile" in md
    assert "## Experience" in md
    assert "## Education" in md
    assert "Built features" in md


def test_cv_to_markdown_links(sample_cv):
    md = _cv_to_markdown(sample_cv)
    assert "[GitHub](https://github.com/janedoe)" in md


def test_cv_to_markdown_skills(sample_cv):
    md = _cv_to_markdown(sample_cv)
    assert "Python" in md
    assert "TypeScript" in md


def test_cv_to_markdown_optional_sections():
    """Markdown export handles missing optional sections gracefully."""
    cv = {
        "name": "Jane",
        "title": "Dev",
        "contact": {"email": "j@test.com"},
        "experience": [{"title": "Dev", "org": "Co", "start": "2020", "end": "2021"}],
    }
    md = _cv_to_markdown(cv)
    assert "# Jane" in md
    assert "## Experience" in md
    # No certifications section
    assert "## Certifications" not in md


def test_cv_to_html(sample_cv):
    html = _cv_to_html(sample_cv)
    assert "<!DOCTYPE html>" in html
    assert "<h1>" in html
    assert "Jane Doe" in html
    assert "</html>" in html


def test_cv_to_html_has_styles(sample_cv):
    html = _cv_to_html(sample_cv)
    assert "<style>" in html
    assert "font-family" in html


def test_cv_to_plaintext(sample_cv):
    txt = _cv_to_plaintext(sample_cv)
    assert "JANE DOE" in txt
    assert "Software Engineer" in txt
    assert "PROFILE" in txt
    assert "EXPERIENCE" in txt
    assert "EDUCATION" in txt
    assert "Built features" in txt
    # No markdown formatting
    assert "##" not in txt
    assert "**" not in txt
    assert "[GitHub](" not in txt


def test_cv_to_plaintext_links(sample_cv):
    txt = _cv_to_plaintext(sample_cv)
    assert "GitHub: https://github.com/janedoe" in txt


def test_cv_to_plaintext_skills(sample_cv):
    txt = _cv_to_plaintext(sample_cv)
    assert "Python" in txt
    assert "SKILLS" in txt


def test_cv_to_plaintext_optional_sections():
    """Plaintext export handles missing optional sections gracefully."""
    cv = {
        "name": "Jane",
        "title": "Dev",
        "contact": {"email": "j@test.com"},
        "experience": [{"title": "Dev", "org": "Co", "start": "2020", "end": "2021"}],
    }
    txt = _cv_to_plaintext(cv)
    assert "JANE" in txt
    assert "EXPERIENCE" in txt
    assert "CERTIFICATIONS" not in txt


def test_cv_to_markdown_custom_sections(sample_cv):
    sample_cv["awards"] = [
        {"title": "Best Paper", "org": "EuroPython", "start": "2023", "end": "2023"},
    ]
    md = _cv_to_markdown(sample_cv)
    assert "## Awards" in md
    assert "Best Paper" in md
    assert "EuroPython" in md


def test_cv_to_plaintext_custom_sections(sample_cv):
    sample_cv["awards"] = [
        {"title": "Best Paper", "org": "EuroPython", "start": "2023", "end": "2023"},
    ]
    txt = _cv_to_plaintext(sample_cv)
    assert "AWARDS" in txt
    assert "Best Paper" in txt
