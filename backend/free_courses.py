"""
backend/free_courses.py
------------------------
Curated catalogue of free courses from official learning platforms, with
search-by-domain and filter helpers for the "Free Courses" page.

Design notes
------------
- Data is curated/static (no scraping), per project requirements. Each
  entry links to the platform's own course/catalogue page.
- Deliberately does NOT reuse backend/recommendations.py's `Course`
  dataclass: that one is scoped to the AI-Roadmap "recommended courses"
  flow (tied to a generated roadmap/profile) and this page is a standalone
  browsable catalogue searchable by anyone, so a separate, slightly
  richer dataclass (platform/difficulty/duration/certificate as
  filterable fields) avoids overloading an existing type used elsewhere.
"""

from __future__ import annotations

from dataclasses import dataclass

DOMAINS: list[str] = [
    "AI",
    "Data Science",
    "Machine Learning",
    "Web Development",
    "Python",
    "Cybersecurity",
    "Cloud Computing",
    "UI/UX",
    "DevOps",
]


@dataclass(frozen=True)
class FreeCourse:
    name: str
    provider: str
    domain: str
    platform: str          # filter facet - platform/brand
    difficulty: str        # Beginner / Intermediate / Advanced
    duration: str           # human-readable, e.g. "6 hours", "4 weeks"
    certificate: bool
    url: str


# ------------------------------------------------------------------
# Curated catalogue. Every URL points at the provider's own official
# course or catalogue page - never a third-party mirror.
# ------------------------------------------------------------------
_CATALOGUE: list[FreeCourse] = [
    # ---------------- AI ----------------
    FreeCourse("Elements of AI", "University of Helsinki / MinnaLearn", "AI",
               "Elements of AI", "Beginner", "30 hours", True,
               "https://www.elementsofai.com/"),
    FreeCourse("Introduction to Generative AI", "Google Cloud Skills Boost", "AI",
               "Google Skillshop", "Beginner", "45 min", True,
               "https://www.cloudskillsboost.google/course_templates/536"),
    FreeCourse("AI For Everyone", "DeepLearning.AI (Coursera Free Audit)", "AI",
               "Coursera Free", "Beginner", "6 hours", False,
               "https://www.coursera.org/learn/ai-for-everyone"),
    FreeCourse("Artificial Intelligence: A Business Perspective", "IBM SkillsBuild", "AI",
               "IBM SkillsBuild", "Beginner", "10 hours", True,
               "https://skillsbuild.org/"),
    FreeCourse("Microsoft AI Fundamentals (AI-900 prep)", "Microsoft Learn", "AI",
               "Microsoft Learn", "Beginner", "8 hours", True,
               "https://learn.microsoft.com/training/paths/get-started-with-artificial-intelligence-on-azure/"),

    # ---------------- Data Science ----------------
    FreeCourse("Data Science: Foundations using R", "Harvard University (edX)", "Data Science",
               "edX", "Beginner", "8 weeks", False,
               "https://www.edx.org/learn/data-science"),
    FreeCourse("Data Analysis with Python", "freeCodeCamp", "Data Science",
               "freeCodeCamp", "Beginner", "20 hours", True,
               "https://www.freecodecamp.org/learn/data-analysis-with-python/"),
    FreeCourse("Python for Data Science", "Kaggle Learn", "Data Science",
               "Kaggle Learn", "Beginner", "4 hours", True,
               "https://www.kaggle.com/learn/python"),
    FreeCourse("Data Visualization", "Kaggle Learn", "Data Science",
               "Kaggle Learn", "Intermediate", "4 hours", True,
               "https://www.kaggle.com/learn/data-visualization"),
    FreeCourse("Introduction to Data Science", "IBM SkillsBuild", "Data Science",
               "IBM SkillsBuild", "Beginner", "12 hours", True,
               "https://skillsbuild.org/"),

    # ---------------- Machine Learning ----------------
    FreeCourse("Machine Learning Specialization (audit)", "Stanford / DeepLearning.AI", "Machine Learning",
               "Coursera Free", "Intermediate", "3 months", False,
               "https://www.coursera.org/specializations/machine-learning-introduction"),
    FreeCourse("Intro to Machine Learning", "Kaggle Learn", "Machine Learning",
               "Kaggle Learn", "Beginner", "3 hours", True,
               "https://www.kaggle.com/learn/intro-to-machine-learning"),
    FreeCourse("Intermediate Machine Learning", "Kaggle Learn", "Machine Learning",
               "Kaggle Learn", "Intermediate", "4 hours", True,
               "https://www.kaggle.com/learn/intermediate-machine-learning"),
    FreeCourse("Machine Learning Crash Course", "Google", "Machine Learning",
               "Google Skillshop", "Beginner", "15 hours", False,
               "https://developers.google.com/machine-learning/crash-course"),

    # ---------------- Web Development ----------------
    FreeCourse("Responsive Web Design", "freeCodeCamp", "Web Development",
               "freeCodeCamp", "Beginner", "300 hours", True,
               "https://www.freecodecamp.org/learn/2022/responsive-web-design/"),
    FreeCourse("JavaScript Algorithms and Data Structures", "freeCodeCamp", "Web Development",
               "freeCodeCamp", "Intermediate", "300 hours", True,
               "https://www.freecodecamp.org/learn/javascript-algorithms-and-data-structures/"),
    FreeCourse("Introduction to HTML5", "W3C / edX", "Web Development",
               "edX", "Beginner", "5 weeks", False,
               "https://www.edx.org/learn/html"),
    FreeCourse("Full-Stack Web Development", "IBM SkillsBuild", "Web Development",
               "IBM SkillsBuild", "Intermediate", "20 hours", True,
               "https://skillsbuild.org/"),

    # ---------------- Python ----------------
    FreeCourse("Python for Everybody", "University of Michigan (Coursera Free Audit)", "Python",
               "Coursera Free", "Beginner", "8 months (self-paced)", False,
               "https://www.coursera.org/specializations/python"),
    FreeCourse("Scientific Computing with Python", "freeCodeCamp", "Python",
               "freeCodeCamp", "Beginner", "300 hours", True,
               "https://www.freecodecamp.org/learn/scientific-computing-with-python/"),
    FreeCourse("Python Basics", "Kaggle Learn", "Python",
               "Kaggle Learn", "Beginner", "5 hours", True,
               "https://www.kaggle.com/learn/python"),
    FreeCourse("CS50's Introduction to Programming with Python", "Harvard University (edX)", "Python",
               "edX", "Beginner", "9 weeks", False,
               "https://www.edx.org/learn/python"),

    # ---------------- Cybersecurity ----------------
    FreeCourse("Introduction to Cybersecurity", "Cisco Networking Academy", "Cybersecurity",
               "Cisco Networking Academy", "Beginner", "6 hours", True,
               "https://www.netacad.com/courses/cybersecurity/introduction-cybersecurity"),
    FreeCourse("Cybersecurity Essentials", "Cisco Networking Academy", "Cybersecurity",
               "Cisco Networking Academy", "Intermediate", "15 hours", True,
               "https://www.netacad.com/courses/cybersecurity/cybersecurity-essentials"),
    FreeCourse("Introduction to Cybersecurity", "IBM SkillsBuild", "Cybersecurity",
               "IBM SkillsBuild", "Beginner", "10 hours", True,
               "https://skillsbuild.org/"),
    FreeCourse("Foundations of Cybersecurity", "Google (Coursera Free Audit)", "Cybersecurity",
               "Coursera Free", "Beginner", "10 hours", False,
               "https://www.coursera.org/learn/foundations-of-cybersecurity"),

    # ---------------- Cloud Computing ----------------
    FreeCourse("AWS Cloud Practitioner Essentials", "AWS Skill Builder", "Cloud Computing",
               "AWS Skill Builder", "Beginner", "6 hours", True,
               "https://skillbuilder.aws/"),
    FreeCourse("Microsoft Azure Fundamentals (AZ-900)", "Microsoft Learn", "Cloud Computing",
               "Microsoft Learn", "Beginner", "8 hours", True,
               "https://learn.microsoft.com/training/paths/azure-fundamentals/"),
    FreeCourse("Google Cloud Digital Leader Training", "Google Cloud Skills Boost", "Cloud Computing",
               "Google Skillshop", "Beginner", "10 hours", True,
               "https://www.cloudskillsboost.google/paths"),
    FreeCourse("Introduction to Cloud Computing", "IBM SkillsBuild", "Cloud Computing",
               "IBM SkillsBuild", "Beginner", "8 hours", True,
               "https://skillsbuild.org/"),

    # ---------------- UI/UX ----------------
    FreeCourse("Foundations of User Experience Design", "Google (Coursera Free Audit)", "UI/UX",
               "Coursera Free", "Beginner", "16 hours", False,
               "https://www.coursera.org/learn/foundations-user-experience-design"),
    FreeCourse("Introduction to UX Design", "IBM SkillsBuild", "UI/UX",
               "IBM SkillsBuild", "Beginner", "8 hours", True,
               "https://skillsbuild.org/"),
    FreeCourse("Human-Computer Interaction Design", "edX", "UI/UX",
               "edX", "Intermediate", "6 weeks", False,
               "https://www.edx.org/learn/ui-ux-design"),

    # ---------------- DevOps ----------------
    FreeCourse("Introduction to DevOps", "IBM SkillsBuild", "DevOps",
               "IBM SkillsBuild", "Beginner", "10 hours", True,
               "https://skillsbuild.org/"),
    FreeCourse("DevOps on AWS", "AWS Skill Builder", "DevOps",
               "AWS Skill Builder", "Intermediate", "12 hours", True,
               "https://skillbuilder.aws/"),
    FreeCourse("Introduction to DevOps and Site Reliability Engineering",
               "IBM (Coursera Free Audit)", "DevOps",
               "Coursera Free", "Beginner", "13 hours", False,
               "https://www.coursera.org/learn/intro-to-devops"),
    FreeCourse("GitHub Actions Fundamentals", "Microsoft Learn", "DevOps",
               "Microsoft Learn", "Beginner", "3 hours", True,
               "https://learn.microsoft.com/training/paths/automate-workflow-github-actions/"),
]

PLATFORMS: list[str] = sorted({c.platform for c in _CATALOGUE})
DIFFICULTIES: list[str] = ["Beginner", "Intermediate", "Advanced"]
DURATIONS: list[str] = ["Any", "Under 5 hours", "5-20 hours", "20+ hours / multi-week"]


def _duration_bucket(duration: str) -> str:
    """Best-effort bucket classification for the Duration filter facet."""
    d = duration.lower()
    if "hour" in d:
        try:
            hours = int(d.split("hour")[0].strip().split()[-1])
        except ValueError:
            return "20+ hours / multi-week"
        if hours < 5:
            return "Under 5 hours"
        if hours <= 20:
            return "5-20 hours"
        return "20+ hours / multi-week"
    return "20+ hours / multi-week"


# ------------------------------------------------------------------
# Fuzzy matching (RapidFuzz, with a stdlib fallback so a missing
# dependency degrades gracefully instead of breaking the page - add
# `rapidfuzz>=3.9` to requirements.txt for real fuzzy matching; without
# it this still works, just with weaker (difflib-based) similarity).
# ------------------------------------------------------------------
try:
    from rapidfuzz import fuzz as _fuzz
    _RAPIDFUZZ_AVAILABLE = True
except ImportError:  # pragma: no cover - exercised only when the dep is missing
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
# Synonym expansion - so "ML" also finds "Machine Learning" courses,
# "GenAI"/"Prompt Engineering" find AI courses, etc.
# ------------------------------------------------------------------
SYNONYM_GROUPS: list[set[str]] = [
    {"ai", "artificial intelligence", "genai", "generative ai", "prompt engineering", "prompt design"},
    {"ml", "machine learning", "deep learning"},
    {"data science", "data analytics", "data analysis"},
    {"web dev", "web development", "frontend", "front-end", "backend", "back-end", "full stack", "fullstack"},
    {"cybersecurity", "cyber security", "infosec", "information security"},
    {"cloud", "cloud computing"},
    {"ui/ux", "ux", "ui", "user experience", "user interface", "design"},
    {"devops", "dev ops", "site reliability", "sre", "ci/cd"},
    {"python", "py"},
]


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


_FUZZY_THRESHOLD = 60.0


def _course_score(course: FreeCourse, query_variants: list[str]) -> float:
    """Best fuzzy-match score across the course's searchable text and all query variants."""
    if not query_variants:
        return 100.0
    searchable = f"{course.name} {course.provider} {course.domain} {course.platform}"
    return max(
        (_similarity(variant, searchable) for variant in query_variants),
        default=0.0,
    )


# ------------------------------------------------------------------
# Search across multiple providers - the curated catalogue already spans
# 9+ official platforms (Google Skillshop, Microsoft Learn, IBM
# SkillsBuild, Cisco Networking Academy, Coursera, edX, freeCodeCamp,
# Kaggle Learn, AWS Skill Builder). "Multi-provider" search here means
# fuzzy-matching across every course regardless of platform, rather than
# requiring an exact platform/name match.
# ------------------------------------------------------------------
def _apply_hard_filters(
    courses: list[FreeCourse], domain: str | None, platform: str | None,
    difficulty: str | None, duration: str | None, certificate_only: bool,
) -> list[FreeCourse]:
    results = list(courses)
    if domain and domain != "All Domains":
        results = [c for c in results if c.domain == domain]
    if platform and platform != "All Platforms":
        results = [c for c in results if c.platform == platform]
    if difficulty and difficulty != "All Levels":
        results = [c for c in results if c.difficulty == difficulty]
    if duration and duration != "Any":
        results = [c for c in results if _duration_bucket(c.duration) == duration]
    if certificate_only:
        results = [c for c in results if c.certificate]
    return results


def _fuzzy_rank(courses: list[FreeCourse], query: str) -> list[FreeCourse]:
    """Fuzzy+synonym-rank courses against `query`; unfiltered if query is empty."""
    variants = _expand_query(query)
    if not variants:
        return courses
    scored = [(c, _course_score(c, variants)) for c in courses]
    scored = [(c, s) for c, s in scored if s >= _FUZZY_THRESHOLD]
    scored.sort(key=lambda pair: pair[1], reverse=True)
    return [c for c, _ in scored]


try:
    import streamlit as _st
    _cache_data = _st.cache_data
except ImportError:  # pragma: no cover - only if streamlit isn't installed at all
    def _cache_data(*_a, **_k):
        def _decorator(fn):
            return fn
        return _decorator


def _dedupe(courses: list[FreeCourse]) -> list[FreeCourse]:
    """Merge duplicate results (same course name + provider)."""
    seen: set[tuple[str, str]] = set()
    unique: list[FreeCourse] = []
    for c in courses:
        key = (c.name.strip().lower(), c.provider.strip().lower())
        if key not in seen:
            seen.add(key)
            unique.append(c)
    return unique


@_cache_data(ttl=600, show_spinner=False)
def search_free_courses(
    domain: str | None = None,
    query: str = "",
    platform: str | None = None,
    difficulty: str | None = None,
    duration: str | None = None,
    certificate_only: bool = False,
    page: int = 1,
    page_size: int = 50,
) -> list[FreeCourse]:
    """Search the curated catalogue with fuzzy/synonym matching and pagination.

    Filters are applied normally first. If that combination returns zero
    results, filters are progressively relaxed (platform/difficulty/
    duration/certificate, then domain, then the fuzzy threshold itself)
    so the caller still gets similar/nearby results instead of an empty
    list - the same query never returns nothing as long as the catalogue
    has anything remotely related.

    `page`/`page_size` are optional and default to returning the first up
    to 50 (page_size capped at 50) results, so existing callers that don't
    pass them behave exactly as before.
    """
    page_size = max(1, min(page_size, 50))
    page = max(1, page)

    catalogue = _dedupe(_CATALOGUE)
    filtered = _apply_hard_filters(catalogue, domain, platform, difficulty, duration, certificate_only)
    ranked = _fuzzy_rank(filtered, query)

    relaxed = False
    if not ranked and (query or domain not in (None, "All Domains") or platform not in (None, "All Platforms")
                        or difficulty not in (None, "All Levels") or duration not in (None, "Any") or certificate_only):
        # Step 1: keep domain + query, drop platform/difficulty/duration/certificate.
        relaxed_pool = _apply_hard_filters(catalogue, domain, None, None, None, False)
        ranked = _fuzzy_rank(relaxed_pool, query)
        relaxed = True

    if not ranked and query:
        # Step 2: drop domain too, fuzzy-match the whole catalogue.
        ranked = _fuzzy_rank(catalogue, query)
        relaxed = True

    if not ranked and query:
        # Step 3: still nothing above threshold - surface the closest
        # matches anyway ("similar opportunities") rather than nothing.
        variants = _expand_query(query)
        scored = sorted(
            ((c, _course_score(c, variants)) for c in catalogue),
            key=lambda pair: pair[1], reverse=True,
        )
        ranked = [c for c, _ in scored[:page_size]]
        relaxed = True

    if not ranked:
        ranked = catalogue

    start = (page - 1) * page_size
    return ranked[start: start + page_size]
