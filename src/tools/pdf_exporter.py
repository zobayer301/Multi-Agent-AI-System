from __future__ import annotations
"""
PDF Exporter Module using ReportLab.
Transforms structured ReportOutput Pydantic instances into publication-grade PDF documents.
"""

from io import BytesIO
from typing import Optional, Any, TYPE_CHECKING
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, KeepTogether

if TYPE_CHECKING:
    from src.agents.schemas import ReportOutput


def generate_pdf_report(report: ReportOutput) -> bytes:
    """
    Generate an in-memory PDF binary stream from a ReportOutput object.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=54,
        leftMargin=54,
        topMargin=54,
        bottomMargin=54,
    )

    styles = getSampleStyleSheet()
    
    # Custom Typography Styles
    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#1E3A8A"),
        spaceAfter=12,
    )
    
    h2_style = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=16,
        textColor=colors.HexColor("#1F2937"),
        spaceBefore=12,
        spaceAfter=6,
    )

    body_style = ParagraphStyle(
        "ReportBody",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#374151"),
        spaceAfter=8,
    )

    exec_summary_style = ParagraphStyle(
        "ExecutiveSummary",
        parent=body_style,
        fontName="Helvetica-Oblique",
        fontSize=10.5,
        leading=15,
        textColor=colors.HexColor("#1E40AF"),
        backColor=colors.HexColor("#EFF6FF"),
        borderColor=colors.HexColor("#93C5FD"),
        borderWidth=1,
        borderPadding=10,
        spaceAfter=14,
    )

    bullet_style = ParagraphStyle(
        "ReportBullet",
        parent=body_style,
        leftIndent=15,
        firstLineIndent=-10,
        spaceAfter=4,
    )

    story = []

    # Title
    story.append(Paragraph(report.title, title_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#3B82F6"), spaceAfter=14))

    # Executive Summary Box
    story.append(Paragraph(f"<b>Executive Summary:</b><br/>{report.executive_summary}", exec_summary_style))

    # Topical Sections
    for sec in report.sections:
        story.append(Paragraph(sec.heading, h2_style))
        clean_content = sec.content.replace("\n", "<br/>")
        story.append(Paragraph(clean_content, body_style))

    # Key Takeaways
    story.append(Paragraph("Key Takeaways", h2_style))
    for takeaway in report.key_takeaways:
        story.append(Paragraph(f"&bull; <b>{takeaway}</b>", bullet_style))

    # Conclusion
    story.append(Paragraph("Conclusion & Strategic Outlook", h2_style))
    story.append(Paragraph(report.conclusion.replace("\n", "<br/>"), body_style))

    # References
    story.append(Paragraph("References & Empirical Citations", h2_style))
    for ref in report.references:
        story.append(Paragraph(f"&bull; <i>{ref}</i>", bullet_style))

    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
