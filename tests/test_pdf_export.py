"""
Tests for export/pdf.py — PDF generation for natal and synastry reports.

Strategy: generate PDFs from realistic fixture dicts and verify:
- Output is valid PDF bytes (starts with %PDF header)
- Output is non-trivially sized (content was rendered)
- Markdown features are handled without crash (headers, bold, bullets, Unicode)
- Edge cases (missing fields, empty report) don't raise
"""
import pytest
from export.pdf import natal_pdf, synastry_pdf, _inline, _md_to_flowables, _make_styles


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

_NATAL_RESULT = {
    "full_name": "Jane Doe",
    "parsed_dob": "1990-05-15",
    "birth_location": "Mumbai, Maharashtra, India",
    "birth_time": "14:30",
    "birth_time_timezone": "Asia/Kolkata",
    "current_location": "New York, NY, USA",
    "parsed_current_datetime": "2026-05-17T12:00:00+00:00",
    "report_focus": "Career and relationships",
    "final_report": """## 1. Personal Overview

Your **Sun in Aries** at 15.2° sits in the 1st house — bold and pioneering. The Moon in Taurus at 20.0° brings emotional stability. Your Ascendant in Virgo at 5.0° adds analytical precision.

**Saturn in Capricorn** (domicile) is the structural backbone of your chart. Saturn — the great teacher — rewards sustained effort.

## 2. Current Cosmic Climate

Pluto is squaring your natal Sun through 2026-08-15, demanding a reinvention of identity.

- Neptune trine natal Venus (orb 0.8°, applying): creative inspiration
- Jupiter conjunct Midheaven: career expansion window
- Saturn sextile natal Moon: emotional grounding

## 3. Key Life Themes

*Ambition meets sensitivity.* The tension between your Aries Sun and Taurus Moon creates a powerful drive tempered by patience.

## 4. Practical Guidance

Focus on consolidating rather than expanding this month. Saturn's stabilizing influence rewards careful planning over impulsive action.

## 5. Favorable Timing

The window between 2026-06-01 and 2026-06-15 is particularly favorable for career moves, with Jupiter direct and your progressed Moon entering your 10th house.
""",
}

_SYNASTRY_SYN = {
    "name_a": "Alice Smith",
    "dob_a": "1990-03-21",
    "loc_a": "London, UK",
    "name_b": "Bob Jones",
    "dob_b": "1988-11-15",
    "loc_b": "Paris, France",
    "report": """## 1. The Connection at a Glance

This is a **Venus-Mars double whammy** — Alice's Venus trines Bob's Mars and Bob's Venus sextiles Alice's Mars. The chemistry between you two is unmistakable.

## 2. How You Experience Each Other

Bob's Sun falls in Alice's 7th house, activating her partnership zone directly. Alice feels Bob *as* the archetype of relationship itself.

- Alice's Moon (Cancer) in Bob's 4th house: Alice activates Bob's sense of home and family
- Bob's Venus (Libra) in Alice's 5th house: romance, play, and shared creativity

## 3. Attraction, Chemistry & Emotional Resonance

Your Sun-Moon inter-aspect — Alice's Sun conjunct Bob's Moon at orb 1.2° — is the most fundamental signature here. You two naturally support each other's life force and emotional needs.

## 4. Communication, Growth & Long-Term Compatibility

Mercury aspects are harmonious: Alice's Mercury sextile Bob's Mercury suggests easy intellectual exchange. However, Alice's Saturn squares Bob's Sun — a real growth edge requiring conscious navigation.

## 5. The Relationship as Its Own Entity

The composite Sun in Gemini in the 3rd house describes a relationship built on conversation, ideas, and constant learning.

## 6. Strengths & Growth Edges

**Strengths:** Deep emotional resonance, strong Venus-Mars chemistry, complementary life visions.

**Growth edges:** Alice's Saturn square Bob's Sun requires Alice to soften her critical tendencies; Bob needs to own his solar authority rather than shrinking under Alice's structure.
""",
}


# ---------------------------------------------------------------------------
# _inline — inline markdown conversion
# ---------------------------------------------------------------------------

def test_inline_bold():
    assert "<b>text</b>" in _inline("**text**")


def test_inline_italic():
    assert "<i>text</i>" in _inline("*text*")


def test_inline_escapes_ampersand():
    assert "&amp;" in _inline("A & B")


def test_inline_escapes_lt_gt():
    result = _inline("A < B > C")
    assert "&lt;" in result
    assert "&gt;" in result


def test_inline_no_crash_empty():
    assert _inline("") == ""


def test_inline_unicode_preserved():
    result = _inline("Sun ☉ Moon ☽ at 15°")
    assert "☉" in result
    assert "☽" in result
    assert "°" in result


def test_inline_em_dash_preserved():
    result = _inline("Saturn — the teacher")
    assert "—" in result


# ---------------------------------------------------------------------------
# _md_to_flowables — structural parsing
# ---------------------------------------------------------------------------

def test_flowables_h2_block():
    styles = _make_styles()
    flowables = _md_to_flowables("## Section Title\n\nSome text.", styles)
    assert len(flowables) >= 2


def test_flowables_bullet_list():
    styles = _make_styles()
    flowables = _md_to_flowables("- Item one\n- Item two\n- Item three", styles)
    assert len(flowables) == 3


def test_flowables_numbered_list():
    styles = _make_styles()
    flowables = _md_to_flowables("1. First\n2. Second\n3. Third", styles)
    assert len(flowables) == 3


def test_flowables_bold_heading():
    styles = _make_styles()
    flowables = _md_to_flowables("**1. Section Name**\n\nText here.", styles)
    assert len(flowables) >= 2


def test_flowables_empty_text():
    styles = _make_styles()
    flowables = _md_to_flowables("", styles)
    assert flowables == []


def test_flowables_blank_blocks_ignored():
    styles = _make_styles()
    flowables = _md_to_flowables("Hello\n\n\n\nWorld", styles)
    assert len(flowables) == 2


# ---------------------------------------------------------------------------
# natal_pdf — output validation
# ---------------------------------------------------------------------------

def test_natal_pdf_returns_bytes():
    result = natal_pdf(_NATAL_RESULT)
    assert isinstance(result, bytes)


def test_natal_pdf_starts_with_pdf_header():
    result = natal_pdf(_NATAL_RESULT)
    assert result[:4] == b"%PDF"


def test_natal_pdf_non_trivial_size():
    result = natal_pdf(_NATAL_RESULT)
    assert len(result) > 2_000  # compressed PDF; a multi-section report should exceed 2 KB


def test_natal_pdf_with_unicode_symbols():
    report_with_symbols = _NATAL_RESULT.copy()
    report_with_symbols["final_report"] = (
        "## Overview\n\nSun ☉ in Aries at 15°. Moon ☽ in Taurus at 20°. "
        "Venus ♀ in Pisces — grace and compassion."
    )
    result = natal_pdf(report_with_symbols)
    assert result[:4] == b"%PDF"


def test_natal_pdf_missing_name_no_crash():
    result_no_name = {k: v for k, v in _NATAL_RESULT.items() if k != "full_name"}
    pdf = natal_pdf(result_no_name)
    assert pdf[:4] == b"%PDF"


def test_natal_pdf_empty_report_no_crash():
    minimal = {**_NATAL_RESULT, "final_report": ""}
    pdf = natal_pdf(minimal)
    assert pdf[:4] == b"%PDF"


def test_natal_pdf_no_report_focus_no_crash():
    no_focus = {**_NATAL_RESULT, "report_focus": None}
    pdf = natal_pdf(no_focus)
    assert pdf[:4] == b"%PDF"


def test_natal_pdf_minimal_dict_no_crash():
    pdf = natal_pdf({})
    assert pdf[:4] == b"%PDF"


# ---------------------------------------------------------------------------
# synastry_pdf — output validation
# ---------------------------------------------------------------------------

def test_synastry_pdf_returns_bytes():
    result = synastry_pdf(_SYNASTRY_SYN)
    assert isinstance(result, bytes)


def test_synastry_pdf_starts_with_pdf_header():
    result = synastry_pdf(_SYNASTRY_SYN)
    assert result[:4] == b"%PDF"


def test_synastry_pdf_non_trivial_size():
    result = synastry_pdf(_SYNASTRY_SYN)
    assert len(result) > 2_000


def test_synastry_pdf_with_ampersand_in_names():
    syn = {**_SYNASTRY_SYN, "name_a": "Alice & Charlie", "name_b": "Bob & Dave"}
    result = synastry_pdf(syn)
    assert result[:4] == b"%PDF"


def test_synastry_pdf_empty_report_no_crash():
    syn = {**_SYNASTRY_SYN, "report": ""}
    pdf = synastry_pdf(syn)
    assert pdf[:4] == b"%PDF"


def test_synastry_pdf_minimal_dict_no_crash():
    pdf = synastry_pdf({})
    assert pdf[:4] == b"%PDF"


# ---------------------------------------------------------------------------
# Both PDFs are independently sized (content differs)
# ---------------------------------------------------------------------------

def test_natal_and_synastry_pdfs_differ():
    natal = natal_pdf(_NATAL_RESULT)
    syn = synastry_pdf(_SYNASTRY_SYN)
    assert natal != syn
