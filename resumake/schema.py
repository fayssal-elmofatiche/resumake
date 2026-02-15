"""Pydantic schema for CV YAML validation."""

from typing import Optional

from pydantic import BaseModel


class Contact(BaseModel):
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    nationality: Optional[str] = None


class Link(BaseModel):
    label: str
    url: str


class Language(BaseModel):
    name: str
    level: str


class Skills(BaseModel):
    leadership: Optional[list[str]] = None
    technical: Optional[list[str]] = None
    languages: Optional[list[Language]] = None


class Testimonial(BaseModel):
    name: str
    role: str
    org: str
    quote: str


class Experience(BaseModel):
    model_config = {"extra": "allow"}

    title: str
    org: str
    start: str
    end: str
    description: Optional[str] = None
    bullets: Optional[list[str]] = None


class Education(BaseModel):
    degree: str
    institution: str
    start: str
    end: str
    description: Optional[str] = None
    details: Optional[str] = None


class Volunteering(BaseModel):
    title: str
    org: str
    start: str
    end: str
    description: Optional[str] = None


class Certification(BaseModel):
    name: str
    org: Optional[str] = None
    start: str
    end: str
    description: Optional[str] = None


class Publication(BaseModel):
    title: str
    year: int
    venue: str


KNOWN_KEYS = {
    "name",
    "title",
    "photo",
    "contact",
    "links",
    "skills",
    "profile",
    "testimonials",
    "experience",
    "education",
    "volunteering",
    "references",
    "certifications",
    "publications",
}


class CVSchema(BaseModel):
    model_config = {"extra": "allow"}

    name: str
    title: str
    photo: Optional[str] = None
    contact: Contact
    links: Optional[list[Link]] = None
    skills: Optional[Skills] = None
    profile: Optional[str] = None
    testimonials: Optional[list[Testimonial]] = None
    experience: list[Experience]
    education: Optional[list[Education]] = None
    volunteering: Optional[list[Volunteering]] = None
    references: Optional[str] = None
    certifications: Optional[list[Certification]] = None
    publications: Optional[list[Publication]] = None


def get_custom_sections(cv: dict) -> dict[str, list]:
    """Return custom sections — any top-level list not in the known schema keys."""
    return {k: v for k, v in cv.items() if k not in KNOWN_KEYS and isinstance(v, list)}


def validate_cv(data: dict) -> CVSchema:
    """Validate CV data against the schema. Raises ValidationError on failure."""
    return CVSchema(**data)
