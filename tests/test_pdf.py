"""Tests for PDF conversion module."""

import pytest

from resumake.pdf import convert_to_pdf_auto, convert_to_pdf_docx2pdf, convert_to_pdf_weasyprint


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
