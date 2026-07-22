"""
backend/resume_generator.py
------------------------------
Turns a ResumeProfile into an ATS-friendly resume file (PDF or DOCX).

ATS-friendliness rules followed here (deliberately, not incidentally):
- Single column, no tables, no text boxes, no images, no multi-column
  layout - ATS parsers read left-to-right/top-to-bottom and can silently
  drop content trapped in tables or floating text boxes.
- Standard section headings (EDUCATION, SKILLS, EXPERIENCE, PROJECTS,
  CERTIFICATIONS) in a consistent, parseable order.
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


def _contact_line(profile: ResumeProfile) -> str:
    parts = [p for p in [
        profile.phone, profile.email, profile.address,
        profile.linkedin, profile.github, profile.portfolio,
    ] if p]
    return "  |  ".join(parts)


# ------------------------------------------------------------------
# PDF (reportlab)
# ------------------------------------------------------------------
def build_resume_pdf(profile: ResumeProfile) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=LETTER,
        topMargin=0.6 * inch, bottomMargin=0.6 * inch,
        leftMargin=0.7 * inch, rightMargin=0.7 * inch,
        title=f"{profile.full_name} - Resume",
    )
    styles = getSampleStyleSheet()
    name_style = ParagraphStyle("NameStyle", parent=styles["Title"],
                                 fontName="Helvetica-Bold", fontSize=18,
                                 alignment=TA_LEFT, spaceAfter=2)
    contact_style = ParagraphStyle("ContactStyle", parent=styles["Normal"],
                                    fontSize=9.5, textColor="#333333",
                                    spaceAfter=10)
    heading_style = ParagraphStyle("SectionHeading", parent=styles["Heading2"],
                                    fontName="Helvetica-Bold", fontSize=11.5,
                                    spaceBefore=10, spaceAfter=4,
                                    textColor="#1a1a1a")
    body_style = ParagraphStyle("Body", parent=styles["Normal"],
                                 fontSize=10, leading=14, spaceAfter=3)
    bullet_style = ParagraphStyle("Bullet", parent=body_style,
                                   leftIndent=12, bulletIndent=0)

    story = [
        Paragraph(profile.full_name or "Your Name", name_style),
        Paragraph(_contact_line(profile), contact_style),
    ]

    def add_heading(text: str) -> None:
        story.append(Paragraph(text.upper(), heading_style))

    if profile.career_objective:
        add_heading("Career Objective")
        story.append(Paragraph(profile.career_objective, body_style))

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
            story.append(Paragraph(f"<b>{i.role}</b> - {i.company} ({i.duration})", body_style))
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
            label = f"{c.name} - {c.issuer}" + (f" ({c.year})" if c.year else "")
            story.append(Paragraph(f"- {label}", bullet_style))

    if profile.achievements:
        add_heading("Achievements")
        for line in profile.achievements.splitlines():
            if line.strip():
                story.append(Paragraph(f"- {line.strip()}", bullet_style))

    if profile.languages:
        add_heading("Languages")
        story.append(Paragraph(", ".join(profile.languages), body_style))

    if profile.hobbies:
        add_heading("Hobbies")
        story.append(Paragraph(", ".join(profile.hobbies), body_style))

    if profile.references:
        add_heading("References")
        story.append(Paragraph(profile.references, body_style))

    story.append(Spacer(1, 4))
    doc.build(story)
    return buffer.getvalue()


# ------------------------------------------------------------------
# DOCX (python-docx)
# ------------------------------------------------------------------
def build_resume_docx(profile: ResumeProfile) -> bytes:
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

    contact_p = doc.add_paragraph(_contact_line(profile))
    contact_p.runs[0].font.size = Pt(9.5) if contact_p.runs else None

    def add_heading(text: str) -> None:
        h = doc.add_paragraph()
        run = h.add_run(text.upper())
        run.bold = True
        run.font.size = Pt(12)
        h.paragraph_format.space_before = Pt(10)
        h.paragraph_format.space_after = Pt(2)

    def add_bullet(text: str) -> None:
        doc.add_paragraph(f"- {text}", style=None)

    if profile.career_objective:
        add_heading("Career Objective")
        doc.add_paragraph(profile.career_objective)

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
            p.add_run(f"{i.role} - {i.company} ({i.duration})").bold = True
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
            label = f"{c.name} - {c.issuer}" + (f" ({c.year})" if c.year else "")
            add_bullet(label)

    if profile.achievements:
        add_heading("Achievements")
        for line in profile.achievements.splitlines():
            if line.strip():
                add_bullet(line.strip())

    if profile.languages:
        add_heading("Languages")
        doc.add_paragraph(", ".join(profile.languages))

    if profile.hobbies:
        add_heading("Hobbies")
        doc.add_paragraph(", ".join(profile.hobbies))

    if profile.references:
        add_heading("References")
        doc.add_paragraph(profile.references)

    buffer = io.BytesIO()
    doc.save(buffer)
    return buffer.getvalue()
