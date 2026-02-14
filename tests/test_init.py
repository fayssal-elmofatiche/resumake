"""Tests for init command."""

import tempfile
from pathlib import Path

from resumake.init_cmd import TEMPLATES_DIR
from resumake.utils import BUILTIN_ASSETS_DIR


def test_templates_dir_exists():
    assert TEMPLATES_DIR.exists()
    assert (TEMPLATES_DIR / "cv.example.yaml").exists()


def test_builtin_assets_exist():
    assert BUILTIN_ASSETS_DIR.exists()
    icons = list(BUILTIN_ASSETS_DIR.glob("*.png"))
    assert len(icons) > 0


def test_init_creates_project(monkeypatch):
    """init scaffolds cv.yaml, assets/, output/, and .gitignore."""
    from resumake.init_cmd import init

    with tempfile.TemporaryDirectory() as tmpdir:
        target = Path(tmpdir) / "test-cv"
        # Typer calls invoke, we call the function directly
        init(directory=target)

        assert (target / "cv.yaml").exists()
        assert (target / "assets").is_dir()
        assert (target / "output").is_dir()
        assert (target / ".gitignore").exists()

        # Check gitignore content
        gitignore = (target / ".gitignore").read_text()
        assert "output/" in gitignore

        # Check icons were copied
        icons = list((target / "assets").glob("*.png"))
        assert len(icons) > 0


def test_init_does_not_overwrite_existing(monkeypatch):
    """init skips cv.yaml if it already exists."""
    from resumake.init_cmd import init

    with tempfile.TemporaryDirectory() as tmpdir:
        target = Path(tmpdir) / "test-cv"
        target.mkdir()
        existing_cv = target / "cv.yaml"
        existing_cv.write_text("name: Existing")

        init(directory=target)

        # Should not overwrite
        assert existing_cv.read_text() == "name: Existing"
