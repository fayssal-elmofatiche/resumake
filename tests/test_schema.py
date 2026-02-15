"""Tests for schema validation."""

import pytest
from pydantic import ValidationError

from resumake.schema import get_custom_sections, validate_cv


def test_valid_cv(sample_cv):
    result = validate_cv(sample_cv)
    assert result.name == "Jane Doe"
    assert result.title == "Software Engineer"
    assert len(result.experience) == 1


def test_missing_required_fields():
    with pytest.raises(ValidationError) as exc_info:
        validate_cv({"title": "Engineer"})
    errors = exc_info.value.errors()
    error_fields = {e["loc"][0] for e in errors}
    assert "name" in error_fields
    assert "contact" in error_fields
    assert "experience" in error_fields


def test_extra_fields_in_experience(sample_cv):
    sample_cv["experience"][0]["tech_stack"] = ["Python", "React"]
    sample_cv["experience"][0]["custom_field"] = "allowed"
    result = validate_cv(sample_cv)
    assert len(result.experience) == 1


def test_minimal_cv():
    cv = {
        "name": "Test",
        "title": "Dev",
        "contact": {"email": "test@test.com"},
        "experience": [{"title": "Dev", "org": "Co", "start": "2020", "end": "2021"}],
    }
    result = validate_cv(cv)
    assert result.name == "Test"


def test_optional_sections(sample_cv):
    # All optional sections can be omitted
    minimal = {
        "name": sample_cv["name"],
        "title": sample_cv["title"],
        "contact": sample_cv["contact"],
        "experience": sample_cv["experience"],
    }
    result = validate_cv(minimal)
    assert result.education is None
    assert result.certifications is None
    assert result.publications is None


def test_custom_sections_accepted(sample_cv):
    sample_cv["awards"] = [{"title": "Best Paper", "org": "Conf", "start": "2023", "end": "2023"}]
    result = validate_cv(sample_cv)
    assert result.name == "Jane Doe"


def test_get_custom_sections(sample_cv):
    sample_cv["awards"] = [{"title": "Best Paper"}]
    sample_cv["patents"] = [{"title": "Patent X"}]
    custom = get_custom_sections(sample_cv)
    assert "awards" in custom
    assert "patents" in custom
    assert "experience" not in custom
    assert "name" not in custom


def test_custom_non_list_ignored(sample_cv):
    sample_cv["awards"] = [{"title": "Best Paper"}]
    sample_cv["motto"] = "Work hard"  # string, not list → not a custom section
    custom = get_custom_sections(sample_cv)
    assert "awards" in custom
    assert "motto" not in custom
