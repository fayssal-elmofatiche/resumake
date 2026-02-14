"""Theme system for resumake — colors, fonts, layout, sizes."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml
from docx.shared import RGBColor

PACKAGE_DIR = Path(__file__).resolve().parent
BUILTIN_THEMES_DIR = PACKAGE_DIR / "themes"


def _hex_to_rgb(hex_str: str) -> RGBColor:
    """Convert a hex string like '0F141F' to an RGBColor."""
    h = hex_str.lstrip("#")
    return RGBColor(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


@dataclass
class ThemeColors:
    primary: str = "0F141F"  # Sidebar bg, name, headings
    accent: str = "0AA8A7"  # Links, section lines, accents
    text_light: str = "FFFFFF"  # Sidebar text
    text_muted: str = "7A8599"  # Dates, secondary text
    text_body: str = "333333"  # Main body text

    @property
    def primary_rgb(self) -> RGBColor:
        return _hex_to_rgb(self.primary)

    @property
    def accent_rgb(self) -> RGBColor:
        return _hex_to_rgb(self.accent)

    @property
    def text_light_rgb(self) -> RGBColor:
        return _hex_to_rgb(self.text_light)

    @property
    def text_muted_rgb(self) -> RGBColor:
        return _hex_to_rgb(self.text_muted)

    @property
    def text_body_rgb(self) -> RGBColor:
        return _hex_to_rgb(self.text_body)


@dataclass
class ThemeFonts:
    heading: str = "Arial Narrow"
    body: str = "Calibri"


@dataclass
class ThemeLayout:
    sidebar_width_cm: float = 5.3
    main_width_cm: float = 12.7
    page_top_margin_cm: float = 1.1
    page_bottom_margin_cm: float = 1.1
    page_left_margin_cm: float = 1.4
    page_right_margin_cm: float = 1.4


@dataclass
class ThemeSizes:
    name_pt: int = 13
    heading_pt: int = 12
    subheading_pt: int = 10
    body_pt: int = 9
    small_pt: int = 8


@dataclass
class Theme:
    name: str = "classic"
    colors: ThemeColors = field(default_factory=ThemeColors)
    fonts: ThemeFonts = field(default_factory=ThemeFonts)
    layout: ThemeLayout = field(default_factory=ThemeLayout)
    sizes: ThemeSizes = field(default_factory=ThemeSizes)


def _theme_from_dict(data: dict) -> Theme:
    """Build a Theme from a parsed YAML dict."""
    colors = ThemeColors(**data["colors"]) if "colors" in data else ThemeColors()
    fonts = ThemeFonts(**data["fonts"]) if "fonts" in data else ThemeFonts()
    layout = ThemeLayout(**data["layout"]) if "layout" in data else ThemeLayout()
    sizes = ThemeSizes(**data["sizes"]) if "sizes" in data else ThemeSizes()
    return Theme(
        name=data.get("name", "custom"),
        colors=colors,
        fonts=fonts,
        layout=layout,
        sizes=sizes,
    )


def load_theme(name_or_path: Optional[str] = None) -> Theme:
    """Load a theme by name (built-in) or by file path (custom).

    Resolution order:
    1. If None, check for theme.yaml in CWD
    2. If None and no theme.yaml, use 'classic' defaults
    3. If a path to a .yaml file, load it
    4. If a name, look up in built-in themes
    """
    if name_or_path is None:
        cwd_theme = Path.cwd() / "theme.yaml"
        if cwd_theme.exists():
            with open(cwd_theme, "r", encoding="utf-8") as f:
                return _theme_from_dict(yaml.safe_load(f))
        return Theme()  # classic defaults

    path = Path(name_or_path)
    if path.suffix in (".yaml", ".yml") and path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return _theme_from_dict(yaml.safe_load(f))

    # Look up built-in theme by name
    builtin = BUILTIN_THEMES_DIR / f"{name_or_path}.yaml"
    if builtin.exists():
        with open(builtin, "r", encoding="utf-8") as f:
            return _theme_from_dict(yaml.safe_load(f))

    raise ValueError(f"Theme not found: '{name_or_path}'. Available built-in themes: {list_themes()}")


def list_themes() -> list[str]:
    """List available built-in theme names."""
    if not BUILTIN_THEMES_DIR.exists():
        return []
    return sorted(p.stem for p in BUILTIN_THEMES_DIR.glob("*.yaml"))
