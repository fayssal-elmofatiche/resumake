"""Tests for LinkedIn PDF import."""

import pytest


def test_extract_linkedin_text_import_error(tmp_path, monkeypatch):
    """Should raise SystemExit if pdfplumber is not installed."""
    original_import = __builtins__.__import__ if hasattr(__builtins__, "__import__") else __import__

    def mock_import(name, *args, **kwargs):
        if name == "pdfplumber":
            raise ImportError("No module named 'pdfplumber'")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr("builtins.__import__", mock_import)
    from resumake.linkedin import extract_linkedin_text

    with pytest.raises(SystemExit):
        extract_linkedin_text(tmp_path / "profile.pdf")


def test_linkedin_to_cv_no_provider(monkeypatch):
    """Should raise SystemExit if no LLM provider is available."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    from resumake.linkedin import linkedin_to_cv

    with pytest.raises(SystemExit):
        linkedin_to_cv("Jane Doe\nSoftware Engineer\nBerlin")
