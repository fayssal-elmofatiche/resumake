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


class OpenAIProvider(LLMProvider):
    """OpenAI provider (works with any OpenAI-compatible API)."""

    def __init__(self, api_key: str, model: str = "gpt-4o", base_url: str | None = None):
        import openai

        kwargs = {"api_key": api_key}
        if base_url:
            kwargs["base_url"] = base_url
        self.client = openai.OpenAI(**kwargs)
        self.model = model

    def complete(self, prompt: str, max_tokens: int = 4096) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content.strip()


def get_provider() -> LLMProvider:
    """Auto-detect and return an LLM provider from environment variables.

    Checks in order: ANTHROPIC_API_KEY, OPENAI_API_KEY.
    Supports OPENAI_BASE_URL for OpenAI-compatible APIs (e.g. Ollama, LiteLLM).
    Raises RuntimeError if no provider is available.
    """
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    if anthropic_key:
        try:
            return AnthropicProvider(api_key=anthropic_key)
        except ImportError:
            raise RuntimeError(
                "ANTHROPIC_API_KEY is set but 'anthropic' package is not installed.\n"
                "Install with: uv tool install resumakeai --with anthropic"
            )

    openai_key = os.environ.get("OPENAI_API_KEY")
    if openai_key:
        try:
            base_url = os.environ.get("OPENAI_BASE_URL")
            model = os.environ.get("OPENAI_MODEL", "gpt-4o")
            return OpenAIProvider(api_key=openai_key, model=model, base_url=base_url)
        except ImportError:
            raise RuntimeError(
                "OPENAI_API_KEY is set but 'openai' package is not installed.\n"
                "Install with: uv tool install resumakeai --with openai"
            )

    raise RuntimeError(
        "No LLM provider configured.\n"
        "Set one of: ANTHROPIC_API_KEY, OPENAI_API_KEY\n"
        "Install with: uv tool install resumakeai --with anthropic  (or --with openai)"
    )
