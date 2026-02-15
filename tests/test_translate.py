"""Tests for translation module."""

from resumake.translate import (
    _extract_translatable,
    _merge_translation,
    _source_hash,
    _validate_translation,
)


def test_source_hash_deterministic():
    cv = {"name": "Jane Doe", "title": "Engineer"}
    assert _source_hash(cv) == _source_hash(cv)


def test_source_hash_changes_on_modification():
    cv1 = {"name": "Jane Doe", "title": "Engineer"}
    cv2 = {"name": "Jane Doe", "title": "Senior Engineer"}
    assert _source_hash(cv1) != _source_hash(cv2)


def test_validate_translation_complete():
    source = {"name": "Jane", "experience": [{"title": "Dev"}]}
    translated = {"name": "Jana", "experience": [{"title": "Entw"}]}
    assert _validate_translation(source, translated) == []


def test_validate_translation_missing_key():
    source = {"name": "Jane", "title": "Engineer", "profile": "Text"}
    translated = {"name": "Jana", "title": "Ingenieur"}
    missing = _validate_translation(source, translated)
    assert "profile" in missing


def test_validate_translation_incomplete_list():
    source = {"experience": [{"title": "A"}, {"title": "B"}, {"title": "C"}]}
    translated = {"experience": [{"title": "X"}]}
    missing = _validate_translation(source, translated)
    assert any("experience" in m for m in missing)


def test_validate_translation_all_present():
    source = {"name": "Jane", "skills": ["Python", "Java"]}
    translated = {"name": "Jana", "skills": ["Python", "Java"]}
    assert _validate_translation(source, translated) == []


def test_cache_file_naming():
    from resumake.utils import cache_file_for

    path = cache_file_for("fr")
    assert path.name == ".cv_fr_cache.yaml"
    path_de = cache_file_for("de")
    assert path_de.name == ".cv_de_cache.yaml"


# ── Extract tests ──


def test_extract_excludes_photo(sample_cv):
    sample_cv["photo"] = "profile.jpeg"
    t = _extract_translatable(sample_cv)
    assert "photo" not in t


def test_extract_excludes_name(sample_cv):
    t = _extract_translatable(sample_cv)
    assert "name" not in t


def test_extract_excludes_contact_email_phone(sample_cv):
    t = _extract_translatable(sample_cv)
    assert "email" not in t.get("contact", {})
    assert "phone" not in t.get("contact", {})


def test_extract_includes_contact_address_nationality(sample_cv):
    t = _extract_translatable(sample_cv)
    assert t["contact"]["address"] == "Berlin, Germany"
    assert t["contact"]["nationality"] == "German"


def test_extract_excludes_links(sample_cv):
    t = _extract_translatable(sample_cv)
    assert "links" not in t


def test_extract_includes_title_and_profile(sample_cv):
    t = _extract_translatable(sample_cv)
    assert t["title"] == "Software Engineer"
    assert t["profile"] == "Experienced software engineer."


def test_extract_includes_skills(sample_cv):
    t = _extract_translatable(sample_cv)
    assert t["skills"]["leadership"] == ["Team Leadership"]
    assert t["skills"]["technical"] == ["Python", "TypeScript"]
    assert t["skills"]["languages"] == [{"name": "English"}, {"name": "German"}]


def test_extract_experience_excludes_org_dates(sample_cv):
    t = _extract_translatable(sample_cv)
    exp = t["experience"][0]
    assert "org" not in exp
    assert "start" not in exp
    assert "end" not in exp
    assert exp["title"] == "Software Engineer"
    assert exp["bullets"] == ["Built features", "Led team"]


def test_extract_education_excludes_institution_dates(sample_cv):
    t = _extract_translatable(sample_cv)
    edu = t["education"][0]
    assert "institution" not in edu
    assert "start" not in edu
    assert "end" not in edu
    assert edu["degree"] == "M.Sc. Computer Science"


# ── Merge tests ──


def test_merge_preserves_photo(sample_cv):
    sample_cv["photo"] = "profile.jpeg"
    translated = {"title": "Softwareingenieur"}
    result = _merge_translation(sample_cv, translated)
    assert result["photo"] == "profile.jpeg"


def test_merge_preserves_name(sample_cv):
    translated = {"title": "Softwareingenieur"}
    result = _merge_translation(sample_cv, translated)
    assert result["name"] == "Jane Doe"


def test_merge_preserves_contact_email_phone(sample_cv):
    translated = {"contact": {"nationality": "Deutsch"}}
    result = _merge_translation(sample_cv, translated)
    assert result["contact"]["email"] == "jane@example.com"
    assert result["contact"]["phone"] == "+49 123 456"
    assert result["contact"]["nationality"] == "Deutsch"


def test_merge_preserves_links(sample_cv):
    translated = {}
    result = _merge_translation(sample_cv, translated)
    assert result["links"] == [{"label": "GitHub", "url": "https://github.com/janedoe"}]


def test_merge_preserves_experience_org_dates(sample_cv):
    translated = {"experience": [{"title": "Softwareingenieur", "bullets": ["Features gebaut"]}]}
    result = _merge_translation(sample_cv, translated)
    exp = result["experience"][0]
    assert exp["org"] == "TechCorp"
    assert exp["start"] == "March 2021"
    assert exp["end"] == "Present"
    assert exp["title"] == "Softwareingenieur"
    assert exp["bullets"] == ["Features gebaut"]


def test_merge_preserves_education_institution_dates(sample_cv):
    translated = {"education": [{"degree": "M.Sc. Informatik"}]}
    result = _merge_translation(sample_cv, translated)
    edu = result["education"][0]
    assert edu["institution"] == "TU Berlin"
    assert edu["start"] == "2014"
    assert edu["end"] == "2016"
    assert edu["degree"] == "M.Sc. Informatik"


def test_merge_overwrites_title_profile(sample_cv):
    translated = {"title": "Softwareingenieur", "profile": "Erfahrener Ingenieur."}
    result = _merge_translation(sample_cv, translated)
    assert result["title"] == "Softwareingenieur"
    assert result["profile"] == "Erfahrener Ingenieur."


def test_merge_skills_languages_preserves_level(sample_cv):
    translated = {"skills": {"languages": [{"name": "Englisch"}, {"name": "Deutsch"}]}}
    result = _merge_translation(sample_cv, translated)
    assert result["skills"]["languages"][0]["name"] == "Englisch"
    assert result["skills"]["languages"][0]["level"] == "fluent"
    assert result["skills"]["languages"][1]["name"] == "Deutsch"
    assert result["skills"]["languages"][1]["level"] == "native"


def test_roundtrip_no_data_loss(sample_cv):
    """Extract then merge with identity translation should not lose any data."""
    sample_cv["photo"] = "profile.jpeg"
    t = _extract_translatable(sample_cv)
    result = _merge_translation(sample_cv, t)
    assert result == sample_cv


# ── Custom section tests ──


def test_extract_custom_sections(sample_cv):
    sample_cv["awards"] = [
        {"title": "Best Paper", "org": "Conf", "start": "2023", "end": "2023",
         "description": "Outstanding research."},
    ]
    t = _extract_translatable(sample_cv)
    assert "awards" in t
    # org, start, end should be excluded from translation
    assert "org" not in t["awards"][0]
    assert "start" not in t["awards"][0]
    assert t["awards"][0]["title"] == "Best Paper"
    assert t["awards"][0]["description"] == "Outstanding research."


def test_extract_custom_sections_strings(sample_cv):
    sample_cv["hobbies"] = ["Reading", "Running"]
    t = _extract_translatable(sample_cv)
    assert t["hobbies"] == ["Reading", "Running"]


def test_merge_custom_sections(sample_cv):
    sample_cv["awards"] = [
        {"title": "Best Paper", "org": "Conf", "start": "2023", "end": "2023",
         "description": "Outstanding research."},
    ]
    translated = {"awards": [{"title": "Beste Arbeit", "description": "Herausragende Forschung."}]}
    result = _merge_translation(sample_cv, translated)
    assert result["awards"][0]["title"] == "Beste Arbeit"
    assert result["awards"][0]["description"] == "Herausragende Forschung."
    # Preserved non-translatable fields
    assert result["awards"][0]["org"] == "Conf"
    assert result["awards"][0]["start"] == "2023"


def test_roundtrip_custom_sections(sample_cv):
    sample_cv["awards"] = [
        {"title": "Best Paper", "org": "Conf", "start": "2023", "end": "2023"},
    ]
    sample_cv["hobbies"] = ["Reading", "Running"]
    t = _extract_translatable(sample_cv)
    result = _merge_translation(sample_cv, t)
    assert result["awards"] == sample_cv["awards"]
    assert result["hobbies"] == sample_cv["hobbies"]
