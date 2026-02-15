"""Tests for content suggestions command."""

import pytest


def test_suggest_no_provider(monkeypatch):
    """Should raise SystemExit without an LLM provider."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    from resumake.suggest_cmd import suggest_improvements

    with pytest.raises(SystemExit):
        suggest_improvements({"name": "Jane", "title": "Dev", "experience": []})


def test_suggest_return_structure():
    """Verify expected return structure when we mock the LLM."""
    import json

    from resumake.suggest_cmd import suggest_improvements

    mock_response = json.dumps({
        "suggestions": [{"section": "experience", "original": "Did stuff", "suggested": "Led X", "reason": "better"}],
        "general": ["Add metrics"],
    })

    class MockProvider:
        def complete(self, prompt, max_tokens=4096):
            return mock_response

    # Patch get_provider
    import resumake.llm

    orig = resumake.llm.get_provider

    def mock_get():
        return MockProvider()

    resumake.llm.get_provider = mock_get
    try:
        result = suggest_improvements({"name": "Jane", "title": "Dev"})
        assert "suggestions" in result
        assert len(result["suggestions"]) == 1
        assert result["suggestions"][0]["section"] == "experience"
        assert "general" in result
    finally:
        resumake.llm.get_provider = orig
