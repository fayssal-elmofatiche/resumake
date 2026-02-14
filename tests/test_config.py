"""Tests for config file loading and merging."""

from pathlib import Path

from resumake.config import ResumakeConfig, _load_yaml_config, load_config, resolve


def test_resolve_cli_overrides_config():
    assert resolve("en", "de", "en,de") == "en"


def test_resolve_config_overrides_default():
    assert resolve(None, "de", "en,de") == "de"


def test_resolve_falls_back_to_default():
    assert resolve(None, None, "en,de") == "en,de"


def test_resolve_cli_false_overrides_config_true():
    """Explicit False from CLI should override True from config."""
    assert resolve(False, True, False) is False


def test_load_yaml_config_missing_file(tmp_path):
    result = _load_yaml_config(tmp_path / "nonexistent.yaml")
    assert result == {}


def test_load_yaml_config_valid(tmp_path):
    config_file = tmp_path / ".resumakerc.yaml"
    config_file.write_text("lang: en\ntheme: modern\npdf: true\n")
    result = _load_yaml_config(config_file)
    assert result == {"lang": "en", "theme": "modern", "pdf": True}


def test_load_yaml_config_ignores_unknown_keys(tmp_path):
    config_file = tmp_path / ".resumakerc.yaml"
    config_file.write_text("lang: en\nunknown_key: value\n")
    result = _load_yaml_config(config_file)
    assert result == {"lang": "en"}
    assert "unknown_key" not in result


def test_load_yaml_config_handles_invalid_yaml(tmp_path):
    config_file = tmp_path / ".resumakerc.yaml"
    config_file.write_text(": invalid: yaml: [[[")
    result = _load_yaml_config(config_file)
    assert result == {}


def test_load_yaml_config_handles_non_dict(tmp_path):
    config_file = tmp_path / ".resumakerc.yaml"
    config_file.write_text("- list\n- not\n- dict\n")
    result = _load_yaml_config(config_file)
    assert result == {}


def test_load_config_project_overrides_home(monkeypatch, tmp_path):
    home_dir = tmp_path / "home"
    home_dir.mkdir()
    (home_dir / ".resumakerc.yaml").write_text("lang: en\ntheme: classic\n")

    project_dir = tmp_path / "project"
    project_dir.mkdir()
    (project_dir / ".resumakerc.yaml").write_text("theme: modern\npdf: true\n")

    monkeypatch.setattr(Path, "home", staticmethod(lambda: home_dir))
    monkeypatch.chdir(project_dir)

    cfg = load_config()
    assert cfg.lang == "en"  # from home
    assert cfg.theme == "modern"  # project overrides home
    assert cfg.pdf is True  # from project


def test_resumake_config_defaults():
    cfg = ResumakeConfig()
    assert cfg.lang is None
    assert cfg.theme is None
    assert cfg.pdf is None
    assert cfg.open is None
    assert cfg.source is None
    assert cfg.watch is None
