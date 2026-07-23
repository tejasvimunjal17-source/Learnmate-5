"""
frontend/resume_review_page.py
---------------------------------
Renders the "Resume Review" page: upload a PDF or DOCX resume, run the
local ATS review pipeline in backend/resume_review.py, and display the
score, missing keywords/sections, strengths, and suggestions - styled
entirely with the existing frontend/components.py building blocks (no
new CSS).
"""

from __future__ import annotations

import streamlit as st

from backend.resume_review import (
    extract_text_from_pdf,
    extract_text_from_docx,
    review_resume,
    detect_missing_keywords,
    ResumeReviewResult,
)
from frontend.components import (
    hero, glass_card_open, glass_card_close, progress_bar, pill_row, empty_state,
)


def _score_label(score: int) -> str:
    if score >= 85:
        return "🟢 Excellent"
    if score >= 70:
        return "🟡 Good"
    if score >= 50:
        return "🟠 Needs Improvement"
    return "🔴 Poor"


def _build_report_text(result: ResumeReviewResult, missing_keywords: list[str]) -> str:
    return (
        "ATS Resume Review Report\n"
        f"Score: {result.ats_score}/100 ({_score_label(result.ats_score)})\n\n"
        f"Missing Sections: {', '.join(result.missing_sections) or 'None'}\n"
        f"Missing Keywords: {', '.join(missing_keywords) or 'None'}\n\n"
        "Strengths:\n" + "\n".join(f"- {s}" for s in result.strengths) + "\n\n"
        "Suggestions:\n" + "\n".join(f"- {s}" for s in result.suggestions)
    )


def render_resume_review_page() -> None:
    hero(
        "ATS Resume Review", "📊 Resume Review",
        "Upload your resume as a PDF or Word document to get an instant ATS score, "
        "missing sections and keywords, and concrete improvement suggestions - "
        "analyzed locally, no data sent to third-party APIs.",
    )

    user = st.session_state.get("auth_user") or {}
    email = user.get("email", "")

    glass_card_open("📤 Upload Resume")
    uploaded = st.file_uploader("Upload PDF or DOCX", type=["pdf", "docx"])
    analyze_clicked = st.button(
        "🔍 Analyze Resume", use_container_width=True, disabled=uploaded is None
    )
    glass_card_close()

    if analyze_clicked and uploaded is not None:
        file_bytes = uploaded.read()
        try:
            if uploaded.name.lower().endswith(".pdf"):
                text = extract_text_from_pdf(file_bytes)
            else:
                text = extract_text_from_docx(file_bytes)
        except Exception:
            st.error("Couldn't read that file. Please make sure it's a valid, text-based PDF or DOCX.")
            text = ""

        if text:
            with st.spinner("Analyzing your resume..."):
                result = review_resume(text, email=email)
                _, missing_keywords = detect_missing_keywords(text)
            st.session_state["resume_review_result"] = result
            st.session_state["resume_review_missing_keywords"] = missing_keywords
        else:
            st.warning("No readable text was found in that file.")

    result: ResumeReviewResult | None = st.session_state.get("resume_review_result")
    missing_keywords: list[str] = st.session_state.get("resume_review_missing_keywords", [])

    if result is None:
        empty_state("📄", "Upload a resume and click **Analyze Resume** to get started.")
        return

    glass_card_open("🎯 ATS Score")
    st.markdown(f"### {result.ats_score} / 100 — {_score_label(result.ats_score)}")
    progress_bar(result.ats_score, "ATS Compatibility")
    glass_card_close()

    c1, c2 = st.columns(2)
    with c1:
        glass_card_open("✅ Resume Strengths")
        if result.strengths:
            for s in result.strengths:
                st.markdown(f"- {s}")
        else:
            st.caption("None detected yet.")
        glass_card_close()

        glass_card_open("❌ Missing Sections")
        if result.missing_sections:
            pill_row(result.missing_sections, "pill-high")
        else:
            st.caption("All standard sections are present.")
        glass_card_close()

    with c2:
        glass_card_open("🧩 Missing Keywords")
        if missing_keywords:
            pill_row(missing_keywords[:15], "pill-medium")
        else:
            st.caption("Good keyword coverage.")
        glass_card_close()

        glass_card_open("💡 Suggestions")
        if result.suggestions:
            for tip in result.suggestions:
                st.markdown(f"- {tip}")
        else:
            st.caption("No suggestions - resume looks solid.")
        glass_card_close()

    report_text = _build_report_text(result, missing_keywords)
    st.download_button(
        "⬇️ Download Review Report (.txt)",
        data=report_text,
        file_name="resume_review_report.txt",
        mime="text/plain",
        use_container_width=True,
    )

    if not email:
        st.caption("Log in with an account email to save your review history.")
