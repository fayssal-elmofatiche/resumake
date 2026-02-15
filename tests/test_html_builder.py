"""Tests for HTML builder."""

from resumake.html_builder import build_html
from resumake.theme import Theme, ThemeColors


def test_build_html_doctype(sample_cv):
    html = build_html(sample_cv, "en", theme=Theme())
    assert "<!DOCTYPE html>" in html
    assert "</html>" in html


def test_build_html_has_theme_colors(sample_cv):
    theme = Theme(colors=ThemeColors(primary="1A1A2E", accent="E94560"))
    html = build_html(sample_cv, "en", theme=theme)
    assert "1A1A2E" in html
    assert "E94560" in html


def test_build_html_two_column_structure(sample_cv):
    html = build_html(sample_cv, "en", theme=Theme())
    assert 'class="cv-container"' in html
    assert 'class="sidebar"' in html
    assert 'class="main"' in html


def test_build_html_all_sections(sample_cv):
    html = build_html(sample_cv, "en", theme=Theme())
    assert "Jane Doe" in html
    assert "Software Engineer" in html
    assert "Profile" in html
    assert "Built features" in html
    assert "M.Sc. Computer Science" in html


def test_build_html_lang_attribute(sample_cv):
    html = build_html(sample_cv, "de", theme=Theme())
    assert 'lang="de"' in html


def test_build_html_custom_sections(sample_cv):
    sample_cv["awards"] = [
        {"title": "Best Paper", "org": "EuroPython", "start": "2023", "end": "2023"},
    ]
    html = build_html(sample_cv, "en", theme=Theme())
    assert "Awards" in html
    assert "Best Paper" in html


def test_build_html_escapes_special_chars(sample_cv):
    sample_cv["profile"] = "Experience with <script> & HTML"
    html = build_html(sample_cv, "en", theme=Theme())
    assert "&lt;script&gt;" in html
    assert "&amp; HTML" in html


def test_build_html_links(sample_cv):
    html = build_html(sample_cv, "en", theme=Theme())
    assert 'href="https://github.com/janedoe"' in html
    assert "GitHub" in html
