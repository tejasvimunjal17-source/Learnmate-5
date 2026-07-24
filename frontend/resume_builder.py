"""
frontend/resume_builder.py
-----------------------------
Renders the "Resume Builder" page.

Education, Projects, Certificates, and Internships are all dynamic
add/remove card sections. Backend is untouched: Projects/Certificates/
Internships already map 1:1 onto backend.resume_store's ProjectEntry/
CertificateEntry/InternshipEntry dataclasses. Education has no dedicated
dataclass in the backend (ResumeProfile.education is a single str field),
so the structured education cards captured here (College/University vs
School entries, each with their own fields) are formatted into a single
well-structured multi-line string before being assigned to
ResumeProfile.education - no backend/config changes required.

Note on rendering: backend.resume_generator renders `profile.education`
by splitting on newlines and prefixing each non-empty line with "- " as
a bullet (it wasn't modified here per the "backend untouched" requirement).
So the generated PDF/DOCX will show each education line as its own
bullet rather than the exact visually-grouped block shown in the sample
output - the *content and order* match the sample format, but not its
custom multi-column alignment, since that would require a
resume_generator.py change.
"""

from __future__ import annotations

import uuid

import streamlit as st

from backend.resume_store import (
    ResumeProfile, ProjectEntry, CertificateEntry, InternshipEntry, save_resume,
)
from backend.resume_generator import build_resume_pdf, build_resume_docx
from frontend.components import hero, glass_card_open, glass_card_close

COLLEGE_LEVEL = "College / University"
SCHOOL_LEVEL = "School (10th / 12th)"
SCHOOL_QUALIFICATIONS = ["Secondary Education", "Senior Secondary Education"]

_LIST_STATE_KEYS = ["resume_education", "resume_projects", "resume_certificates", "resume_internships"]


# ------------------------------------------------------------------
# Session state helpers
# ------------------------------------------------------------------
def _new_id() -> str:
    return uuid.uuid4().hex[:8]


def _empty_education() -> dict:
    return {
        "_id": _new_id(), "level": COLLEGE_LEVEL,
        # College / University fields
        "degree": "", "field_major": "", "institution": "", "university_board": "",
        "start_year": "", "end_year": "", "present": False,
        # School fields
        "qualification": SCHOOL_QUALIFICATIONS[1], "school_name": "", "board": "",
        "passing_year": "",
        # Shared fields
        "city": "", "state": "", "country": "", "grade": "",
    }


def _empty_project() -> dict:
    return {"_id": _new_id(), "title": "", "tech_stack": "", "description": ""}


def _empty_certificate() -> dict:
    return {"_id": _new_id(), "name": "", "issuer": "", "year": ""}


def _empty_internship() -> dict:
    return {"_id": _new_id(), "role": "", "company": "", "duration": "", "description": ""}


_EMPTY_FACTORIES = {
    "resume_education": _empty_education,
    "resume_projects": _empty_project,
    "resume_certificates": _empty_certificate,
    "resume_internships": _empty_internship,
}


def _init_state() -> None:
    for key in _LIST_STATE_KEYS:
        if key not in st.session_state or not st.session_state[key]:
            st.session_state[key] = [_EMPTY_FACTORIES[key]()]
    st.session_state.setdefault("resume_profile", None)


def _remove_entry(state_key: str, entry_id: str) -> None:
    entries = st.session_state[state_key]
    if len(entries) <= 1:
        return  # never delete the last remaining card
    st.session_state[state_key] = [e for e in entries if e["_id"] != entry_id]
    st.rerun()


def _add_entry(state_key: str) -> None:
    st.session_state[state_key].append(_EMPTY_FACTORIES[state_key]())
    st.rerun()


def _card_header(label: str, state_key: str, entry_id: str, can_remove: bool) -> None:
    head_col, remove_col = st.columns([6, 1])
    head_col.markdown(f"**{label}**")
    with remove_col:
        if st.button("❌", key=f"remove_{state_key}_{entry_id}",
                      disabled=not can_remove, help="Remove this entry"):
            _remove_entry(state_key, entry_id)


# ------------------------------------------------------------------
# Education cards
# ------------------------------------------------------------------
def _render_education_entries() -> list[dict]:
    entries = st.session_state["resume_education"]
    can_remove = len(entries) > 1

    for idx, entry in enumerate(entries):
        eid = entry["_id"]
        with st.container(border=True):
            _card_header(f"Education Entry {idx + 1}", "resume_education", eid, can_remove)

            entry["level"] = st.selectbox(
                "Education Level", [COLLEGE_LEVEL, SCHOOL_LEVEL],
                index=[COLLEGE_LEVEL, SCHOOL_LEVEL].index(entry["level"]),
                key=f"edu_level_{eid}",
            )

            if entry["level"] == COLLEGE_LEVEL:
                c1, c2 = st.columns(2)
                entry["degree"] = c1.text_input(
                    "Degree (e.g. Bachelor of Commerce (Hons))",
                    value=entry["degree"], key=f"edu_degree_{eid}",
                )
                entry["field_major"] = c2.text_input(
                    "Field / Major", value=entry["field_major"], key=f"edu_field_{eid}",
                )
                c3, c4 = st.columns(2)
                entry["institution"] = c3.text_input(
                    "College / University Name", value=entry["institution"], key=f"edu_inst_{eid}",
                )
                entry["university_board"] = c4.text_input(
                    "University / Board", value=entry["university_board"], key=f"edu_univ_{eid}",
                )
                c5, c6, c7 = st.columns([1, 1, 1])
                entry["start_year"] = c5.text_input(
                    "Start Year", value=entry["start_year"], key=f"edu_start_{eid}",
                )
                entry["present"] = c6.checkbox(
                    "Present", value=entry["present"], key=f"edu_present_{eid}",
                )
                entry["end_year"] = c7.text_input(
                    "End Year", value=entry["end_year"], key=f"edu_end_{eid}",
                    disabled=entry["present"],
                )
                c8, c9, c10 = st.columns(3)
                entry["city"] = c8.text_input("City", value=entry["city"], key=f"edu_city_{eid}")
                entry["state"] = c9.text_input("State", value=entry["state"], key=f"edu_state_{eid}")
                entry["country"] = c10.text_input("Country", value=entry["country"], key=f"edu_country_{eid}")
                entry["grade"] = st.text_input(
                    "CGPA / Percentage (optional)", value=entry["grade"], key=f"edu_grade_{eid}",
                )
            else:
                entry["qualification"] = st.selectbox(
                    "Qualification", SCHOOL_QUALIFICATIONS,
                    index=SCHOOL_QUALIFICATIONS.index(entry["qualification"])
                    if entry["qualification"] in SCHOOL_QUALIFICATIONS else 1,
                    key=f"edu_qual_{eid}",
                )
                c1, c2 = st.columns(2)
                entry["school_name"] = c1.text_input(
                    "School Name", value=entry["school_name"], key=f"edu_school_{eid}",
                )
                entry["board"] = c2.text_input(
                    "Education Board (CBSE / ICSE / State Board / IB / etc.)",
                    value=entry["board"], key=f"edu_board_{eid}",
                )
                entry["passing_year"] = st.text_input(
                    "Passing Year", value=entry["passing_year"], key=f"edu_passing_{eid}",
                )
                c3, c4, c5 = st.columns(3)
                entry["city"] = c3.text_input("City", value=entry["city"], key=f"edu_scity_{eid}")
                entry["state"] = c4.text_input("State", value=entry["state"], key=f"edu_sstate_{eid}")
                entry["country"] = c5.text_input("Country", value=entry["country"], key=f"edu_scountry_{eid}")
                entry["grade"] = st.text_input(
                    "Percentage / CGPA (optional)", value=entry["grade"], key=f"edu_sgrade_{eid}",
                )

    if st.button("➕ Add Education", key="add_resume_education"):
        _add_entry("resume_education")

    return entries


def _format_education_entry(e: dict) -> str:
    location = ", ".join(p for p in [e.get("city", ""), e.get("state", ""), e.get("country", "")] if p)

    if e["level"] == COLLEGE_LEVEL:
        title_line = e["degree"] or e["field_major"]
        status = "Pursuing" if e["present"] else (e["end_year"] or "")
        if title_line and status:
            title_line = f"{title_line} | {status}"
        years = f"{e['start_year']} – {'Present' if e['present'] else e['end_year']}".strip(" –")
        last_line = f"{years}          {location}".strip() if (years or location) else ""
        lines = [title_line, e["institution"], e["university_board"], last_line]
    else:
        years = e["passing_year"]
        last_line = f"{years}          {location}".strip() if (years or location) else ""
        lines = [e["qualification"], e["school_name"], e["board"], last_line]

    lines = [l for l in lines if l and l.strip()]
    if e.get("grade"):
        lines.append(f"Grade: {e['grade']}")
    return "\n".join(lines)


def _education_entries_to_text(entries: list[dict]) -> str:
    blocks = [_format_education_entry(e) for e in entries]
    blocks = [b for b in blocks if b.strip()]
    return "\n".join(blocks)


# ------------------------------------------------------------------
# Projects / Certificates / Internships cards
# ------------------------------------------------------------------
def _render_project_entries() -> list[dict]:
    entries = st.session_state["resume_projects"]
    can_remove = len(entries) > 1
    for idx, entry in enumerate(entries):
        eid = entry["_id"]
        with st.container(border=True):
            _card_header(f"Project {idx + 1}", "resume_projects", eid, can_remove)
            c1, c2 = st.columns(2)
            entry["title"] = c1.text_input("Project Title", value=entry["title"], key=f"proj_title_{eid}")
            entry["tech_stack"] = c2.text_input("Tech Stack", value=entry["tech_stack"], key=f"proj_tech_{eid}")
            entry["description"] = st.text_area(
                "Description", value=entry["description"], key=f"proj_desc_{eid}", height=70,
            )
    if st.button("➕ Add Another Project", key="add_resume_projects"):
        _add_entry("resume_projects")
    return entries


def _render_certificate_entries() -> list[dict]:
    entries = st.session_state["resume_certificates"]
    can_remove = len(entries) > 1
    for idx, entry in enumerate(entries):
        eid = entry["_id"]
        with st.container(border=True):
            _card_header(f"Certificate {idx + 1}", "resume_certificates", eid, can_remove)
            c1, c2, c3 = st.columns(3)
            entry["name"] = c1.text_input("Certificate Name", value=entry["name"], key=f"cert_name_{eid}")
            entry["issuer"] = c2.text_input("Issuer", value=entry["issuer"], key=f"cert_issuer_{eid}")
            entry["year"] = c3.text_input("Year", value=entry["year"], key=f"cert_year_{eid}")
    if st.button("➕ Add Another Certificate", key="add_resume_certificates"):
        _add_entry("resume_certificates")
    return entries


def _render_internship_entries() -> list[dict]:
    entries = st.session_state["resume_internships"]
    can_remove = len(entries) > 1
    for idx, entry in enumerate(entries):
        eid = entry["_id"]
        with st.container(border=True):
            _card_header(f"Internship {idx + 1}", "resume_internships", eid, can_remove)
            c1, c2, c3 = st.columns(3)
            entry["role"] = c1.text_input("Role", value=entry["role"], key=f"intern_role_{eid}")
            entry["company"] = c2.text_input("Company", value=entry["company"], key=f"intern_company_{eid}")
            entry["duration"] = c3.text_input("Duration", value=entry["duration"], key=f"intern_duration_{eid}")
            entry["description"] = st.text_area(
                "Description", value=entry["description"], key=f"intern_desc_{eid}", height=70,
            )
    if st.button("➕ Add Another Internship", key="add_resume_internships"):
        _add_entry("resume_internships")
    return entries


# ------------------------------------------------------------------
# Page
# ------------------------------------------------------------------
def render_resume_builder_page():
    _init_state()
    user = st.session_state.get("auth_user") or {}

    hero(
        "ATS Resume Builder", "📄 Resume Builder",
        "Build a clean, single-column, ATS-friendly resume - fill in your "
        "details below, save your progress, then generate a PDF or Word download.",
    )

    glass_card_open("👤 Personal Details")
    c1, c2 = st.columns(2)
    first_name = c1.text_input("First Name *", value=user.get("first_name", ""))
    last_name = c2.text_input("Last Name *", value=user.get("last_name", ""))
    email = st.text_input("Email *", value=user.get("email", ""))
    glass_card_close()

    glass_card_open("🎓 Education")
    education_entries = _render_education_entries()
    glass_card_close()

    glass_card_open("🧠 Skills")
    skills_raw = st.text_area("Skills (comma-separated)", height=70,
                               placeholder="Python, SQL, Data Analysis, Communication")
    glass_card_close()

    glass_card_open("💼 Internships")
    internship_entries = _render_internship_entries()
    glass_card_close()

    glass_card_open("🛠️ Projects")
    project_entries = _render_project_entries()
    glass_card_close()

    glass_card_open("🏅 Certificates")
    certificate_entries = _render_certificate_entries()
    glass_card_close()

    glass_card_open("🏆 Achievements")
    achievements = st.text_area("Achievements (one per line)", height=80)
    glass_card_close()

    glass_card_open("🌐 Hobbies")
    hobbies_raw = st.text_input("Hobbies (comma-separated)")
    glass_card_close()

    def _build_profile() -> ResumeProfile:
        return ResumeProfile(
            first_name=first_name.strip(),
            last_name=last_name.strip(),
            email=email.strip(),
            education=_education_entries_to_text(education_entries),
            skills=[s.strip() for s in skills_raw.split(",") if s.strip()],
            achievements=achievements.strip(),
            hobbies=[s.strip() for s in hobbies_raw.split(",") if s.strip()],
            projects=[
                ProjectEntry(title=e["title"], tech_stack=e["tech_stack"], description=e["description"])
                for e in project_entries if e["title"].strip()
            ],
            certificates=[
                CertificateEntry(name=e["name"], issuer=e["issuer"], year=e["year"])
                for e in certificate_entries if e["name"].strip()
            ],
            internships=[
                InternshipEntry(role=e["role"], company=e["company"],
                                 duration=e["duration"], description=e["description"])
                for e in internship_entries if e["role"].strip()
            ],
        )

    b1, b2, b3, b4 = st.columns(4)

    if b1.button("💾 Save Resume", use_container_width=True):
        if not (first_name and last_name and email):
            st.error("First Name, Last Name, and Email are required to save.")
        else:
            try:
                save_resume(_build_profile())
                st.success("✅ Resume details saved.")
            except Exception as exc:
                st.error(f"Couldn't save your resume details right now: {exc}")

    if b2.button("✨ Generate Resume", use_container_width=True):
        if not (first_name and last_name and email):
            st.error("First Name, Last Name, and Email are required to generate a resume.")
        else:
            st.session_state["resume_profile"] = _build_profile()
            st.success("✅ Resume generated below - use the download buttons to save it.")

    profile: ResumeProfile | None = st.session_state["resume_profile"]

    with b3:
        if profile is not None:
            try:
                pdf_bytes = build_resume_pdf(profile)
                st.download_button(
                    "⬇️ Download PDF", data=pdf_bytes,
                    file_name=f"{profile.full_name.replace(' ', '_') or 'resume'}.pdf",
                    mime="application/pdf", use_container_width=True,
                )
            except Exception as exc:
                st.error(f"Couldn't generate the PDF right now: {exc}")
        else:
            st.button("⬇️ Download PDF", disabled=True, use_container_width=True)

    with b4:
        if profile is not None:
            try:
                docx_bytes = build_resume_docx(profile)
                st.download_button(
                    "⬇️ Download DOCX", data=docx_bytes,
                    file_name=f"{profile.full_name.replace(' ', '_') or 'resume'}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True,
                )
            except Exception as exc:
                st.error(f"Couldn't generate the Word document right now: {exc}")
        else:
            st.button("⬇️ Download DOCX", disabled=True, use_container_width=True)

    if profile is not None:
        st.markdown("### 👁️ Preview")
        glass_card_open(profile.full_name or "Your Name")
        st.caption(profile.email)
        if profile.education:
            st.markdown("**Education**")
            st.text(profile.education)
        if profile.skills:
            st.markdown(f"**Skills**  \n{', '.join(profile.skills)}")
        glass_card_close()

    if not email:
        st.caption("Add your email above so your resume can be saved and retrieved later.")
