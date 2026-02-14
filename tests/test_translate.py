"""Tests for translation module."""

from resumake.translate import _source_hash, _validate_translation


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
