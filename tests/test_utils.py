"""Tests for utils module."""

from resumake.utils import parse_start_date, slugify_name, validate_photo


def test_slugify_name_simple():
    assert slugify_name("Jane Doe") == "Jane_Doe"


def test_slugify_name_with_comma():
    assert slugify_name("Jane Doe, PhD") == "Jane_Doe_PhD"


def test_slugify_name_special_chars():
    assert slugify_name("Dr. Jane-Doe (PhD)") == "Dr_JaneDoe_PhD"


def test_parse_start_date_month_year():
    assert parse_start_date("March 2021") == (2021, 3)


def test_parse_start_date_german():
    assert parse_start_date("März 2020") == (2020, 3)


def test_parse_start_date_year_only():
    assert parse_start_date("2014") == (2014, 0)


def test_parse_start_date_empty():
    assert parse_start_date("") == (0, 0)


def test_parse_start_date_invalid():
    assert parse_start_date("Present") == (0, 0)


def test_validate_photo_missing(tmp_path, monkeypatch):
    monkeypatch.setattr("resumake.utils.ASSETS_DIR", tmp_path / "assets")
    monkeypatch.setattr("resumake.utils.BUILTIN_ASSETS_DIR", tmp_path / "builtin")
    warnings = validate_photo("nonexistent.jpg")
    assert len(warnings) == 1
    assert "not found" in warnings[0]


def test_validate_photo_empty():
    assert validate_photo("") == []
    assert validate_photo(None) == []


def test_validate_photo_unsupported_format(tmp_path, monkeypatch):
    monkeypatch.setattr("resumake.utils.ASSETS_DIR", tmp_path)
    (tmp_path / "photo.bmp").write_bytes(b"fake")
    warnings = validate_photo("photo.bmp")
    assert len(warnings) == 1
    assert "unsupported format" in warnings[0]


def test_validate_photo_too_large(tmp_path, monkeypatch):
    monkeypatch.setattr("resumake.utils.ASSETS_DIR", tmp_path)
    big_file = tmp_path / "photo.jpg"
    big_file.write_bytes(b"x" * (6 * 1024 * 1024))  # 6 MB
    warnings = validate_photo("photo.jpg")
    assert len(warnings) == 1
    assert "MB" in warnings[0]


def test_validate_photo_valid(tmp_path, monkeypatch):
    monkeypatch.setattr("resumake.utils.ASSETS_DIR", tmp_path)
    (tmp_path / "photo.png").write_bytes(b"fake png data")
    warnings = validate_photo("photo.png")
    assert warnings == []
