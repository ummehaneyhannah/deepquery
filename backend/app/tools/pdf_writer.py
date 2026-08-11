"""
PDF generation utility — turns an agent answer into a downloadable PDF.

Uses reportlab's simple paragraph-flow API rather than manual coordinate
placement, so text wraps and paginates automatically regardless of answer
length.
"""

import io
import logging

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

logger = logging.getLogger(__name__)


def build_pdf(question: str, answer: str, sources: list[str]) -> bytes:
    """
    Render a question/answer/sources triple as a simple report-style PDF.
    Returns raw PDF bytes, ready to stream back to the client.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
        leftMargin=0.85 * inch,
        rightMargin=0.85 * inch,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "DeepQueryTitle", parent=styles["Heading1"], fontSize=16, spaceAfter=4
    )
    question_style = ParagraphStyle(
        "DeepQueryQuestion", parent=styles["Heading2"], fontSize=12, textColor="#555555"
    )
    body_style = ParagraphStyle(
        "DeepQueryBody", parent=styles["BodyText"], fontSize=11, leading=16
    )
    source_style = ParagraphStyle(
        "DeepQuerySource", parent=styles["BodyText"], fontSize=9, textColor="#666666"
    )

    # reportlab's Paragraph treats & < > as XML — escape user/model text
    # before wrapping it, otherwise a stray "<" in the answer breaks layout.
    def esc(text: str) -> str:
        return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    story = [
        Paragraph("DeepQuery Research Dispatch", title_style),
        Spacer(1, 12),
        Paragraph(f"Question: {esc(question)}", question_style),
        Spacer(1, 10),
        Paragraph(esc(answer).replace("\n", "<br/>"), body_style),
    ]

    if sources:
        story.append(Spacer(1, 18))
        story.append(Paragraph("Sources", question_style))
        for i, url in enumerate(sources, start=1):
            story.append(Paragraph(f"[{i}] {esc(url)}", source_style))

    doc.build(story)
    return buffer.getvalue()