"""
backend/resume_store.py
-------------------------
Data model for the ATS Resume Builder + persistence into the new
"Users Resume Details" Google Sheet.

Reuses backend/sheets_client.py's existing generic `append_row` /
`read_rows` API exactly as-is - no changes to that module. Since Sheets
rows are flat, multi-entry sections (projects, certificates, internships)
are serialized to JSON strings in their own columns and parsed back on
read.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any

from config import SHEETS_CONFIG
from backend.sheets_client import append_row, read_rows
from backend.logger_setup import get_logger

logger = get_logger(__name__)


@dataclass
class ProjectEntry:
    title: str = ""
    description: str = ""
    tech_stack: str = ""


@dataclass
class CertificateEntry:
    name: str = ""
    issuer: str = ""
    year: str = ""


@dataclass
class InternshipEntry:
    role: str = ""
    company: str = ""
    duration: str = ""
    description: str = ""


@dataclass
class ResumeProfile:
    first_name: str = ""
    last_name: str = ""
    email: str = ""
    phone: str = ""
    address: str = ""
    linkedin: str = ""
    github: str = ""
    portfolio: str = ""
    career_objective: str = ""
    education: str = ""              # free text - degree/institution/year, one per line
    skills: list[str] = field(default_factory=list)
    achievements: str = ""            # free text, one per line
    languages: list[str] = field(default_factory=list)
    hobbies: list[str] = field(default_factory=list)
    references: str = ""              # free text, optional
    projects: list[ProjectEntry] = field(default_factory=list)
    certificates: list[CertificateEntry] = field(default_factory=list)
    internships: list[InternshipEntry] = field(default_factory=list)

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()


# Column order for the "Users Resume Details" sheet.
RESUME_SHEET_HEADER: list[str] = [
    "timestamp", "email", "first_name", "last_name", "phone", "address",
    "linkedin", "github", "portfolio", "career_objective", "education",
    "skills", "achievements", "languages", "hobbies", "references",
    "projects_json", "certificates_json", "internships_json",
]


def _to_row(profile: ResumeProfile) -> dict[str, Any]:
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "email": profile.email,
        "first_name": profile.first_name,
        "last_name": profile.last_name,
        "phone": profile.phone,
        "address": profile.address,
        "linkedin": profile.linkedin,
        "github": profile.github,
        "portfolio": profile.portfolio,
        "career_objective": profile.career_objective,
        "education": profile.education,
        "skills": ", ".join(profile.skills),
        "achievements": profile.achievements,
        "languages": ", ".join(profile.languages),
        "hobbies": ", ".join(profile.hobbies),
        "references": profile.references,
        "projects_json": json.dumps([asdict(p) for p in profile.projects]),
        "certificates_json": json.dumps([asdict(c) for c in profile.certificates]),
        "internships_json": json.dumps([asdict(i) for i in profile.internships]),
    }


def save_resume(profile: ResumeProfile) -> None:
    """Append/update this user's resume details in the Users Resume Details sheet."""
    row = _to_row(profile)
    append_row(SHEETS_CONFIG.resume_sheet_name, RESUME_SHEET_HEADER, row)
    logger.info("Resume details saved for %s", profile.email)


def _from_row(row: dict[str, Any]) -> ResumeProfile:
    def _split(value: str) -> list[str]:
        return [v.strip() for v in value.split(",") if v.strip()] if value else []

    def _load_list(value: str, cls):
        try:
            items = json.loads(value) if value else []
        except (json.JSONDecodeError, TypeError):
            items = []
        return [cls(**item) for item in items]

    return ResumeProfile(
        first_name=row.get("first_name", ""),
        last_name=row.get("last_name", ""),
        email=row.get("email", ""),
        phone=row.get("phone", ""),
        address=row.get("address", ""),
        linkedin=row.get("linkedin", ""),
        github=row.get("github", ""),
        portfolio=row.get("portfolio", ""),
        career_objective=row.get("career_objective", ""),
        education=row.get("education", ""),
        skills=_split(row.get("skills", "")),
        achievements=row.get("achievements", ""),
        languages=_split(row.get("languages", "")),
        hobbies=_split(row.get("hobbies", "")),
        references=row.get("references", ""),
        projects=_load_list(row.get("projects_json", ""), ProjectEntry),
        certificates=_load_list(row.get("certificates_json", ""), CertificateEntry),
        internships=_load_list(row.get("internships_json", ""), InternshipEntry),
    )


def get_latest_resume(email: str) -> ResumeProfile | None:
    """Return the most recently saved resume for this email, if any."""
    rows = read_rows(SHEETS_CONFIG.resume_sheet_name, RESUME_SHEET_HEADER)
    matches = [r for r in rows if r.get("email") == email]
    if not matches:
        return None
    return _from_row(matches[-1])
