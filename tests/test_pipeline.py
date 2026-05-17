"""
Tests for the three-pass report pipeline and synastry three-pass pipeline.

Strategy:
- Pure builders (_build_review_prompt, _build_fact_sheet, etc.) → test as pure functions,
  no mocking needed.
- LLM-calling functions (_review_report, _ground_report, generate_report_stream, etc.) →
  mock the OpenAI client to verify call sequence and data flow without network calls.
"""
import pytest
from unittest.mock import MagicMock, patch, call


@pytest.fixture(autouse=True)
def _isolated_cache(tmp_path, monkeypatch):
    """Redirect the cache DB to a fresh temp file for every test so cache
    hits from one test never bleed into another."""
    import cache.report_cache as rc
    monkeypatch.setattr(rc, "_DB_PATH", tmp_path / "test_pipeline_cache.db")


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

_BASE_STATE = {
    "full_name": "Jane Doe",
    "parsed_dob": "1990-05-15",
    "birth_location": "Mumbai, Maharashtra, India",
    "birth_time": "14:30",
    "birth_time_timezone": "Asia/Kolkata",
    "current_location": "New York, NY, USA",
    "parsed_current_datetime": "2026-05-15T12:00:00+00:00",
    "report_focus": None,
    "additional_info": None,
}

_PLANET = {"sign": "Aries", "position": "15.00", "house": "1", "retrograde": False, "dignity": "domicile"}
_PLANET_DEBIL = {"sign": "Libra", "position": "15.00", "house": "7", "retrograde": False, "dignity": "detriment"}
_PLANET_FALL = {"sign": "Capricorn", "position": "5.00", "house": "10", "retrograde": False, "dignity": "fall"}


def _make_chart(**kwargs):
    base = {
        "sun": _PLANET,
        "moon": {"sign": "Taurus", "position": "20.00", "house": "2", "retrograde": False, "dignity": None},
        "mercury": {"sign": "Gemini", "position": "10.00", "house": "3", "retrograde": False, "dignity": "domicile"},
        "venus": {"sign": "Pisces", "position": "5.00", "house": "12", "retrograde": False, "dignity": "exaltation"},
        "mars": _PLANET_DEBIL,
        "jupiter": {"sign": "Sagittarius", "position": "25.00", "house": "9", "retrograde": False, "dignity": "domicile"},
        "saturn": _PLANET_FALL,
        "uranus": {"sign": "Capricorn", "position": "1.00", "house": "10", "retrograde": False, "dignity": None},
        "neptune": {"sign": "Capricorn", "position": "12.00", "house": "10", "retrograde": False, "dignity": None},
        "pluto": {"sign": "Scorpio", "position": "18.00", "house": "8", "retrograde": False, "dignity": "domicile"},
        "ascendant": {"sign": "Aries", "position": "5.00"},
        "midheaven": {"sign": "Capricorn", "position": "10.00"},
        "transits": [],
        "upcoming_transits": [],
        "solar_arc_aspects": [],
        "progressed_aspects": [],
        "transit_passes": [],
        "aspect_patterns": [],
        "profection": None,
        "firdaria": None,
        "vedic": None,
        "eclipse_sensitivity": [],
        "retrograde_stations": [],
    }
    base.update(kwargs)
    return base


def _state_with_chart(**kwargs):
    return {**_BASE_STATE, "chart_data": _make_chart(**kwargs)}


# ---------------------------------------------------------------------------
# _build_fact_sheet
# ---------------------------------------------------------------------------

from llm.report import _build_fact_sheet


def test_fact_sheet_includes_natal_placements():
    chart = _make_chart()
    sheet = _build_fact_sheet(chart)
    assert "Sun:" in sheet
    assert "Aries" in sheet
    assert "Ascendant:" in sheet


def test_fact_sheet_marks_retrograde():
    chart = _make_chart(mercury={
        "sign": "Virgo", "position": "10.00", "house": "6", "retrograde": True, "dignity": "domicile"
    })
    sheet = _build_fact_sheet(chart)
    assert "Rx" in sheet


def test_fact_sheet_includes_dignity():
    chart = _make_chart()
    sheet = _build_fact_sheet(chart)
    assert "domicile" in sheet or "detriment" in sheet or "fall" in sheet


def test_fact_sheet_includes_profection():
    chart = _make_chart(profection={
        "profected_house": 5, "lord_of_year": "venus", "age": 34,
        "lord_position": "5", "lord_sign": "Pisces",
    })
    sheet = _build_fact_sheet(chart)
    assert "Profection" in sheet
    assert "Venus" in sheet


def test_fact_sheet_includes_firdaria():
    chart = _make_chart(firdaria={
        "major_lord": "saturn", "major_period_end": "2030-06-01",
        "years_remaining_major": 4, "major_period_years": 10,
        "sub_lord": "mercury", "sub_period_end": "2027-03-01",
    })
    sheet = _build_fact_sheet(chart)
    assert "Firdaria" in sheet
    assert "Saturn" in sheet
    assert "Mercury" in sheet


def test_fact_sheet_includes_mahadasha():
    chart = _make_chart(vedic={
        "dasha": {
            "mahadasha_lord": "jupiter", "mahadasha_end": "2033-01-01",
            "years_remaining_mahadasha": 7, "mahadasha_years": 16,
            "antardasha_lord": "saturn", "antardasha_end": "2028-06-01",
        }
    })
    sheet = _build_fact_sheet(chart)
    assert "Mahadasha" in sheet
    assert "Jupiter" in sheet
    assert "Antardasha" in sheet
    assert "Saturn" in sheet


def test_fact_sheet_includes_transit_passes():
    chart = _make_chart(transit_passes=[{
        "transiting_planet": "saturn", "natal_planet": "sun", "aspect": "square",
        "passes": [{"date": "2026-07-15", "orb": "0.1", "retrograde": False}],
    }])
    sheet = _build_fact_sheet(chart)
    assert "Transit Passes" in sheet
    assert "2026-07-15" in sheet


def test_fact_sheet_includes_upcoming_transits():
    chart = _make_chart(upcoming_transits=[{
        "transiting_planet": "pluto", "natal_planet": "moon",
        "aspect": "conjunction", "exact_date": "2026-08-10", "min_orb": 0.05,
    }])
    sheet = _build_fact_sheet(chart)
    assert "Upcoming Transits" in sheet
    assert "2026-08-10" in sheet


def test_fact_sheet_includes_solar_arcs():
    chart = _make_chart(solar_arc_aspects=[{
        "directed_planet": "arc_sun", "natal_planet": "midheaven",
        "aspect": "conjunction", "orb": "0.3", "applying": True,
    }])
    sheet = _build_fact_sheet(chart)
    assert "Solar Arc" in sheet


def test_fact_sheet_includes_aspect_patterns():
    chart = _make_chart(aspect_patterns=[
        {"type": "Grand Trine", "planets": ["sun", "moon", "jupiter"]},
    ])
    sheet = _build_fact_sheet(chart)
    assert "Grand Trine" in sheet


def test_fact_sheet_empty_chart_no_crash():
    sheet = _build_fact_sheet({})
    assert isinstance(sheet, str)
    assert len(sheet) > 0


# ---------------------------------------------------------------------------
# _build_review_prompt
# ---------------------------------------------------------------------------

from llm.report import _build_review_prompt


def test_review_prompt_contains_four_error_types():
    state = _state_with_chart()
    prompt = _build_review_prompt("DRAFT TEXT", state)
    assert "DIGNITY ERROR" in prompt
    assert "SYSTEM MIXING" in prompt
    assert "PATTERN SPINE MISSING" in prompt
    assert "UNSUPPORTED HOUSE CLAIM" in prompt


def test_review_prompt_contains_draft():
    state = _state_with_chart()
    prompt = _build_review_prompt("MY UNIQUE DRAFT CONTENT", state)
    assert "MY UNIQUE DRAFT CONTENT" in prompt


def test_review_prompt_contains_dignity_hierarchy():
    state = _state_with_chart()
    prompt = _build_review_prompt("DRAFT", state)
    assert "Dignity Hierarchy" in prompt


def test_review_prompt_without_chart_data_no_crash():
    state = {**_BASE_STATE, "chart_data": None}
    prompt = _build_review_prompt("DRAFT", state)
    assert "DIGNITY ERROR" in prompt
    assert "Not available" in prompt


# ---------------------------------------------------------------------------
# _build_grounding_prompt
# ---------------------------------------------------------------------------

from llm.report import _build_grounding_prompt


def test_grounding_prompt_contains_four_check_types():
    state = _state_with_chart()
    prompt = _build_grounding_prompt("REPORT TEXT", state)
    assert "DATE MISMATCH" in prompt
    assert "PLACEMENT ERROR" in prompt
    assert "TIMING LORD ERROR" in prompt
    assert "INVENTED ASPECT" in prompt


def test_grounding_prompt_contains_report():
    state = _state_with_chart()
    prompt = _build_grounding_prompt("UNIQUE REPORT CONTENT", state)
    assert "UNIQUE REPORT CONTENT" in prompt


def test_grounding_prompt_contains_fact_sheet():
    chart = _make_chart(profection={
        "profected_house": 3, "lord_of_year": "mercury", "age": 35,
        "lord_position": "10", "lord_sign": "Gemini",
    })
    state = {**_BASE_STATE, "chart_data": chart}
    prompt = _build_grounding_prompt("REPORT", state)
    assert "Mercury" in prompt  # from profection in fact sheet


def test_grounding_prompt_empty_chart_no_crash():
    state = {**_BASE_STATE, "chart_data": {}}
    prompt = _build_grounding_prompt("REPORT", state)
    assert isinstance(prompt, str)


# ---------------------------------------------------------------------------
# _review_report — mocked OpenAI
# ---------------------------------------------------------------------------

from llm.report import _review_report


def _mock_openai_response(text: str) -> MagicMock:
    chunk = MagicMock()
    chunk.choices[0].message.content = text
    return chunk


@patch("llm.report.openai.OpenAI")
def test_review_report_returns_model_content(mock_openai_cls):
    mock_client = MagicMock()
    mock_openai_cls.return_value = mock_client
    mock_client.chat.completions.create.return_value = _mock_openai_response("REVIEWED TEXT")

    state = _state_with_chart()
    result = _review_report("DRAFT", state)
    assert result == "REVIEWED TEXT"


@patch("llm.report.openai.OpenAI")
def test_review_report_falls_back_to_draft_on_empty_response(mock_openai_cls):
    mock_client = MagicMock()
    mock_openai_cls.return_value = mock_client
    mock_client.chat.completions.create.return_value = _mock_openai_response("")

    state = _state_with_chart()
    result = _review_report("ORIGINAL DRAFT", state)
    assert result == "ORIGINAL DRAFT"


@patch("llm.report.openai.OpenAI")
def test_review_report_uses_low_temperature(mock_openai_cls):
    mock_client = MagicMock()
    mock_openai_cls.return_value = mock_client
    mock_client.chat.completions.create.return_value = _mock_openai_response("OK")

    _review_report("DRAFT", _state_with_chart())

    _, kwargs = mock_client.chat.completions.create.call_args
    assert kwargs.get("temperature", 1.0) <= 0.3


# ---------------------------------------------------------------------------
# _ground_report — mocked OpenAI
# ---------------------------------------------------------------------------

from llm.report import _ground_report


@patch("llm.report.openai.OpenAI")
def test_ground_report_returns_model_content(mock_openai_cls):
    mock_client = MagicMock()
    mock_openai_cls.return_value = mock_client
    mock_client.chat.completions.create.return_value = _mock_openai_response("GROUNDED TEXT")

    state = _state_with_chart()
    result = _ground_report("REVIEWED", state)
    assert result == "GROUNDED TEXT"


@patch("llm.report.openai.OpenAI")
def test_ground_report_skips_when_no_chart_data(mock_openai_cls):
    mock_client = MagicMock()
    mock_openai_cls.return_value = mock_client

    state = {**_BASE_STATE, "chart_data": None}
    result = _ground_report("REVIEWED REPORT", state)
    assert result == "REVIEWED REPORT"
    mock_client.chat.completions.create.assert_not_called()


@patch("llm.report.openai.OpenAI")
def test_ground_report_skips_when_empty_chart(mock_openai_cls):
    mock_client = MagicMock()
    mock_openai_cls.return_value = mock_client

    state = {**_BASE_STATE, "chart_data": {}}
    result = _ground_report("REVIEWED REPORT", state)
    assert result == "REVIEWED REPORT"
    mock_client.chat.completions.create.assert_not_called()


@patch("llm.report.openai.OpenAI")
def test_ground_report_uses_zero_temperature(mock_openai_cls):
    mock_client = MagicMock()
    mock_openai_cls.return_value = mock_client
    mock_client.chat.completions.create.return_value = _mock_openai_response("OK")

    _ground_report("REPORT", _state_with_chart())

    _, kwargs = mock_client.chat.completions.create.call_args
    assert kwargs.get("temperature") == 0


# ---------------------------------------------------------------------------
# generate_report_stream — mocked OpenAI (three-pass sequence)
# ---------------------------------------------------------------------------

from llm.report import generate_report_stream


def _mock_completion(text):
    resp = MagicMock()
    resp.choices[0].message.content = text
    return resp


@patch("llm.report.openai.OpenAI")
def test_generate_report_stream_calls_three_passes(mock_openai_cls):
    mock_client = MagicMock()
    mock_openai_cls.return_value = mock_client
    mock_client.chat.completions.create.side_effect = [
        _mock_completion("DRAFT"),      # pass 1
        _mock_completion("REVIEWED"),   # pass 2
        _mock_completion("FINAL"),      # pass 3
    ]

    state = _state_with_chart()
    chunks = list(generate_report_stream(state))
    assert mock_client.chat.completions.create.call_count == 3


@patch("llm.report.openai.OpenAI")
def test_generate_report_stream_yields_final_text(mock_openai_cls):
    mock_client = MagicMock()
    mock_openai_cls.return_value = mock_client
    mock_client.chat.completions.create.side_effect = [
        _mock_completion("DRAFT"),
        _mock_completion("REVIEWED"),
        _mock_completion("LINE ONE\nLINE TWO"),
    ]

    state = _state_with_chart()
    output = "".join(generate_report_stream(state))
    assert "LINE ONE" in output
    assert "LINE TWO" in output


@patch("llm.report.openai.OpenAI")
def test_generate_report_stream_pass1_uses_high_temperature(mock_openai_cls):
    mock_client = MagicMock()
    mock_openai_cls.return_value = mock_client
    mock_client.chat.completions.create.side_effect = [
        _mock_completion("D"), _mock_completion("R"), _mock_completion("F"),
    ]

    list(generate_report_stream(_state_with_chart()))

    first_call_kwargs = mock_client.chat.completions.create.call_args_list[0][1]
    assert first_call_kwargs.get("temperature", 0) >= 0.5


@patch("llm.report.openai.OpenAI")
def test_generate_report_stream_no_chart_skips_pass3(mock_openai_cls):
    """With no chart data, pass 3 (grounding) is skipped — only 2 LLM calls."""
    mock_client = MagicMock()
    mock_openai_cls.return_value = mock_client
    mock_client.chat.completions.create.side_effect = [
        _mock_completion("DRAFT"),
        _mock_completion("REVIEWED"),
    ]

    state = {**_BASE_STATE, "chart_data": None}
    list(generate_report_stream(state))
    assert mock_client.chat.completions.create.call_count == 2


# ===========================================================================
# Synastry three-pass helpers
# ===========================================================================

from llm.report import (
    _build_synastry_fact_sheet,
    _build_synastry_review_prompt,
    _build_synastry_grounding_prompt,
    _review_synastry_report,
    _ground_synastry_report,
    generate_synastry_report_stream,
)

_NAME_A = "Alice"
_NAME_B = "Bob"

_PLANET_A = {"sign": "Leo", "position": "10.00", "house": "5", "retrograde": False, "dignity": "domicile"}
_PLANET_B = {"sign": "Aquarius", "position": "10.00", "house": "11", "retrograde": False, "dignity": "detriment"}


def _chart_a():
    return {
        "sun": _PLANET_A,
        "moon": {"sign": "Cancer", "position": "22.00", "house": "4", "retrograde": False, "dignity": "domicile"},
        "ascendant": {"sign": "Aries", "position": "5.00"},
        "venus": {"sign": "Virgo", "position": "3.00", "house": "6", "retrograde": False, "dignity": "fall"},
        "mars": {"sign": "Scorpio", "position": "15.00", "house": "8", "retrograde": False, "dignity": "domicile"},
        "mercury": {"sign": "Leo", "position": "2.00", "house": "5", "retrograde": False, "dignity": None},
        "jupiter": {"sign": "Pisces", "position": "8.00", "house": "12", "retrograde": False, "dignity": "domicile"},
        "saturn": {"sign": "Capricorn", "position": "20.00", "house": "10", "retrograde": False, "dignity": "domicile"},
    }


def _chart_b():
    return {
        "sun": _PLANET_B,
        "moon": {"sign": "Taurus", "position": "5.00", "house": "2", "retrograde": False, "dignity": "exaltation"},
        "ascendant": {"sign": "Libra", "position": "15.00"},
        "venus": {"sign": "Gemini", "position": "25.00", "house": "9", "retrograde": False, "dignity": None},
        "mars": {"sign": "Sagittarius", "position": "10.00", "house": "3", "retrograde": False, "dignity": None},
        "mercury": {"sign": "Aquarius", "position": "18.00", "house": "5", "retrograde": False, "dignity": None},
        "jupiter": {"sign": "Cancer", "position": "12.00", "house": "10", "retrograde": False, "dignity": "exaltation"},
        "saturn": {"sign": "Aries", "position": "1.00", "house": "7", "retrograde": False, "dignity": "detriment"},
    }


def _synastry(cross_aspects=None, overlays_ba=None, overlays_ab=None, composite=None):
    return {
        "cross_aspects": cross_aspects or [],
        "house_overlays_b_in_a": overlays_ba or [],
        "house_overlays_a_in_b": overlays_ab or [],
        "composite": composite or {},
        "composite_aspects": [],
    }


# ---------------------------------------------------------------------------
# _build_synastry_fact_sheet
# ---------------------------------------------------------------------------

def test_syn_fact_sheet_includes_both_person_placements():
    sheet = _build_synastry_fact_sheet(_NAME_A, _chart_a(), _NAME_B, _chart_b(), _synastry())
    assert _NAME_A in sheet
    assert _NAME_B in sheet
    assert "Leo" in sheet      # Alice's Sun
    assert "Aquarius" in sheet  # Bob's Sun


def test_syn_fact_sheet_includes_cross_aspects():
    syn = _synastry(cross_aspects=[{
        "planet_a": "sun", "planet_b": "moon", "aspect": "trine", "orb": "1.5", "applying": True,
    }])
    sheet = _build_synastry_fact_sheet(_NAME_A, _chart_a(), _NAME_B, _chart_b(), syn)
    assert "Inter-Chart Aspects" in sheet
    assert "trine" in sheet


def test_syn_fact_sheet_includes_house_overlays():
    syn = _synastry(overlays_ba=[{
        "planet": "sun", "sign": "Leo", "house_in_partner": 7,
    }])
    sheet = _build_synastry_fact_sheet(_NAME_A, _chart_a(), _NAME_B, _chart_b(), syn)
    assert "House" in sheet
    assert "7" in sheet


def test_syn_fact_sheet_includes_composite():
    syn = _synastry(composite={
        "sun": {"sign": "Gemini", "position": "15.00", "house": "3"},
        "moon": {"sign": "Scorpio", "position": "5.00", "house": "8"},
    })
    sheet = _build_synastry_fact_sheet(_NAME_A, _chart_a(), _NAME_B, _chart_b(), syn)
    assert "Composite" in sheet
    assert "Gemini" in sheet
    assert "Scorpio" in sheet


def test_syn_fact_sheet_empty_synastry_no_crash():
    sheet = _build_synastry_fact_sheet(_NAME_A, {}, _NAME_B, {}, {})
    assert isinstance(sheet, str)


# ---------------------------------------------------------------------------
# _build_synastry_review_prompt
# ---------------------------------------------------------------------------

def test_syn_review_prompt_contains_four_error_types():
    prompt = _build_synastry_review_prompt(
        "DRAFT", _NAME_A, _chart_a(), _NAME_B, _chart_b(), _synastry()
    )
    assert "CONVERGENCE NOT ADDRESSED" in prompt
    assert "COMPOSITE DIGNITY ERROR" in prompt
    assert "SATURN FRAMING ERROR" in prompt
    assert "HOUSE OVERLAY UNSUPPORTED CLAIM" in prompt


def test_syn_review_prompt_contains_draft():
    prompt = _build_synastry_review_prompt(
        "MY SYNASTRY DRAFT", _NAME_A, _chart_a(), _NAME_B, _chart_b(), _synastry()
    )
    assert "MY SYNASTRY DRAFT" in prompt


def test_syn_review_prompt_flags_composite_debilitated():
    syn = _synastry(composite={
        "venus": {"sign": "Virgo", "position": "5.00", "house": "6", "dignity": "fall"},
    })
    prompt = _build_synastry_review_prompt(
        "DRAFT", _NAME_A, _chart_a(), _NAME_B, _chart_b(), syn
    )
    assert "Venus" in prompt
    assert "fall" in prompt


def test_syn_review_prompt_flags_saturn_hard_aspects():
    syn = _synastry(cross_aspects=[{
        "planet_a": "saturn", "planet_b": "sun", "aspect": "square", "orb": "1.0", "applying": True,
    }])
    prompt = _build_synastry_review_prompt(
        "DRAFT", _NAME_A, _chart_a(), _NAME_B, _chart_b(), syn
    )
    assert "Saturn" in prompt
    assert "square" in prompt


def test_syn_review_prompt_ignores_saturn_soft_aspects():
    syn = _synastry(cross_aspects=[{
        "planet_a": "saturn", "planet_b": "sun", "aspect": "trine", "orb": "1.0", "applying": True,
    }])
    prompt = _build_synastry_review_prompt(
        "DRAFT", _NAME_A, _chart_a(), _NAME_B, _chart_b(), syn
    )
    # Trine should NOT appear in the Saturn challenging contacts list
    assert "trine" not in prompt.split("## Reading")[0]


# ---------------------------------------------------------------------------
# _build_synastry_grounding_prompt
# ---------------------------------------------------------------------------

def test_syn_grounding_prompt_contains_four_check_types():
    prompt = _build_synastry_grounding_prompt(
        "REPORT", _NAME_A, _chart_a(), _NAME_B, _chart_b(), _synastry()
    )
    assert "PLACEMENT ERROR" in prompt
    assert "INVENTED CROSS-ASPECT" in prompt
    assert "COMPOSITE ERROR" in prompt
    assert "HOUSE NUMBER ERROR" in prompt


def test_syn_grounding_prompt_contains_report():
    prompt = _build_synastry_grounding_prompt(
        "UNIQUE SYNASTRY REPORT", _NAME_A, _chart_a(), _NAME_B, _chart_b(), _synastry()
    )
    assert "UNIQUE SYNASTRY REPORT" in prompt


def test_syn_grounding_prompt_contains_fact_sheet_data():
    syn = _synastry(cross_aspects=[{
        "planet_a": "venus", "planet_b": "mars", "aspect": "conjunction", "orb": "0.5", "applying": True,
    }])
    prompt = _build_synastry_grounding_prompt(
        "REPORT", _NAME_A, _chart_a(), _NAME_B, _chart_b(), syn
    )
    assert "conjunction" in prompt


# ---------------------------------------------------------------------------
# _review_synastry_report — mocked OpenAI
# ---------------------------------------------------------------------------

@patch("llm.report.openai.OpenAI")
def test_review_synastry_returns_model_content(mock_openai_cls):
    mock_client = MagicMock()
    mock_openai_cls.return_value = mock_client
    mock_client.chat.completions.create.return_value = _mock_completion("REVIEWED SYNASTRY")

    result = _review_synastry_report(
        "DRAFT", _NAME_A, _chart_a(), _NAME_B, _chart_b(), _synastry()
    )
    assert result == "REVIEWED SYNASTRY"


@patch("llm.report.openai.OpenAI")
def test_review_synastry_falls_back_to_draft_on_empty_response(mock_openai_cls):
    mock_client = MagicMock()
    mock_openai_cls.return_value = mock_client
    mock_client.chat.completions.create.return_value = _mock_completion("")

    result = _review_synastry_report(
        "ORIGINAL DRAFT", _NAME_A, _chart_a(), _NAME_B, _chart_b(), _synastry()
    )
    assert result == "ORIGINAL DRAFT"


@patch("llm.report.openai.OpenAI")
def test_review_synastry_uses_low_temperature(mock_openai_cls):
    mock_client = MagicMock()
    mock_openai_cls.return_value = mock_client
    mock_client.chat.completions.create.return_value = _mock_completion("OK")

    _review_synastry_report("DRAFT", _NAME_A, _chart_a(), _NAME_B, _chart_b(), _synastry())

    _, kwargs = mock_client.chat.completions.create.call_args
    assert kwargs.get("temperature", 1.0) <= 0.3


# ---------------------------------------------------------------------------
# _ground_synastry_report — mocked OpenAI
# ---------------------------------------------------------------------------

@patch("llm.report.openai.OpenAI")
def test_ground_synastry_returns_model_content(mock_openai_cls):
    mock_client = MagicMock()
    mock_openai_cls.return_value = mock_client
    mock_client.chat.completions.create.return_value = _mock_completion("GROUNDED SYNASTRY")

    result = _ground_synastry_report(
        "REVIEWED", _NAME_A, _chart_a(), _NAME_B, _chart_b(), _synastry(
            cross_aspects=[{"planet_a": "sun", "planet_b": "moon", "aspect": "trine", "orb": "1", "applying": True}]
        )
    )
    assert result == "GROUNDED SYNASTRY"


@patch("llm.report.openai.OpenAI")
def test_ground_synastry_skips_when_no_synastry(mock_openai_cls):
    mock_client = MagicMock()
    mock_openai_cls.return_value = mock_client

    result = _ground_synastry_report(
        "REVIEWED REPORT", _NAME_A, {}, _NAME_B, {}, {}
    )
    assert result == "REVIEWED REPORT"
    mock_client.chat.completions.create.assert_not_called()


@patch("llm.report.openai.OpenAI")
def test_ground_synastry_uses_zero_temperature(mock_openai_cls):
    mock_client = MagicMock()
    mock_openai_cls.return_value = mock_client
    mock_client.chat.completions.create.return_value = _mock_completion("OK")

    _ground_synastry_report(
        "REPORT", _NAME_A, _chart_a(), _NAME_B, _chart_b(),
        _synastry(cross_aspects=[{"planet_a": "sun", "planet_b": "moon", "aspect": "trine", "orb": "1", "applying": True}])
    )

    _, kwargs = mock_client.chat.completions.create.call_args
    assert kwargs.get("temperature") == 0


# ---------------------------------------------------------------------------
# generate_synastry_report_stream — three-pass sequence
# ---------------------------------------------------------------------------

@patch("llm.report.openai.OpenAI")
def test_synastry_stream_calls_three_passes(mock_openai_cls):
    mock_client = MagicMock()
    mock_openai_cls.return_value = mock_client
    mock_client.chat.completions.create.side_effect = [
        _mock_completion("DRAFT"),
        _mock_completion("REVIEWED"),
        _mock_completion("FINAL"),
    ]

    syn = _synastry(cross_aspects=[{
        "planet_a": "sun", "planet_b": "moon", "aspect": "trine", "orb": "1", "applying": True
    }])
    list(generate_synastry_report_stream(
        _NAME_A, "1990-01-01", "London, UK", _chart_a(),
        _NAME_B, "1992-06-15", "Paris, France", _chart_b(),
        syn,
    ))
    assert mock_client.chat.completions.create.call_count == 3


@patch("llm.report.openai.OpenAI")
def test_synastry_stream_yields_final_pass_content(mock_openai_cls):
    mock_client = MagicMock()
    mock_openai_cls.return_value = mock_client
    mock_client.chat.completions.create.side_effect = [
        _mock_completion("DRAFT"),
        _mock_completion("REVIEWED"),
        _mock_completion("FINAL LINE A\nFINAL LINE B"),
    ]

    syn = _synastry(cross_aspects=[{
        "planet_a": "sun", "planet_b": "moon", "aspect": "trine", "orb": "1", "applying": True
    }])
    output = "".join(generate_synastry_report_stream(
        _NAME_A, "1990-01-01", "London, UK", _chart_a(),
        _NAME_B, "1992-06-15", "Paris, France", _chart_b(),
        syn,
    ))
    assert "FINAL LINE A" in output
    assert "FINAL LINE B" in output


@patch("llm.report.openai.OpenAI")
def test_synastry_stream_empty_synastry_skips_pass3(mock_openai_cls):
    """Empty synastry dict → grounding skipped → only 2 LLM calls."""
    mock_client = MagicMock()
    mock_openai_cls.return_value = mock_client
    mock_client.chat.completions.create.side_effect = [
        _mock_completion("DRAFT"),
        _mock_completion("REVIEWED"),
    ]

    list(generate_synastry_report_stream(
        _NAME_A, "1990-01-01", "London, UK", {},
        _NAME_B, "1992-06-15", "Paris, France", {},
        {},
    ))
    assert mock_client.chat.completions.create.call_count == 2
