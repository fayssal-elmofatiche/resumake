"""Tests for JSON Resume bidirectional mapping."""

from resumake.jsonresume import cv_to_json_resume, json_resume_to_cv, validate_json_resume


def test_basics_mapping(sample_cv):
    jr = cv_to_json_resume(sample_cv)
    assert jr["basics"]["name"] == "Jane Doe"
    assert jr["basics"]["label"] == "Software Engineer"
    assert jr["basics"]["email"] == "jane@example.com"
    assert jr["basics"]["phone"] == "+49 123 456"


def test_work_mapping(sample_cv):
    jr = cv_to_json_resume(sample_cv)
    assert len(jr["work"]) == 1
    assert jr["work"][0]["position"] == "Software Engineer"
    assert jr["work"][0]["name"] == "TechCorp"
    assert jr["work"][0]["highlights"] == ["Built features", "Led team"]


def test_education_mapping(sample_cv):
    jr = cv_to_json_resume(sample_cv)
    assert len(jr["education"]) == 1
    assert jr["education"][0]["studyType"] == "M.Sc. Computer Science"
    assert jr["education"][0]["institution"] == "TU Berlin"


def test_skills_flattening(sample_cv):
    jr = cv_to_json_resume(sample_cv)
    assert any(s["name"] == "Leadership" for s in jr["skills"])
    assert any(s["name"] == "Technical" for s in jr["skills"])


def test_languages_mapping(sample_cv):
    jr = cv_to_json_resume(sample_cv)
    assert len(jr["languages"]) == 2
    assert jr["languages"][0]["language"] == "English"


def test_reverse_mapping():
    jr = {
        "basics": {
            "name": "Jane Doe",
            "label": "Engineer",
            "email": "jane@test.com",
            "location": {"address": "Berlin"},
            "profiles": [{"network": "GitHub", "url": "https://github.com/jane"}],
        },
        "work": [
            {"name": "Corp", "position": "Dev", "startDate": "2020", "endDate": "2021",
             "highlights": ["Built stuff"]},
        ],
        "education": [
            {"institution": "Uni", "studyType": "M.Sc.", "startDate": "2016", "endDate": "2018"},
        ],
    }
    cv = json_resume_to_cv(jr)
    assert cv["name"] == "Jane Doe"
    assert cv["title"] == "Engineer"
    assert cv["contact"]["email"] == "jane@test.com"
    assert cv["links"][0]["label"] == "GitHub"
    assert cv["experience"][0]["title"] == "Dev"
    assert cv["experience"][0]["bullets"] == ["Built stuff"]
    assert cv["education"][0]["degree"] == "M.Sc."


def test_roundtrip(sample_cv):
    """Converting to JSON Resume and back should preserve key fields."""
    jr = cv_to_json_resume(sample_cv)
    cv2 = json_resume_to_cv(jr)
    assert cv2["name"] == sample_cv["name"]
    assert cv2["title"] == sample_cv["title"]
    assert cv2["contact"]["email"] == sample_cv["contact"]["email"]
    assert len(cv2["experience"]) == len(sample_cv["experience"])
    assert cv2["experience"][0]["title"] == sample_cv["experience"][0]["title"]


def test_validation_missing_basics():
    issues = validate_json_resume({})
    assert any("basics" in i for i in issues)


def test_validation_missing_name():
    issues = validate_json_resume({"basics": {}})
    assert any("name" in i for i in issues)


def test_validation_valid():
    issues = validate_json_resume({"basics": {"name": "Jane"}})
    assert issues == []
