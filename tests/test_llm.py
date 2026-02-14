"""Tests for LLM module."""

from resumake.llm import strip_yaml_fences


def test_strip_yaml_fences_plain():
    assert strip_yaml_fences("name: Jane") == "name: Jane"


def test_strip_yaml_fences_with_backticks():
    text = "```yaml\nname: Jane\n```"
    assert strip_yaml_fences(text) == "name: Jane"


def test_strip_yaml_fences_with_backticks_no_lang():
    text = "```\nname: Jane\n```"
    assert strip_yaml_fences(text) == "name: Jane"


def test_strip_yaml_fences_strips_whitespace():
    text = "  \n```yaml\nname: Jane\n```\n  "
    assert strip_yaml_fences(text) == "name: Jane"


def test_get_provider_no_keys(monkeypatch):
    """get_provider raises RuntimeError when no API keys are set."""
    import pytest

    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    from resumake.llm import get_provider

    with pytest.raises(RuntimeError, match="No LLM provider configured"):
        get_provider()
