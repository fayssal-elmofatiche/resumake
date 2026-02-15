"""Tests for ATS keyword optimization command."""

import json

import pytest


def test_ats_no_provider(monkeypatch):
    """Should raise SystemExit without an LLM provider."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    from resumake.ats_cmd import analyze_ats_match

    with pytest.raises(SystemExit):
        analyze_ats_match({"name": "Jane"}, "Looking for a Python developer")


def test_ats_return_structure():
    """Verify expected return structure when we mock the LLM."""
    from resumake.ats_cmd import analyze_ats_match

    mock_response = json.dumps({
        "score": 75,
        "matched_keywords": ["Python", "Docker"],
        "missing_keywords": ["Kubernetes"],
        "suggestions": [{"keyword": "Kubernetes", "where_to_add": "skills", "phrasing": "Add to technical skills"}],
        "summary": "Good match overall.",
    })

    class MockProvider:
        def complete(self, prompt, max_tokens=4096):
            return mock_response

    import resumake.llm

    orig = resumake.llm.get_provider

    def mock_get():
        return MockProvider()

    resumake.llm.get_provider = mock_get
    try:
        result = analyze_ats_match({"name": "Jane"}, "Python and Kubernetes developer needed")
        assert result["score"] == 75
        assert "Python" in result["matched_keywords"]
        assert "Kubernetes" in result["missing_keywords"]
        assert len(result["suggestions"]) == 1
    finally:
        resumake.llm.get_provider = orig


def test_ats_missing_file():
    """ATS command should reject missing file."""
    from click.exceptions import Exit

    from resumake.ats_cmd import ats

    with pytest.raises(Exit):
        ats(description_file=__import__("pathlib").Path("/nonexistent"))
