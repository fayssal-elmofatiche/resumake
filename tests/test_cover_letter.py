"""Tests for cover letter command."""

import sys
import tempfile
from pathlib import Path

from resumake.cover_letter import _build_cover_letter_docx
from resumake.theme import Theme


def test_build_cover_letter_docx(sample_cv, monkeypatch):
    """Cover letter docx builder produces a valid .docx file."""
    letter = {
        "recipient": "TechCorp",
        "subject": "Application for Senior Engineer",
        "opening": "I am writing to express my interest...",
        "body": "With 5 years of experience in Python...",
        "closing": "I look forward to discussing this opportunity.",
    }
    with tempfile.TemporaryDirectory() as tmpdir:
        monkeypatch.setattr("resumake.utils.OUTPUT_DIR", Path(tmpdir))
        cover_module = sys.modules["resumake.cover_letter"]
        monkeypatch.setattr(cover_module, "OUTPUT_DIR", Path(tmpdir))
        output = _build_cover_letter_docx(sample_cv, letter, "en", Theme())
        assert output.exists()
        assert output.suffix == ".docx"
        assert "Cover_Letter" in output.name
        assert output.stat().st_size > 0


def test_cover_letter_filename_includes_lang(sample_cv, monkeypatch):
    """Cover letter filename includes the language code."""
    letter = {
        "recipient": "Company",
        "subject": "Application",
        "opening": "Dear...",
        "body": "Body text.",
        "closing": "Closing.",
    }
    with tempfile.TemporaryDirectory() as tmpdir:
        monkeypatch.setattr("resumake.utils.OUTPUT_DIR", Path(tmpdir))
        cover_module = sys.modules["resumake.cover_letter"]
        monkeypatch.setattr(cover_module, "OUTPUT_DIR", Path(tmpdir))
        output = _build_cover_letter_docx(sample_cv, letter, "de", Theme())
        assert "DE" in output.name
