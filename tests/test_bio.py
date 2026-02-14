"""Tests for bio command."""

import sys
import tempfile
from pathlib import Path

from resumake.bio import build_bio_docx, select_bio_content_deterministic
from resumake.theme import Theme


def test_deterministic_bio_selection(sample_cv):
    """Deterministic bio selection extracts correct fields."""
    bio = select_bio_content_deterministic(sample_cv)
    assert bio["name"] == "Jane Doe"
    assert bio["title"] == "Software Engineer"
    assert bio["contact"]["email"] == "jane@example.com"
    assert len(bio["current_roles"]) > 0
    assert len(bio["career_highlights"]) > 0
    assert bio["skills_summary"]  # non-empty


def test_deterministic_bio_roles_sorted(sample_cv):
    """Current roles are taken from most recent experience."""
    sample_cv["experience"].append(
        {
            "title": "Junior Dev",
            "org": "OldCorp",
            "start": "January 2015",
            "end": "December 2018",
            "bullets": ["Old work"],
        }
    )
    bio = select_bio_content_deterministic(sample_cv)
    # Most recent should be first (March 2021 > January 2015)
    assert bio["current_roles"][0]["title"] == "Software Engineer"


def test_build_bio_docx_produces_file(sample_cv, monkeypatch):
    """Bio docx builder produces a valid .docx file."""
    bio = select_bio_content_deterministic(sample_cv)
    with tempfile.TemporaryDirectory() as tmpdir:
        monkeypatch.setattr("resumake.utils.OUTPUT_DIR", Path(tmpdir))
        bio_module = sys.modules["resumake.bio"]
        monkeypatch.setattr(bio_module, "OUTPUT_DIR", Path(tmpdir))
        output = build_bio_docx(bio, "en", theme=Theme())
        assert output.exists()
        assert output.suffix == ".docx"
        assert "Bio" in output.name


def test_deterministic_bio_no_bullets():
    """Bio selection handles experience entries without bullets."""
    cv = {
        "name": "Test",
        "title": "Dev",
        "contact": {"email": "t@t.com", "phone": "123", "address": "Berlin"},
        "skills": {"technical": ["Python"]},
        "profile": "A developer.",
        "experience": [{"title": "Dev", "org": "Co", "start": "2020", "end": "2021"}],
        "education": [{"degree": "BSc", "institution": "Uni"}],
        "links": [],
    }
    bio = select_bio_content_deterministic(cv)
    assert bio["name"] == "Test"
    assert bio["career_highlights"] == []
