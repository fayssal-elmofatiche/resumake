"""Configuration file support for resumake (.resumakerc.yaml)."""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import yaml

CONFIG_FILENAME = ".resumakerc.yaml"

VALID_KEYS = {"lang", "theme", "pdf", "open", "source", "watch", "pdf_engine"}


@dataclass
class ResumakeConfig:
    """Resolved configuration from .resumakerc.yaml files."""

    lang: Optional[str] = None
    theme: Optional[str] = None
    pdf: Optional[bool] = None
    open: Optional[bool] = None
    source: Optional[str] = None
    watch: Optional[bool] = None
    pdf_engine: Optional[str] = None


def _load_yaml_config(path: Path) -> dict:
    """Load a single .resumakerc.yaml file, returning an empty dict if missing or invalid."""
    if not path.exists():
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if not isinstance(data, dict):
            return {}
        return {k: v for k, v in data.items() if k in VALID_KEYS}
    except Exception:
        return {}


def load_config() -> ResumakeConfig:
    """Load and merge config from .resumakerc.yaml files.

    Resolution order (later overrides earlier):
    1. ~/.resumakerc.yaml  (user-level defaults)
    2. ./.resumakerc.yaml  (project-level overrides)
    """
    merged = {}

    home_config = Path.home() / CONFIG_FILENAME
    merged.update(_load_yaml_config(home_config))

    project_config = Path.cwd() / CONFIG_FILENAME
    merged.update(_load_yaml_config(project_config))

    return ResumakeConfig(**{k: v for k, v in merged.items() if k in VALID_KEYS})


def resolve(cli_value, config_value, default):
    """Three-way merge: CLI (if not None) > config > hardcoded default."""
    if cli_value is not None:
        return cli_value
    if config_value is not None:
        return config_value
    return default
