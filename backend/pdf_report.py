"""
backend/pdf_report.py
------------------------
Generates a clean, professional downloadable PDF report of the student's
roadmap using ReportLab. Returns raw PDF bytes so Streamlit's
`st.download_button` can serve it directly (no disk writes required).
"""

from __future__ import annotations

from datetime import datetime
from io import BytesIO
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, ListFlowable,
    ListItem, PageBreak, HRFlowable,
)

from backend.logger_setup import get_logger

logger = get_logger(__name__)

PRIMARY = colors.HexColor("#6C5CE7")
DARK = colors.HexColor("#1A1A2E")
GREY = colors.HexColor("#6b7280")


def _styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="TitleCustom", fontSize=24, leading=28, textColor=DARK,
        spaceAfter=6, fontName="Helvetica-Bold",
    ))
    styles.add(ParagraphStyle(
        name="SubtitleCustom", fontSize=12, leading=16, textColor=PRIMARY,
        spaceAfter=16, fontName="Helvetica-Bold",
    ))
    styles.add(ParagraphStyle(
        name="SectionHeading", fontSize=14, leading=18, textColor=PRIMARY,
        spaceBefore=14, spaceAfter=8, fontName="Helvetica-Bold",
    ))
    styles.add(ParagraphStyle(
        name="WeekHeading", fontSize=12, leading=15, textColor=DARK,
        spaceBefore=10, spaceAfter=4, fontName="Helvetica-Bold",
    ))
    styles.add(ParagraphStyle(
        name="BodyCustom", fontSize=10, leading=14, textColor=DARK,
    ))
    styles.add(ParagraphStyle(
        name="Muted", fontSize=9, leading=12, textColor=GREY,
    ))
    return styles


def build_pdf_report(profile: dict[str, Any], roadmap: dict[str, Any]) -> bytes:
    """Build the PDF and return it as bytes."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=2 * cm, rightMargin=2 * cm, topMargin=2 * cm, bottomMargin=2 * cm,
        title=f"Career Roadmap - {profile.get('name', 'Student')}",
    )
    styles = _styles()
    story = []

    # Header
    story.append(Paragraph("AI Career Learning Pathway Report", styles["TitleCustom"]))
    story.append(Paragraph(
        f"Personalized Roadmap for {profile.get('name', 'Student')} &bull; "
        f"Domain: {str(profile.get('preferred_domain', '')).title()}",
        styles["SubtitleCustom"],
    ))
    story.append(HRFlowable(width="100%", color=PRIMARY, thickness=1.2))
    story.append(Spacer(1, 12))

    # Profile summary table
    profile_rows = [
        ["Career Goal", profile.get("career_goal", "-")],
        ["Current Level", profile.get("current_level", "-")],
        ["Study Hours / Week", str(profile.get("study_hours_per_week", "-"))],
        ["Preferred Domain", str(profile.get("preferred_domain", "-")).title()],
        ["Learning Preference", profile.get("learning_preference", "-")],
        ["Existing Skills", ", ".join(profile.get("existing_skills", []) or ["None specified"])],
        ["Generated On", datetime.now().strftime("%B %d, %Y %H:%M")],
    ]
    table = Table(profile_rows, colWidths=[5 * cm, 11 * cm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F3F1FF")),
        ("TEXTCOLOR", (0, 0), (0, -1), PRIMARY),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(table)
    story.append(Spacer(1, 16))

    # Summary
    if roadmap.get("summary"):
        story.append(Paragraph("Roadmap Overview", styles["SectionHeading"]))
        story.append(Paragraph(roadmap["summary"], styles["BodyCustom"]))
        story.append(Paragraph(
            f"Estimated Duration: {roadmap.get('estimated_duration_weeks', '-')} weeks",
            styles["Muted"],
        ))

    # Weekly milestones
    milestones = roadmap.get("weekly_milestones", [])
    if milestones:
        story.append(Paragraph("Weekly Milestones", styles["SectionHeading"]))
        for m in milestones:
            story.append(Paragraph(
                f"Week {m.get('week', '?')}: {m.get('title', '')}", styles["WeekHeading"]
            ))
            if m.get("key_skills"):
                story.append(Paragraph(
                    f"<b>Key Skills:</b> {', '.join(m['key_skills'])}", styles["BodyCustom"]
                ))
            if m.get("recommended_courses"):
                story.append(Paragraph(
                    f"<b>Recommended Courses:</b> {', '.join(m['recommended_courses'])}",
                    styles["BodyCustom"],
                ))
            if m.get("mini_project"):
                story.append(Paragraph(
                    f"<b>Mini Project:</b> {m['mini_project']}", styles["BodyCustom"]
                ))
            if m.get("practice_tasks"):
                story.append(ListFlowable(
                    [ListItem(Paragraph(t, styles["BodyCustom"])) for t in m["practice_tasks"]],
                    bulletType="bullet", start="circle", leftIndent=14,
                ))
            story.append(Spacer(1, 6))

    story.append(PageBreak())

    # Capstone + certifications
    if roadmap.get("capstone_project"):
        story.append(Paragraph("Capstone Project", styles["SectionHeading"]))
        story.append(Paragraph(roadmap["capstone_project"], styles["BodyCustom"]))
        story.append(Spacer(1, 10))

    if roadmap.get("certifications"):
        story.append(Paragraph("Recommended Certifications", styles["SectionHeading"]))
        story.append(ListFlowable(
            [ListItem(Paragraph(c, styles["BodyCustom"])) for c in roadmap["certifications"]],
            bulletType="bullet", start="circle", leftIndent=14,
        ))
        story.append(Spacer(1, 10))

    # Skill gap analysis
    gaps = roadmap.get("skill_gap_analysis", [])
    if gaps:
        story.append(Paragraph("Skill Gap Analysis", styles["SectionHeading"]))
        rows = [["Skill", "Current Level", "Required Level", "Priority"]]
        for g in gaps:
            rows.append([
                g.get("skill", "-"), g.get("current_level", "-"),
                g.get("required_level", "-"), g.get("priority", "-"),
            ])
        gap_table = Table(rows, colWidths=[6 * cm, 3.3 * cm, 3.3 * cm, 3.4 * cm])
        gap_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F9FAFB")]),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(gap_table)

    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", color=colors.HexColor("#E5E7EB"), thickness=0.8))
    story.append(Paragraph(
        "Generated by AI Career Learning Pathway | Powered by IBM watsonx.ai & Granite",
        styles["Muted"],
    ))

    doc.build(story)
    logger.info("PDF report generated for %s", profile.get("name"))
    return buffer.getvalue()
