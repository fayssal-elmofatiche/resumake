"""Shared test fixtures."""

import pytest


@pytest.fixture
def sample_cv():
    """Minimal valid CV dict for testing."""
    return {
        "name": "Jane Doe",
        "title": "Software Engineer",
        "photo": "",
        "contact": {
            "address": "Berlin, Germany",
            "phone": "+49 123 456",
            "email": "jane@example.com",
            "nationality": "German",
        },
        "links": [{"label": "GitHub", "url": "https://github.com/janedoe"}],
        "skills": {
            "leadership": ["Team Leadership"],
            "technical": ["Python", "TypeScript"],
            "languages": [
                {"name": "English", "level": "fluent"},
                {"name": "German", "level": "native"},
            ],
        },
        "profile": "Experienced software engineer.",
        "experience": [
            {
                "title": "Software Engineer",
                "org": "TechCorp",
                "start": "March 2021",
                "end": "Present",
                "bullets": ["Built features", "Led team"],
            }
        ],
        "education": [
            {
                "degree": "M.Sc. Computer Science",
                "institution": "TU Berlin",
                "start": "2014",
                "end": "2016",
            }
        ],
    }
