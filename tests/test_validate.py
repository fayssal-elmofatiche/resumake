"""Tests for validate command."""

from resumake.schema import validate_cv


def test_validate_full_cv(sample_cv):
    """Full sample CV passes validation."""
    result = validate_cv(sample_cv)
    assert result.name == "Jane Doe"


def test_validate_with_all_sections(sample_cv):
    """CV with all optional sections passes validation."""
    sample_cv["certifications"] = [{"name": "AWS Certified", "org": "Amazon", "start": "2023", "end": "2026"}]
    sample_cv["publications"] = [{"title": "Paper Title", "year": 2024, "venue": "Conference"}]
    sample_cv["volunteering"] = [{"title": "Mentor", "org": "Code Club", "start": "2020", "end": "Present"}]
    sample_cv["references"] = "Available upon request."
    sample_cv["testimonials"] = [{"name": "John", "role": "CTO", "org": "TechCo", "quote": "Great engineer."}]
    result = validate_cv(sample_cv)
    assert len(result.certifications) == 1
    assert len(result.publications) == 1


def test_validate_rejects_bad_experience():
    """Experience entry missing required 'start' field fails."""
    import pytest
    from pydantic import ValidationError

    cv = {
        "name": "Test",
        "title": "Dev",
        "contact": {"email": "t@t.com"},
        "experience": [{"title": "Dev", "org": "Co"}],  # missing start/end
    }
    with pytest.raises(ValidationError):
        validate_cv(cv)


def test_validate_extra_fields_preserved(sample_cv):
    """Extra fields on experience entries are allowed (tech_stack, etc.)."""
    sample_cv["experience"][0]["tech_stack"] = ["Python", "React"]
    sample_cv["experience"][0]["project_methodology"] = "Agile"
    result = validate_cv(sample_cv)
    assert len(result.experience) == 1
