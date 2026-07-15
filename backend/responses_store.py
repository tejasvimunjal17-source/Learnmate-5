"""
backend/responses_store.py
-----------------------------
Persists every AI Roadmap form submission into the "LearnMate AI Users
Responses" Google Sheet (or local CSV fallback), independent of the roadmap
generation itself, so submissions are captured even if AI generation later
fails.
"""

from __future__ import annotations

from datetime import datetime, timezone

from config import SHEETS_CONFIG
from backend.sheets_client import append_row
from backend.logger_setup import get_logger
from backend.roadmap_engine import StudentProfile

logger = get_logger(__name__)

RESPONSES_HEADER = [
    "Timestamp", "Email", "Career Goal", "Level", "Domain",
    "Learning Preference", "Study Hours", "Existing Skills",
]


def save_response(email: str, profile: StudentProfile) -> None:
    """Append one roadmap-form submission to the responses sheet."""
    row = {
        "Timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "Email": email.strip().lower(),
        "Career Goal": profile.career_goal,
        "Level": profile.current_level,
        "Domain": profile.preferred_domain,
        "Learning Preference": profile.learning_preference,
        "Study Hours": profile.study_hours_per_week,
        "Existing Skills": ", ".join(profile.existing_skills),
    }
    try:
        append_row(SHEETS_CONFIG.responses_sheet_name, RESPONSES_HEADER, row)
    except Exception:  # noqa: BLE001 - never block roadmap generation on logging failure
        logger.exception("Failed to persist roadmap response for %s", email)
