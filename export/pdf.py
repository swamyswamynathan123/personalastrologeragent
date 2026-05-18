"""
PDF export for natal and synastry reports using reportlab.

reportlab handles the full Unicode range natively (astrological symbols,
degree signs, em-dashes, curly quotes) without needing external font files.

Chart wheels (SVGs) are embedded via svglib: each SVG is scaled to fit the
page width and inserted as a reportlab Drawing before the report text.
"""
from __future__ import annotations

import io
import re

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer

# Page usable width: A4 210mm − 2×20mm margins = 170mm
_PAGE_WIDTH_PTS = 170 * mm

_PURPLE = colors.HexColor("#4a2d7a")
_LIGHT_PURPLE = colors.HexColor("#6644aa")
_ACCENT = colors.HexColor("#c8a8f8")
_GREY = colors.HexColor("#666666")
_LIGHT_GREY = colors.HexColor("#999999")
_RULE_GREY = colors.HexColor("#cccccc")


def _make_styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        "AstroTitle", parent=styles["Title"],
        fontSize=20, textColor=_PURPLE, spaceAfter=4,
    ))
    styles.add(ParagraphStyle(
        "AstroMeta", parent=styles["Normal"],
        fontSize=10, textColor=_GREY, spaceAfter=2,
        fontName="Helvetica-Oblique",
    ))
    styles.add(ParagraphStyle(
        "AstroH2", parent=styles["Heading2"],
        fontSize=14, textColor=_LIGHT_PURPLE, spaceBefore=14, spaceAfter=4,
    ))
    styles.add(ParagraphStyle(
        "AstroH3", parent=styles["Heading3"],
        fontSize=12, textColor=_LIGHT_PURPLE, spaceBefore=8, spaceAfter=3,
    ))
    styles.add(ParagraphStyle(
        "AstroBody", parent=styles["Normal"],
        fontSize=11, leading=17, spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        "AstroBullet", parent=styles["Normal"],
        fontSize=11, leading=15, leftIndent=16, spaceAfter=3,
    ))
    styles.add(ParagraphStyle(
        "AstroFooter", parent=styles["Normal"],
        fontSize=8, textColor=_LIGHT_GREY, alignment=1,
    ))
    return styles


def _inline(text: str) -> str:
    """Convert inline markdown to reportlab XML markup."""
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"__(.+?)__", r"<b>\1</b>", text)
    text = re.sub(r"\*([^*]+)\*", r"<i>\1</i>", text)
    text = re.sub(r"(?<![_])_([^_]+)_(?![_])", r"<i>\1</i>", text)
    return text


def _md_to_flowables(text: str, styles) -> list:
    """Parse markdown text into reportlab Platypus flowables."""
    flowables = []
    blocks = re.split(r"\n{2,}", text.strip())

    for block in blocks:
        block = block.strip()
        if not block:
            continue

        if block.startswith("### "):
            flowables.append(Paragraph(block[4:], styles["AstroH3"]))
        elif block.startswith("## "):
            flowables.append(Paragraph(block[3:], styles["AstroH2"]))
        elif block.startswith("# "):
            flowables.append(Paragraph(block[2:], styles["AstroH2"]))
        elif re.search(r"^[-*] ", block, re.MULTILINE):
            for line in block.splitlines():
                m = re.match(r"^[-*] (.+)", line.strip())
                if m:
                    flowables.append(
                        Paragraph("• " + _inline(m.group(1)), styles["AstroBullet"])
                    )
        elif re.match(r"^\d+\. ", block):
            for line in block.splitlines():
                m = re.match(r"^(\d+)\. (.+)", line.strip())
                if m:
                    flowables.append(
                        Paragraph(f"{m.group(1)}. {_inline(m.group(2))}", styles["AstroBody"])
                    )
        elif re.match(r"^\*\*[^*]+\*\*$", block):
            # Bold-only line used as section heading (e.g. **1. Section Name**)
            heading = re.sub(r"^\*\*(.+)\*\*$", r"\1", block)
            flowables.append(Paragraph(heading, styles["AstroH2"]))
        else:
            for line in block.splitlines():
                line = line.strip()
                if line:
                    flowables.append(Paragraph(_inline(line), styles["AstroBody"]))

    return flowables


# Fallback palette for kerykeion CSS variables that may not appear in the SVG's
# own :root block (e.g. dynamically injected percentage-bar colors).
_KERYKEION_FALLBACKS: dict[str, str] = {
    "--kerykeion-chart-color-paper-0":             "#ffffff",
    "--kerykeion-chart-color-paper-1":             "#f0f0f0",
    "--kerykeion-chart-color-fire-percentage":     "#ff6600",
    "--kerykeion-chart-color-earth-percentage":    "#669900",
    "--kerykeion-chart-color-air-percentage":      "#ccaa00",
    "--kerykeion-chart-color-water-percentage":    "#3388cc",
    "--kerykeion-chart-color-trine":               "#36d100",
    "--kerykeion-chart-color-conjunction":         "#5765fb",
    "--kerykeion-chart-color-opposition":          "#ff0000",
    "--kerykeion-chart-color-square":              "#ff0000",
    "--kerykeion-chart-color-sextile":             "#9090fb",
    "--kerykeion-chart-color-quincunx":            "#aaaa00",
    "--kerykeion-chart-color-semi-sextile":        "#aaaa00",
}


def _resolve_css_vars(svg_str: str) -> str:
    """Replace CSS custom properties (var(--x)) with their literal values.

    svglib cannot evaluate CSS variables, so we:
    1. Extract every --variable: value definition from all <style>/:root blocks.
    2. Merge with a built-in fallback palette for kerykeion vars absent from
       the SVG's own style block (e.g. percentage-bar colors).
    3. Substitute every var(--name) occurrence with the resolved literal.
    """
    css_vars: dict[str, str] = dict(_KERYKEION_FALLBACKS)  # start with fallbacks

    # Collect definitions from every <style> block and every :root rule inside it
    for style_content in re.findall(r"<style[^>]*>(.*?)</style>", svg_str, re.DOTALL | re.IGNORECASE):
        for root_content in re.findall(r":root\s*\{([^}]+)\}", style_content, re.DOTALL):
            for m in re.finditer(r"(--[\w-]+)\s*:\s*([^;]+);", root_content):
                css_vars[m.group(1).strip()] = m.group(2).strip()

    def _sub(match: re.Match) -> str:
        var_name = match.group(1).strip()
        fallback = (match.group(2) or "").strip() or "#000000"
        return css_vars.get(var_name, fallback)

    # One pass is enough; kerykeion doesn't chain variables
    return re.sub(
        r"var\(\s*(--[\w-]+)\s*(?:,\s*([^)]+))?\s*\)",
        _sub,
        svg_str,
    )


def _svg_flowable(svg_str: str, max_width_pts: float = _PAGE_WIDTH_PTS):
    """Convert an SVG string to a scaled reportlab Drawing, or return None on failure."""
    try:
        import tempfile
        import os
        from svglib.svglib import svg2rlg

        resolved = _resolve_css_vars(svg_str)
        with tempfile.NamedTemporaryFile(
            suffix=".svg", delete=False, mode="w", encoding="utf-8"
        ) as f:
            f.write(resolved)
            tmp_path = f.name
        try:
            drawing = svg2rlg(tmp_path)
        finally:
            os.unlink(tmp_path)

        if drawing is None or drawing.width == 0:
            return None

        scale = max_width_pts / drawing.width
        drawing.width = max_width_pts
        drawing.height = drawing.height * scale
        drawing.transform = (scale, 0, 0, scale, 0, 0)
        return drawing
    except Exception:
        return None


def _footer(styles) -> list:
    return [
        Spacer(1, 16),
        HRFlowable(width="100%", thickness=0.5, color=_RULE_GREY),
        Spacer(1, 4),
        Paragraph("Generated by Personal Astrologer Agent · For personal use only", styles["AstroFooter"]),
    ]


def natal_pdf(result: dict) -> bytes:
    """Return PDF bytes for a natal chart reading."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        rightMargin=20 * mm, leftMargin=20 * mm,
        topMargin=20 * mm, bottomMargin=20 * mm,
        title=f"Natal Reading — {result.get('full_name', '')}",
        author="Personal Astrologer Agent",
    )
    styles = _make_styles()
    story: list = []

    story.append(Paragraph(f"Natal Chart Reading — {result.get('full_name', '')}", styles["AstroTitle"]))
    story.append(Paragraph(
        f"Born {result.get('parsed_dob', '')} · {result.get('birth_location', '')}",
        styles["AstroMeta"],
    ))
    current_dt = (result.get("parsed_current_datetime") or "")[:10]
    story.append(Paragraph(
        f"Current location: {result.get('current_location', '')} · Reading date: {current_dt}",
        styles["AstroMeta"],
    ))
    if result.get("report_focus"):
        story.append(Paragraph(f"Focus: {result['report_focus']}", styles["AstroMeta"]))
    story.append(Spacer(1, 6))
    story.append(HRFlowable(width="100%", thickness=1.5, color=_ACCENT))
    story.append(Spacer(1, 12))

    # Embed chart wheels if available
    chart_data = result.get("chart_data") or {}
    _charts = [
        ("Natal Chart Wheel", chart_data.get("chart_svg") or ""),
        ("Transit Overlay", chart_data.get("transit_svg") or ""),
        ("Vedic Chart Wheel", chart_data.get("vedic_svg") or ""),
    ]
    _any_chart = False
    for chart_title, svg_str in _charts:
        if not svg_str:
            continue
        drawing = _svg_flowable(svg_str)
        if drawing is None:
            continue
        story.append(Paragraph(chart_title, styles["AstroH2"]))
        story.append(Spacer(1, 4))
        story.append(drawing)
        story.append(Spacer(1, 14))
        _any_chart = True
    if _any_chart:
        story.append(HRFlowable(width="100%", thickness=0.5, color=_RULE_GREY))
        story.append(Spacer(1, 12))

    report_text = result.get("final_report") or ""
    story.extend(_md_to_flowables(report_text, styles))
    story.extend(_footer(styles))

    doc.build(story)
    return buf.getvalue()


def synastry_pdf(syn: dict) -> bytes:
    """Return PDF bytes for a synastry compatibility reading."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        rightMargin=20 * mm, leftMargin=20 * mm,
        topMargin=20 * mm, bottomMargin=20 * mm,
        title=f"Synastry — {syn.get('name_a', '')} & {syn.get('name_b', '')}",
        author="Personal Astrologer Agent",
    )
    styles = _make_styles()
    story: list = []

    story.append(Paragraph(
        f"Synastry: {syn.get('name_a', '')} &amp; {syn.get('name_b', '')}",
        styles["AstroTitle"],
    ))
    story.append(Paragraph(
        f"{syn.get('name_a', '')}: {syn.get('dob_a', '')} · {syn.get('loc_a', '')}",
        styles["AstroMeta"],
    ))
    story.append(Paragraph(
        f"{syn.get('name_b', '')}: {syn.get('dob_b', '')} · {syn.get('loc_b', '')}",
        styles["AstroMeta"],
    ))
    story.append(Spacer(1, 6))
    story.append(HRFlowable(width="100%", thickness=1.5, color=_ACCENT))
    story.append(Spacer(1, 12))

    report_text = syn.get("report") or ""
    story.extend(_md_to_flowables(report_text, styles))
    story.extend(_footer(styles))

    doc.build(story)
    return buf.getvalue()
