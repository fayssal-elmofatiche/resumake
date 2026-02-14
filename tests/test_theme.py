"""Tests for theme system."""

import pytest

from resumake.theme import Theme, list_themes, load_theme


def test_default_theme():
    theme = Theme()
    assert theme.name == "classic"
    assert theme.colors.primary == "0F141F"
    assert theme.fonts.heading == "Arial Narrow"


def test_load_classic_theme():
    theme = load_theme("classic")
    assert theme.name == "classic"
    assert theme.colors.primary == "0F141F"


def test_load_minimal_theme():
    theme = load_theme("minimal")
    assert theme.name == "minimal"
    assert theme.colors.primary != "0F141F"


def test_load_modern_theme():
    theme = load_theme("modern")
    assert theme.name == "modern"


def test_load_nonexistent_theme():
    with pytest.raises(ValueError, match="Theme not found"):
        load_theme("nonexistent")


def test_list_themes():
    themes = list_themes()
    assert "classic" in themes
    assert "minimal" in themes
    assert "modern" in themes


def test_theme_colors_rgb():
    from docx.shared import RGBColor

    theme = Theme()
    rgb = theme.colors.primary_rgb
    assert isinstance(rgb, RGBColor)
    assert str(rgb) == "0F141F"


def test_load_none_returns_default():
    theme = load_theme(None)
    assert theme.name == "classic"
