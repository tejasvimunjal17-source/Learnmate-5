"""
backend/job_search.py
------------------------
Job Search backend.

Primary source: RemoteOK's public JSON API (https://remoteok.com/api) -
free, no API key required. If that request fails for any reason (network
error, timeout, rate limit, schema change), search_jobs() falls back to a
small curated sample dataset so the page never breaks - the same
fail-soft pattern already used by backend/watsonx_client.py (offline
roadmap) and backend/sheets_client.py (local CSV fallback) elsewhere in
this project.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import requests

from backend.logger_setup import get_logger

logger = get_logger(__name__)

REMOTEOK_API_URL = "https://remoteok.com/api"
_REQUEST_TIMEOUT = 10
_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; LearnMateAI/1.0)"}


@dataclass
class JobListing:
    title: str
    company: str
    location: str
    experience: str
    remote: bool
    salary: str
    url: str
    source: str = "RemoteOK"
    tags: list[str] = field(default_factory=list)


# ------------------------------------------------------------------
# Fallback sample dataset - used only if the live API is unavailable.
# ------------------------------------------------------------------
_SAMPLE_JOBS: list[JobListing] = [
    JobListing("Data Scientist", "Acme Analytics", "Remote", "Mid-level", True,
               "$90,000 - $120,000", "https://www.linkedin.com/jobs/", "Sample Data",
               tags=["python", "sql", "machine learning"]),
    JobListing("Frontend Developer", "Bright Web Co.", "Remote", "Entry-level", True,
               "$60,000 - $85,000", "https://www.indeed.com/", "Sample Data",
               tags=["react", "javascript", "css"]),
    JobListing("Cloud Engineer", "NimbusStack", "Austin, TX", "Mid-level", False,
               "$100,000 - $135,000", "https://www.google.com/about/careers/", "Sample Data",
               tags=["aws", "docker", "kubernetes"]),
    JobListing("Cybersecurity Analyst", "SecureNet Inc.", "New York, NY", "Mid-level", False,
               "$85,000 - $110,000", "https://careers.microsoft.com/", "Sample Data",
               tags=["cybersecurity", "network security"]),
    JobListing("DevOps Engineer", "PipelinePro", "Remote", "Senior", True,
               "$110,000 - $150,000", "https://www.ibm.com/careers/", "Sample Data",
               tags=["ci/cd", "docker", "linux"]),
    JobListing("UI/UX Designer", "PixelCraft Studio", "Remote", "Entry-level", True,
               "$50,000 - $75,000", "https://www.wellfound.com/", "Sample Data",
               tags=["figma", "design", "ui/ux"]),
    JobListing("Machine Learning Engineer", "DeepLogic AI", "Remote", "Senior", True,
               "$130,000 - $170,000", "https://www.kaggle.com/jobs", "Sample Data",
               tags=["python", "pytorch", "machine learning"]),
    JobListing("Backend Developer", "ServerSide Labs", "Bengaluru, India", "Mid-level", False,
               "$80,000 - $110,000", "https://www.naukri.com/", "Sample Data",
               tags=["node", "javascript", "api"]),
]


def _parse_salary(job: dict[str, Any]) -> str:
    lo, hi = job.get("salary_min"), job.get("salary_max")
    if lo and hi:
        return f"${int(lo):,} - ${int(hi):,}"
    if lo:
        return f"${int(lo):,}+"
    return "Not disclosed"


def _infer_experience(title: str, tags: list[str]) -> str:
    text = (title + " " + " ".join(tags)).lower()
    if any(w in text for w in ("senior", "sr.", "lead", "principal", "staff")):
        return "Senior"
    if any(w in text for w in ("junior", "jr.", "entry", "intern", "graduate")):
        return "Entry-level"
    return "Mid-level"


def _fetch_remoteok_jobs() -> list[JobListing]:
    """Fetch and normalize listings from RemoteOK's public API."""
    resp = requests.get(REMOTEOK_API_URL, headers=_HEADERS, timeout=_REQUEST_TIMEOUT)
    resp.raise_for_status()
    data = resp.json()

    listings: list[JobListing] = []
    for job in data:
        # RemoteOK's first array element is a legal/metadata notice, not a job.
        if not isinstance(job, dict) or "position" not in job:
            continue
        title = job.get("position", "").strip()
        company = job.get("company", "Unknown").strip()
        if not title or not company:
            continue
        tags = [str(t) for t in job.get("tags", [])]
        listings.append(JobListing(
            title=title,
            company=company,
            location=job.get("location") or "Remote",
            experience=_infer_experience(title, tags),
            remote=True,  # every RemoteOK listing is a remote position
            salary=_parse_salary(job),
            url=job.get("url") or "https://remoteok.com",
            source="RemoteOK",
            tags=tags,
        ))
    return listings


def search_jobs(
    title: str = "",
    location: str = "",
    remote: bool | None = None,
    experience: str = "",
    company: str = "",
) -> list[JobListing]:
    """Fetch jobs from RemoteOK (falling back to sample data on failure), then filter."""
    try:
        all_jobs = _fetch_remoteok_jobs()
        if not all_jobs:
            raise ValueError("RemoteOK returned no parsable listings.")
        logger.info("Fetched %d listings from RemoteOK.", len(all_jobs))
    except Exception as exc:  # noqa: BLE001 - any failure falls back gracefully
        logger.warning("RemoteOK fetch failed (%s) — using fallback sample job data.", exc)
        all_jobs = list(_SAMPLE_JOBS)

    return filter_jobs(
        all_jobs, title=title, location=location, remote=remote,
        experience=experience, company=company,
    )


def filter_jobs(
    jobs: list[JobListing],
    title: str = "",
    location: str = "",
    remote: bool | None = None,
    experience: str = "",
    company: str = "",
) -> list[JobListing]:
    """Apply structured filters (title, location, remote, experience, company) to a job list."""
    results = list(jobs)

    if title:
        query = title.strip().lower()
        results = [
            j for j in results
            if query in j.title.lower() or any(query in t.lower() for t in j.tags)
        ]

    if location:
        loc = location.strip().lower()
        results = [j for j in results if loc in j.location.lower()]

    if remote is not None:
        results = [j for j in results if j.remote == remote]

    if experience and experience != "Any":
        results = [j for j in results if j.experience == experience]

    if company:
        comp = company.strip().lower()
        results = [j for j in results if comp in j.company.lower()]

    return results
