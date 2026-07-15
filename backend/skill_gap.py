"""
backend/skill_gap.py
----------------------
Utilities for turning the roadmap's `skill_gap_analysis` block into
UI-friendly, sortable/scoreable data (used by the dashboard & charts).
"""

from __future__ import annotations

from typing import Any

LEVEL_SCORE = {"None": 0, "Basic": 1, "Intermediate": 2, "Advanced": 3}
PRIORITY_ORDER = {"High": 0, "Medium": 1, "Low": 2}


def normalize_skill_gaps(raw_gaps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Validate/normalize skill-gap entries and compute a numeric gap score."""
    normalized = []
    for item in raw_gaps or []:
        skill = str(item.get("skill", "Unknown skill")).strip()
        current = item.get("current_level", "None")
        required = item.get("required_level", "Intermediate")
        priority = item.get("priority", "Medium")

        current = current if current in LEVEL_SCORE else "None"
        required = required if required in LEVEL_SCORE else "Intermediate"
        priority = priority if priority in PRIORITY_ORDER else "Medium"

        gap_score = max(LEVEL_SCORE[required] - LEVEL_SCORE[current], 0)

        normalized.append({
            "skill": skill,
            "current_level": current,
            "required_level": required,
            "priority": priority,
            "gap_score": gap_score,
        })

    normalized.sort(key=lambda x: (PRIORITY_ORDER[x["priority"]], -x["gap_score"]))
    return normalized


def overall_readiness_percent(raw_gaps: list[dict[str, Any]]) -> int:
    """A simple 0-100% readiness score derived from current vs required levels."""
    gaps = normalize_skill_gaps(raw_gaps)
    if not gaps:
        return 0
    max_possible = sum(LEVEL_SCORE[g["required_level"]] for g in gaps) or 1
    achieved = sum(LEVEL_SCORE[g["current_level"]] for g in gaps)
    return round(min(achieved / max_possible, 1.0) * 100)
