"""
backend/job_search.py
------------------------
Job Search backend.

Sources (merged, deduped): RemoteOK, Remotive, and Arbeitnow - all free,
public JSON APIs, no key required. Each source is fetched independently;
if one fails (network error, timeout, rate limit, schema change) the
others still contribute results. Only if ALL three fail/return nothing
does search_jobs() fall back to a small curated sample dataset, so the
page never breaks - the same fail-soft pattern already used by
backend/watsonx_client.py (offline roadmap) and backend/sheets_client.py
(local CSV fallback) elsewhere in this project.

Search: RapidFuzz-powered fuzzy matching + a domain/role synonym map on
the `title` filter (e.g. "ML" also finds "Machine Learning" roles), with
a stdlib difflib fallback if rapidfuzz isn't installed - add
`rapidfuzz>=3.9` to requirements.txt for full fuzzy matching; without it
this still works correctly, just with weaker similarity scoring.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import requests

from backend.logger_setup import get_logger

logger = get_logger(__name__)

REMOTEOK_API_URL = "https://remoteok.com/api"
REMOTIVE_API_URL = "https://remotive.com/api/remote-jobs"
ARBEITNOW_API_URL = "https://www.arbeitnow.com/api/job-board-api"
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
# Fallback sample dataset - used only if every live source fails.
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


# ------------------------------------------------------------------
# Provider fetchers - each independent; a failure in one never blocks
# the others (see _fetch_all_providers).
# ------------------------------------------------------------------
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


def _fetch_remotive_jobs() -> list[JobListing]:
    """Fetch and normalize listings from Remotive's public API."""
    resp = requests.get(REMOTIVE_API_URL, headers=_HEADERS, timeout=_REQUEST_TIMEOUT)
    resp.raise_for_status()
    data = resp.json()

    listings: list[JobListing] = []
    for job in data.get("jobs", []):
        title = str(job.get("title", "")).strip()
        company = str(job.get("company_name", "Unknown")).strip()
        if not title or not company:
            continue
        tags = [str(t) for t in job.get("tags", [])]
        salary = str(job.get("salary") or "").strip() or "Not disclosed"
        listings.append(JobListing(
            title=title,
            company=company,
            location=job.get("candidate_required_location") or "Remote",
            experience=_infer_experience(title, tags),
            remote=True,  # Remotive is a remote-only job board
            salary=salary,
            url=job.get("url") or "https://remotive.com",
            source="Remotive",
            tags=tags,
        ))
    return listings


def _fetch_arbeitnow_jobs() -> list[JobListing]:
    """Fetch and normalize listings from Arbeitnow's public API."""
    resp = requests.get(ARBEITNOW_API_URL, headers=_HEADERS, timeout=_REQUEST_TIMEOUT)
    resp.raise_for_status()
    data = resp.json()

    listings: list[JobListing] = []
    for job in data.get("data", []):
        title = str(job.get("title", "")).strip()
        company = str(job.get("company_name", "Unknown")).strip()
        if not title or not company:
            continue
        tags = [str(t) for t in job.get("tags", [])]
        listings.append(JobListing(
            title=title,
            company=company,
            location=job.get("location") or ("Remote" if job.get("remote") else "Not specified"),
            experience=_infer_experience(title, tags),
            remote=bool(job.get("remote", False)),
            salary="Not disclosed",  # Arbeitnow's public API doesn't expose salary
            url=job.get("url") or "https://www.arbeitnow.com",
            source="Arbeitnow",
            tags=tags,
        ))
    return listings


_PROVIDERS = (
    ("RemoteOK", _fetch_remoteok_jobs),
    ("Remotive", _fetch_remotive_jobs),
    ("Arbeitnow", _fetch_arbeitnow_jobs),
)


def _dedupe(jobs: list[JobListing]) -> list[JobListing]:
    """Merge duplicate results (same title + company) seen across providers."""
    seen: set[tuple[str, str]] = set()
    unique: list[JobListing] = []
    for j in jobs:
        key = (j.title.strip().lower(), j.company.strip().lower())
        if key not in seen:
            seen.add(key)
            unique.append(j)
    return unique


# ------------------------------------------------------------------
# Streamlit caching, with a safe no-op fallback if streamlit isn't
# importable (e.g. a plain script/test context).
# ------------------------------------------------------------------
try:
    import streamlit as _st
    _cache_data = _st.cache_data
except ImportError:  # pragma: no cover
    def _cache_data(*_a, **_k):
        def _decorator(fn):
            return fn
        return _decorator


@_cache_data(ttl=600, show_spinner=False)
def _fetch_all_providers() -> list[JobListing]:
    """Fetch from every provider (each fail-soft independently), merge, and dedupe."""
    all_jobs: list[JobListing] = []
    any_succeeded = False

    for name, fetch_fn in _PROVIDERS:
        try:
            jobs = fetch_fn()
            if jobs:
                any_succeeded = True
                all_jobs.extend(jobs)
                logger.info("Fetched %d listings from %s.", len(jobs), name)
        except Exception as exc:  # noqa: BLE001 - one provider's failure never blocks the others
            logger.warning("%s fetch failed (%s) — continuing with other providers.", name, exc)

    if not any_succeeded:
        logger.warning("All job providers failed — using fallback sample job data.")
        return list(_SAMPLE_JOBS)

    return _dedupe(all_jobs)


# ------------------------------------------------------------------
# Fuzzy matching (RapidFuzz, with a stdlib fallback).
# ------------------------------------------------------------------
try:
    from rapidfuzz import fuzz as _fuzz
    _RAPIDFUZZ_AVAILABLE = True
except ImportError:  # pragma: no cover
    import difflib
    _RAPIDFUZZ_AVAILABLE = False


def _similarity(a: str, b: str) -> float:
    """Fuzzy similarity score, 0-100. RapidFuzz if available, difflib otherwise."""
    if not a or not b:
        return 0.0
    if _RAPIDFUZZ_AVAILABLE:
        return _fuzz.WRatio(a, b)
    return difflib.SequenceMatcher(None, a.lower(), b.lower()).ratio() * 100


# ------------------------------------------------------------------
# Domain/role synonym expansion - "ML" also finds "Machine Learning"
# roles, "GenAI"/"Prompt Engineering" find AI roles, etc.
# ------------------------------------------------------------------
SYNONYM_GROUPS: list[set[str]] = [
    {"ai", "artificial intelligence", "genai", "generative ai", "prompt engineering", "prompt engineer"},
    {"ml", "machine learning", "deep learning", "ml engineer", "machine learning engineer"},
    {"data science", "data scientist", "data analytics", "data analyst", "data analysis"},
    {"web dev", "web developer", "web development", "frontend", "front-end", "frontend developer",
     "backend", "back-end", "backend developer", "full stack", "fullstack", "full stack developer"},
    {"cybersecurity", "cyber security", "infosec", "information security", "security analyst"},
    {"cloud", "cloud computing", "cloud engineer"},
    {"ui/ux", "ux", "ui", "user experience", "user interface", "designer", "ux designer", "ui designer"},
    {"devops", "dev ops", "site reliability", "sre", "ci/cd", "devops engineer"},
    {"software engineer", "software developer", "programmer", "swe"},
    {"python", "python developer"},
]

_FUZZY_THRESHOLD = 55.0


def _expand_query(query: str) -> list[str]:
    """Return [query] plus any synonym terms that match it or its words."""
    if not query:
        return []
    q = query.strip().lower()
    variants = {q}
    for group in SYNONYM_GROUPS:
        if q in group or any(word in group for word in q.split()):
            variants |= group
    return list(variants)


def _job_score(job: JobListing, query_variants: list[str]) -> float:
    """Best fuzzy-match score across the job's searchable text and all query variants."""
    if not query_variants:
        return 100.0
    searchable = f"{job.title} {job.company} {' '.join(job.tags)}"
    return max((_similarity(v, searchable) for v in query_variants), default=0.0)


def _fuzzy_rank_by_title(jobs: list[JobListing], title: str) -> list[JobListing]:
    variants = _expand_query(title)
    if not variants:
        return jobs
    scored = [(j, _job_score(j, variants)) for j in jobs]
    scored = [(j, s) for j, s in scored if s >= _FUZZY_THRESHOLD]
    scored.sort(key=lambda pair: pair[1], reverse=True)
    return [j for j, _ in scored]


# ------------------------------------------------------------------
# Public search API
# ------------------------------------------------------------------
def search_jobs(
    title: str = "",
    location: str = "",
    remote: bool | None = None,
    experience: str = "",
    company: str = "",
    page: int = 1,
    page_size: int = 50,
) -> list[JobListing]:
    """Fetch jobs from all providers (merged/deduped, sample-fallback on
    total failure), then fuzzy-filter and paginate.

    `page`/`page_size` are optional and default to the first up to 50
    (page_size capped at 50) results, so existing callers that don't pass
    them behave exactly as before.
    """
    all_jobs = _fetch_all_providers()
    has_filters = bool(title or location or remote is not None or experience or company)

    filtered = filter_jobs(
        all_jobs, title=title, location=location, remote=remote,
        experience=experience, company=company,
    )

    if not filtered and has_filters:
        # Relax: keep only the fuzzy title match, drop location/remote/experience/company.
        filtered = filter_jobs(all_jobs, title=title)

    if not filtered and title:
        # Relax further: fuzzy-rank the whole pool below the normal threshold
        # so the user sees "similar" roles instead of nothing.
        variants = _expand_query(title)
        scored = sorted(
            ((j, _job_score(j, variants)) for j in all_jobs),
            key=lambda pair: pair[1], reverse=True,
        )
        filtered = [j for j, _ in scored]

    if not filtered:
        filtered = all_jobs

    if not has_filters:
        # A bare, filter-less call (e.g. a caller fetching the full pool to
        # cache/filter client-side, as frontend/job_search_page.py does)
        # returns everything unpaginated - pagination only kicks in once an
        # actual search/filter is being performed.
        return filtered

    page_size = max(1, min(page_size, 50))
    page = max(1, page)
    start = (page - 1) * page_size
    return filtered[start: start + page_size]


def filter_jobs(
    jobs: list[JobListing],
    title: str = "",
    location: str = "",
    remote: bool | None = None,
    experience: str = "",
    company: str = "",
) -> list[JobListing]:
    """Apply structured filters to a job list.

    `title` uses fuzzy + synonym matching (typo-tolerant, e.g. "ML" also
    matches "Machine Learning" roles). `location`/`company` remain
    substring filters; `remote`/`experience` remain exact-match filters.
    """
    results = _fuzzy_rank_by_title(jobs, title)

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
