"""
frontend/job_search_page.py
------------------------------
Renders the "Job Search" page: filters over backend/job_search.py
(RemoteOK-backed, with automatic sample-data fallback), styled with the
same hero/glass-card components used across the rest of LearnMate AI.
"""

from __future__ import annotations

import streamlit as st

from backend.job_search import search_jobs, filter_jobs, JobListing
from frontend.components import hero, glass_card_open, glass_card_close, pill_row, empty_state

EXPERIENCE_LEVELS = ["Any", "Entry-level", "Mid-level", "Senior"]
REMOTE_OPTIONS = ["Any", "Remote only", "Onsite only"]


@st.cache_data(ttl=600, show_spinner=False)
def _fetch_all_jobs() -> list[JobListing]:
    """Fetch the full (unfiltered) job list once and cache it for 10 minutes,
    so changing filters doesn't re-hit the RemoteOK API on every rerun."""
    return search_jobs()


def _render_job_card(job: JobListing) -> None:
    glass_card_open(job.title)
    st.caption(f"🏢 {job.company}  ·  📍 {job.location}  ·  🌐 {job.source}")

    c1, c2, c3 = st.columns(3)
    c1.markdown(f"**Experience**\n\n{job.experience}")
    c2.markdown(f"**Work Mode**\n\n{'Remote' if job.remote else 'Onsite/Hybrid'}")
    c3.markdown(f"**Salary**\n\n{job.salary if job.salary else 'Not disclosed'}")

    posted_date = getattr(job, "posted_date", None) or getattr(job, "date", None)
    st.caption(f"🗓️ Posted: {posted_date or 'Not available'}")

    if job.tags:
        pill_row(job.tags[:6])

    st.link_button("🚀 Apply Now", job.url, use_container_width=True)
    glass_card_close()


def render_job_search_page() -> None:
    hero(
        "Find Your Next Role", "💼 Job Search",
        "Live remote-job listings via RemoteOK, with filters for keyword, "
        "location, work mode, and experience level.",
    )

    glass_card_open("🔍 Filters")
    f1, f2 = st.columns(2)
    with f1:
        keyword = st.text_input("Keyword", placeholder="e.g. Data Scientist, Python, React")
    with f2:
        location = st.text_input("Location", placeholder="e.g. Remote, New York, India")

    f3, f4 = st.columns(2)
    with f3:
        remote_choice = st.selectbox("Remote", REMOTE_OPTIONS)
    with f4:
        experience = st.selectbox("Experience", EXPERIENCE_LEVELS)
    glass_card_close()

    remote_value = {"Any": None, "Remote only": True, "Onsite only": False}[remote_choice]

    try:
        all_jobs = _fetch_all_jobs()
    except Exception:
        all_jobs = []

    results = filter_jobs(
        all_jobs, title=keyword, location=location,
        remote=remote_value, experience=experience,
    )

    st.markdown(f"### Results ({len(results)})")
    if not results:
        empty_state("🔎", "No jobs match those filters - try widening your search.")
        return

    for job in results:
        _render_job_card(job)
