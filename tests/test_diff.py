"""Tests for diff command."""

from resumake.diff_cmd import _flatten


def test_flatten_simple():
    data = {"name": "Jane", "title": "Dev"}
    result = _flatten(data)
    assert result == {"name": "Jane", "title": "Dev"}


def test_flatten_nested():
    data = {"contact": {"email": "j@test.com", "phone": "123"}}
    result = _flatten(data)
    assert result["contact.email"] == "j@test.com"
    assert result["contact.phone"] == "123"


def test_flatten_list_of_dicts():
    data = {"experience": [{"title": "Dev", "org": "Co"}]}
    result = _flatten(data)
    assert "experience[Dev].org" in result
    assert result["experience[Dev].org"] == "Co"


def test_flatten_list_of_strings():
    data = {"skills": ["Python", "Java"]}
    result = _flatten(data)
    assert result["skills[0]"] == "Python"
    assert result["skills[1]"] == "Java"


def test_flatten_empty():
    assert _flatten({}) == {}


def test_flatten_deeply_nested():
    data = {"a": {"b": {"c": "value"}}}
    result = _flatten(data)
    assert result["a.b.c"] == "value"
