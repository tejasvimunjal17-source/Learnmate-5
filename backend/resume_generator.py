"""
backend/resume_generator.py
------------------------------
Turns a backend.resume_store.ResumeProfile into an ATS-friendly resume
file (PDF or DOCX), returned as bytes for st.download_button().

ATS-friendliness rules followed here (deliberately, not incidentally):
- Single column, no tables, no text boxes, no images, no multi-column
  layout - ATS parsers read left-to-right/top-to-bottom and can silently
  drop content trapped in tables or floating text boxes.
- Standard, consistently-ordered section headings (EDUCATION, SKILLS,
  INTERNSHIP EXPERIENCE, PROJECTS, CERTIFICATIONS, ACHIEVEMENTS, HOBBIES).
- Plain hyphen bullets, not custom glyphs/icons, since some ATS bullet
  fonts don't map to Unicode symbols cleanly.
- Standard fonts (Helvetica / Calibri) at readable sizes, no color-only
  emphasis (bold/caps only).
"""

from __future__ import annotations

import io

from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_LEFT
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH

from backend.resume_store import ResumeProfile
from backend.logger_setup import get_logger

logger = get_logger(__name__)


class ResumeGenerationError(RuntimeError):
    """Raised when a resume file (PDF or DOCX) fails to generate."""


def _validate_profile(profile: ResumeProfile) -> None:
    if not isinstance(profile, ResumeProfile):
        raise ResumeGenerationError(f"Expected a ResumeProfile instance, got {type(profile).__name__}.")
    if not profile.first_name or not profile.first_name.strip():
        raise ResumeGenerationError("Cannot generate a resume without first_name.")
    if not profile.last_name or not profile.last_name.strip():
        raise ResumeGenerationError("Cannot generate a resume without last_name.")


def _contact_line(profile: ResumeProfile) -> str:
    return profile.email.strip() if profile.email else ""


# ------------------------------------------------------------------
# PDF (reportlab)
# ------------------------------------------------------------------
def build_resume_pdf(profile: ResumeProfile) -> bytes:
    """Generate an ATS-friendly, single-column PDF resume.

    Args:
        profile: The ResumeProfile to render.

    Returns:
        The generated PDF file's raw bytes.

    Raises:
        ResumeGenerationError: if `profile` is invalid or PDF rendering fails.
    """
    _validate_profile(profile)

    try:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer, pagesize=LETTER,
            topMargin=0.6 * inch, bottomMargin=0.6 * inch,
            leftMargin=0.7 * inch, rightMargin=0.7 * inch,
            title=f"{profile.full_name} - Resume",
        )
        styles = getSampleStyleSheet()
        name_style = ParagraphStyle(
            "NameStyle", parent=styles["Title"], fontName="Helvetica-Bold",
            fontSize=18, alignment=TA_LEFT, spaceAfter=2,
        )
        contact_style = ParagraphStyle(
            "ContactStyle", parent=styles["Normal"], fontSize=9.5,
            textColor="#333333", spaceAfter=10,
        )
        heading_style = ParagraphStyle(
            "SectionHeading", parent=styles["Heading2"], fontName="Helvetica-Bold",
            fontSize=11.5, spaceBefore=10, spaceAfter=4, textColor="#1a1a1a",
        )
        body_style = ParagraphStyle(
            "Body", parent=styles["Normal"], fontSize=10, leading=14, spaceAfter=3,
        )
        bullet_style = ParagraphStyle(
            "Bullet", parent=body_style, leftIndent=12, bulletIndent=0,
        )

        story = [
            Paragraph(profile.full_name or "Your Name", name_style),
        ]
        contact = _contact_line(profile)
        if contact:
            story.append(Paragraph(contact, contact_style))
        else:
            story.append(Spacer(1, 6))

        def add_heading(text: str) -> None:
            story.append(Paragraph(text.upper(), heading_style))

        if profile.education:
            add_heading("Education")
            for line in profile.education.splitlines():
                if line.strip():
                    story.append(Paragraph(f"- {line.strip()}", bullet_style))

        if profile.skills:
            add_heading("Skills")
            story.append(Paragraph(", ".join(profile.skills), body_style))

        if profile.internships:
            add_heading("Internship Experience")
            for i in profile.internships:
                header = f"<b>{i.role}</b>"
                if i.company:
                    header += f" - {i.company}"
                if i.duration:
                    header += f" ({i.duration})"
                story.append(Paragraph(header, body_style))
                if i.description:
                    story.append(Paragraph(f"- {i.description}", bullet_style))

        if profile.projects:
            add_heading("Projects")
            for p in profile.projects:
                title = p.title + (f" ({p.tech_stack})" if p.tech_stack else "")
                story.append(Paragraph(f"<b>{title}</b>", body_style))
                if p.description:
                    story.append(Paragraph(f"- {p.description}", bullet_style))

        if profile.certificates:
            add_heading("Certifications")
            for c in profile.certificates:
                label = c.name
                if c.issuer:
                    label += f" - {c.issuer}"
                if c.year:
                    label += f" ({c.year})"
                story.append(Paragraph(f"- {label}", bullet_style))

        if profile.achievements:
            add_heading("Achievements")
            for line in profile.achievements.splitlines():
                if line.strip():
                    story.append(Paragraph(f"- {line.strip()}", bullet_style))

        if profile.hobbies:
            add_heading("Hobbies")
            story.append(Paragraph(", ".join(profile.hobbies), body_style))

        story.append(Spacer(1, 4))
        doc.build(story)
        return buffer.getvalue()

    except ResumeGenerationError:
        raise
    except Exception as exc:  # noqa: BLE001
        logger.exception("Failed to generate PDF resume for %s", getattr(profile, "email", "unknown"))
        raise ResumeGenerationError(f"Could not generate PDF resume: {exc}") from exc


# ------------------------------------------------------------------
# DOCX (python-docx)
# ------------------------------------------------------------------
def build_resume_docx(profile: ResumeProfile) -> bytes:
    """Generate an ATS-friendly, single-column DOCX resume.

    Args:
        profile: The ResumeProfile to render.

    Returns:
        The generated DOCX file's raw bytes.

    Raises:
        ResumeGenerationError: if `profile` is invalid or DOCX rendering fails.
    """
    _validate_profile(profile)

    try:
        doc = Document()

        style = doc.styles["Normal"]
        style.font.name = "Calibri"
        style.font.size = Pt(10.5)

        for section in doc.sections:
            section.top_margin = section.bottom_margin = Pt(36)
            section.left_margin = section.right_margin = Pt(50)

        name_p = doc.add_paragraph()
        name_run = name_p.add_run(profile.full_name or "Your Name")
        name_run.bold = True
        name_run.font.size = Pt(18)

        contact = _contact_line(profile)
        if contact:
            contact_p = doc.add_paragraph(contact)
            if contact_p.runs:
                contact_p.runs[0].font.size = Pt(9.5)

        def add_heading(text: str) -> None:
            h = doc.add_paragraph()
            run = h.add_run(text.upper())
            run.bold = True
            run.font.size = Pt(12)
            h.paragraph_format.space_before = Pt(10)
            h.paragraph_format.space_after = Pt(2)

        def add_bullet(text: str) -> None:
            doc.add_paragraph(f"- {text}")

        if profile.education:
            add_heading("Education")
            for line in profile.education.splitlines():
                if line.strip():
                    add_bullet(line.strip())

        if profile.skills:
            add_heading("Skills")
            doc.add_paragraph(", ".join(profile.skills))

        if profile.internships:
            add_heading("Internship Experience")
            for i in profile.internships:
                p = doc.add_paragraph()
                header = i.role
                if i.company:
                    header += f" - {i.company}"
                if i.duration:
                    header += f" ({i.duration})"
                p.add_run(header).bold = True
                if i.description:
                    add_bullet(i.description)

        if profile.projects:
            add_heading("Projects")
            for proj in profile.projects:
                p = doc.add_paragraph()
                title = proj.title + (f" ({proj.tech_stack})" if proj.tech_stack else "")
                p.add_run(title).bold = True
                if proj.description:
                    add_bullet(proj.description)

        if profile.certificates:
            add_heading("Certifications")
            for c in profile.certificates:
                label = c.name
                if c.issuer:
                    label += f" - {c.issuer}"
                if c.year:
                    label += f" ({c.year})"
                add_bullet(label)

        if profile.achievements:
            add_heading("Achievements")
            for line in profile.achievements.splitlines():
                if line.strip():
                    add_bullet(line.strip())

        if profile.hobbies:
            add_heading("Hobbies")
            doc.add_paragraph(", ".join(profile.hobbies))

        buffer = io.BytesIO()
        doc.save(buffer)
        return buffer.getvalue()

    except ResumeGenerationError:
        raise
    except Exception as exc:  # noqa: BLE001
        logger.exception("Failed to generate DOCX resume for %s", getattr(profile, "email", "unknown"))
        raise ResumeGenerationError(f"Could not generate DOCX resume: {exc}") from exc
