"""Tests for utils module."""

from resumake.utils import slugify_name, parse_start_date


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
