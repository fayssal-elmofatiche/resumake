"""Tests for docx builder."""

import tempfile
from pathlib import Path

from resumake.docx_builder import build_docx
from resumake.theme import Theme


def test_build_docx_produces_file(sample_cv, monkeypatch):
    with tempfile.TemporaryDirectory() as tmpdir:
        monkeypatch.setattr("resumake.utils.OUTPUT_DIR", Path(tmpdir))
        output = build_docx(sample_cv, "en", theme=Theme())
        assert output.exists()
        assert output.suffix == ".docx"
        assert output.stat().st_size > 0


def test_build_docx_filename_from_name(sample_cv, monkeypatch):
    with tempfile.TemporaryDirectory() as tmpdir:
        monkeypatch.setattr("resumake.utils.OUTPUT_DIR", Path(tmpdir))
        output = build_docx(sample_cv, "en", theme=Theme())
        assert "Jane_Doe" in output.name
        assert "CV_EN" in output.name


def test_build_docx_with_minimal_theme(sample_cv, monkeypatch):
    from resumake.theme import load_theme

    with tempfile.TemporaryDirectory() as tmpdir:
        monkeypatch.setattr("resumake.utils.OUTPUT_DIR", Path(tmpdir))
        theme = load_theme("minimal")
        output = build_docx(sample_cv, "en", theme=theme)
        assert output.exists()


def test_build_docx_with_custom_sections(sample_cv, monkeypatch):
    sample_cv["awards"] = [
        {
            "title": "Best Paper",
            "org": "EuroPython",
            "start": "2023",
            "end": "2023",
            "description": "Awarded for outstanding research.",
        },
        {"title": "Employee of the Year", "org": "TechCorp"},
    ]
    sample_cv["projects"] = ["Open Source CLI tool", "Internal dashboard"]
    with tempfile.TemporaryDirectory() as tmpdir:
        monkeypatch.setattr("resumake.utils.OUTPUT_DIR", Path(tmpdir))
        output = build_docx(sample_cv, "en", theme=Theme())
        assert output.exists()
        assert output.stat().st_size > 0


def test_build_single_column(sample_cv, monkeypatch):
    from resumake.theme import load_theme

    with tempfile.TemporaryDirectory() as tmpdir:
        monkeypatch.setattr("resumake.utils.OUTPUT_DIR", Path(tmpdir))
        theme = load_theme("single-column")
        output = build_docx(sample_cv, "en", theme=theme)
        assert output.exists()
        assert output.stat().st_size > 0


def test_build_academic(sample_cv, monkeypatch):
    from resumake.theme import load_theme

    with tempfile.TemporaryDirectory() as tmpdir:
        monkeypatch.setattr("resumake.utils.OUTPUT_DIR", Path(tmpdir))
        theme = load_theme("academic")
        output = build_docx(sample_cv, "en", theme=theme)
        assert output.exists()


def test_build_compact(sample_cv, monkeypatch):
    from resumake.theme import load_theme

    with tempfile.TemporaryDirectory() as tmpdir:
        monkeypatch.setattr("resumake.utils.OUTPUT_DIR", Path(tmpdir))
        theme = load_theme("compact")
        output = build_docx(sample_cv, "en", theme=theme)
        assert output.exists()


def test_build_default_two_column(sample_cv, monkeypatch):
    with tempfile.TemporaryDirectory() as tmpdir:
        monkeypatch.setattr("resumake.utils.OUTPUT_DIR", Path(tmpdir))
        theme = Theme()
        assert theme.layout.layout_type == "two-column"
        output = build_docx(sample_cv, "en", theme=theme)
        assert output.exists()
