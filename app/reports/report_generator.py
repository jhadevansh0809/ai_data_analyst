"""PDF report generation for analytics results.

Builds the PDF entirely in memory (no disk or object storage).
Embeds a chart image when chart_json is Plotly-compatible (Kaleido).
"""

from __future__ import annotations

import logging
import os
import tempfile
import uuid
from datetime import datetime
from html import escape as html_escape
from io import BytesIO
from typing import Any

import markdown
import plotly.graph_objects as go
from bs4 import BeautifulSoup, NavigableString, Tag
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Image as RLImage
from reportlab.platypus import Paragraph, Preformatted, SimpleDocTemplate, Spacer

logger = logging.getLogger(__name__)


def _inline_to_reportlab_markup(element: Tag) -> str:
    """Turn inline HTML (strong, em, code, br, links) into ReportLab Paragraph markup."""
    parts: list[str] = []
    for child in element.children:
        if isinstance(child, NavigableString):
            parts.append(html_escape(str(child)))
        elif not isinstance(child, Tag):
            continue
        elif child.name in ("strong", "b"):
            parts.append("<b>" + _inline_to_reportlab_markup(child) + "</b>")
        elif child.name in ("em", "i"):
            parts.append("<i>" + _inline_to_reportlab_markup(child) + "</i>")
        elif child.name == "br":
            parts.append("<br/>")
        elif child.name == "code":
            parts.append('<font face="Courier">' + html_escape(child.get_text()) + "</font>")
        elif child.name == "a":
            parts.append(html_escape(child.get_text()))
        elif child.name == "p":
            parts.append(_inline_to_reportlab_markup(child))
        else:
            parts.append(_inline_to_reportlab_markup(child))
    return "".join(parts)


def _markdown_insights_to_flowables(insights: str, styles: Any) -> list:
    """Convert markdown summary to ReportLab flowables (readable text, not raw md syntax)."""
    if not insights or not insights.strip():
        return [Paragraph("-", styles["Normal"])]

    html_str = markdown.markdown(
        insights.strip(),
        extensions=["nl2br", "fenced_code", "tables", "sane_lists"],
    )
    soup = BeautifulSoup(f"<div>{html_str}</div>", "html.parser")
    root = soup.div
    if root is None:
        return [Paragraph(html_escape(insights.strip()), styles["Normal"])]

    out: list = []
    for el in root.children:
        if isinstance(el, NavigableString):
            t = str(el).strip()
            if t:
                out.append(Paragraph(html_escape(t), styles["Normal"]))
            continue
        if not isinstance(el, Tag) or not el.name:
            continue

        if el.name == "p":
            out.append(Paragraph(_inline_to_reportlab_markup(el), styles["Normal"]))
            out.append(Spacer(1, 6))
        elif el.name in ("h1", "h2", "h3", "h4"):
            out.append(Paragraph(_inline_to_reportlab_markup(el), styles["Heading2"]))
            out.append(Spacer(1, 8))
        elif el.name == "ul":
            for li in el.find_all("li", recursive=False):
                out.append(Paragraph("• " + _inline_to_reportlab_markup(li), styles["Normal"]))
            out.append(Spacer(1, 6))
        elif el.name == "ol":
            for i, li in enumerate(el.find_all("li", recursive=False), start=1):
                out.append(Paragraph(f"{i}. " + _inline_to_reportlab_markup(li), styles["Normal"]))
            out.append(Spacer(1, 6))
        elif el.name == "pre":
            code = el.get_text()
            out.append(Preformatted(code, styles["Code"]))
            out.append(Spacer(1, 6))
        elif el.name == "blockquote":
            out.append(Paragraph("<i>" + _inline_to_reportlab_markup(el) + "</i>", styles["Normal"]))
            out.append(Spacer(1, 6))
        elif el.name == "table":
            out.append(Preformatted(el.get_text(separator="\n"), styles["Code"]))
            out.append(Spacer(1, 6))
        elif el.name == "hr":
            out.append(Spacer(1, 12))

    if not out:
        out.append(Paragraph(html_escape(insights.strip()), styles["Normal"]))
    return out


def _chart_json_to_png_bytes(chart_json: dict[str, Any] | None) -> bytes | None:
    """Render chart JSON to PNG bytes using Kaleido, or None if not possible."""
    if not chart_json:
        return None
    try:
        if chart_json.get("type") == "table":
            columns = chart_json.get("columns", [])
            rows = chart_json.get("rows", [])
            values = [[row.get(col) for row in rows] for col in columns]
            fig = go.Figure(
                data=[
                    go.Table(
                        header=dict(values=columns),
                        cells=dict(values=values),
                    )
                ]
            )
            fig.update_layout(title=chart_json.get("title") or "Table")
        elif "data" in chart_json and "layout" in chart_json:
            fig = go.Figure(chart_json)
        else:
            return None

        buf = BytesIO()
        fig.write_image(buf, format="png", width=900, height=520, engine="kaleido", scale=1)
        return buf.getvalue()
    except Exception as e:
        logger.warning("[report] Could not render chart to PNG for PDF: %s", e)
        return None


class ReportGenerator:
    """Service for generating PDF reports in memory."""

    def generate_report(
        self,
        user_query: str,
        insights: str | None,
        chart_json: dict[str, Any] | None = None,
    ) -> tuple[str, bytes]:
        """Build a PDF in memory. Returns (report_id, pdf_bytes).

        Includes summary text and an embedded chart image when Kaleido can render it.
        """
        report_id = str(uuid.uuid4())

        styles = getSampleStyleSheet()
        story: list = []

        story.append(Paragraph("Report", styles["Title"]))
        story.append(Spacer(1, 12))

        created_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        story.append(Paragraph(f"Created at: {created_at}", styles["Normal"]))
        story.append(Spacer(1, 12))

        if user_query:
            story.append(Paragraph("<b>Your question</b>", styles["Heading2"]))
            story.append(Paragraph(html_escape(user_query), styles["Normal"]))
            story.append(Spacer(1, 12))

        story.append(Paragraph("<b>Summary</b>", styles["Heading2"]))
        story.extend(_markdown_insights_to_flowables(insights or "-", styles))
        story.append(Spacer(1, 12))

        png_bytes = _chart_json_to_png_bytes(chart_json)
        chart_png_path: str | None = None
        if png_bytes:
            story.append(Paragraph("<b>Chart</b>", styles["Heading2"]))
            fd, chart_png_path = tempfile.mkstemp(suffix=".png", prefix="chart_")
            try:
                os.write(fd, png_bytes)
            finally:
                os.close(fd)
            size_reader = ImageReader(chart_png_path)
            iw, ih = size_reader.getSize()
            if iw > 0 and ih > 0:
                max_w = 6.2 * inch
                w = max_w
                h = w * ih / float(iw)
                max_h = 5.0 * inch
                if h > max_h:
                    h = max_h
                    w = h * float(iw) / float(ih)
                story.append(RLImage(chart_png_path, width=w, height=h))
            story.append(Spacer(1, 12))
        elif chart_json:
            story.append(Paragraph("<b>Chart</b>", styles["Heading2"]))
            story.append(
                Paragraph(
                    "Chart could not be embedded as an image in this PDF "
                    "(see the interactive chart in the app).",
                    styles["Normal"],
                )
            )

        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        try:
            doc.build(story)
        finally:
            if chart_png_path:
                try:
                    os.unlink(chart_png_path)
                except OSError:
                    pass

        pdf_bytes = buffer.getvalue()
        return report_id, pdf_bytes


report_generator = ReportGenerator()
