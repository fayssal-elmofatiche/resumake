"""LLM provider abstraction for resumake."""

import os
from abc import ABC, abstractmethod


def strip_yaml_fences(text: str) -> str:
    """Remove markdown code fences from YAML output."""
    text = text.strip()
    if text.startswith("```"):
        text = "\n".join(text.split("\n")[1:])
    if text.endswith("```"):
        text = "\n".join(text.split("\n")[:-1])
    return text.strip()


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    def complete(self, prompt: str, max_tokens: int = 4096) -> str:
        """Send a prompt and return the text response."""
        ...


class AnthropicProvider(LLMProvider):
    """Anthropic Claude provider."""

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-5-20250929"):
        import anthropic
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model

    def complete(self, prompt: str, max_tokens: int = 4096) -> str:
        message = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text.strip()


def get_provider() -> LLMProvider:
    """Auto-detect and return an LLM provider from environment variables.

    Currently supports Anthropic (ANTHROPIC_API_KEY).
    Raises RuntimeError if no provider is available.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if api_key:
        try:
            return AnthropicProvider(api_key=api_key)
        except ImportError:
            raise RuntimeError(
                "Anthropic API key found but 'anthropic' package is not installed.\n"
                "Install with: pip install resumake[ai]"
            )

    raise RuntimeError(
        "No LLM provider configured.\n"
        "Set ANTHROPIC_API_KEY to enable AI features, or install with: pip install resumake[ai]"
    )
