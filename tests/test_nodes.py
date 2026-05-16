import pytest
from agent.nodes import (
    ingest_inputs,
    validate_required_fields,
    request_follow_up,
    normalize_and_parse,
)

_BASE = {
    "full_name": "Jane Doe",
    "dob": "1990-05-15",
    "birth_location": "Mumbai, Maharashtra, India",
    "birth_time": "14:30",
    "birth_time_timezone": "Asia/Kolkata",
    "current_location": "New York, NY, USA",
    "additional_info": None,
    "report_focus": None,
    "current_datetime": "2026-05-15T12:00:00+00:00",
    "missing_fields": [],
    "validation_errors": {},
    "parsed_dob": None,
    "parsed_birth_datetime": None,
    "parsed_current_datetime": None,
    "chart_data": None,
    "follow_up_message": None,
    "final_report": None,
}


# --- ingest_inputs ---

def test_ingest_resets_tracking_fields():
    state = {**_BASE, "missing_fields": ["old"], "validation_errors": {"x": "y"}}
    result = ingest_inputs(state)
    assert result["missing_fields"] == []
    assert result["validation_errors"] == {}


def test_ingest_preserves_raw_inputs():
    result = ingest_inputs(_BASE.copy())
    assert result["full_name"] == "Jane Doe"
    assert result["dob"] == "1990-05-15"


# --- validate_required_fields ---

def test_validate_passes_for_complete_state():
    state = {**_BASE, "missing_fields": [], "validation_errors": {}}
    result = validate_required_fields(state)
    assert result["missing_fields"] == []
    assert result["validation_errors"] == {}


def test_validate_detects_missing_name():
    state = {**_BASE, "full_name": None}
    result = validate_required_fields(state)
    assert "full_name" in result["missing_fields"]


def test_validate_detects_bad_dob_format():
    state = {**_BASE, "dob": "15-05-1990"}
    result = validate_required_fields(state)
    assert "dob" in result["validation_errors"]


def test_validate_detects_vague_birth_time():
    state = {**_BASE, "birth_time": "evening"}
    result = validate_required_fields(state)
    assert "birth_time" in result["validation_errors"]


# --- request_follow_up ---

def test_follow_up_message_mentions_missing_fields():
    state = {**_BASE, "missing_fields": ["full_name", "dob"], "validation_errors": {}}
    result = request_follow_up(state)
    msg = result["follow_up_message"]
    assert msg is not None
    assert "full_name" in msg or "Full Name" in msg
    assert "dob" in msg or "Date of Birth" in msg


def test_follow_up_message_mentions_validation_errors():
    state = {**_BASE, "missing_fields": [], "validation_errors": {"dob": "Invalid format"}}
    result = request_follow_up(state)
    msg = result["follow_up_message"]
    assert "dob" in msg or "Date of Birth" in msg
    assert "Invalid format" in msg


def test_follow_up_does_not_set_final_report():
    state = {**_BASE, "missing_fields": ["birth_time"], "validation_errors": {}}
    result = request_follow_up(state)
    assert result.get("final_report") is None


# --- normalize_and_parse ---

def test_normalize_parses_valid_state():
    state = {**_BASE}
    result = normalize_and_parse(state)
    assert result["parsed_dob"] == "1990-05-15"
    assert result["parsed_birth_datetime"] is not None
    assert "+05:30" in result["parsed_birth_datetime"]  # Asia/Kolkata offset
    assert result["parsed_current_datetime"] is not None
    assert result["validation_errors"] == {}


def test_normalize_falls_back_to_utc_when_no_timezone():
    state = {**_BASE, "birth_time_timezone": None}
    result = normalize_and_parse(state)
    assert result["parsed_birth_datetime"] is not None
    assert result["validation_errors"] == {}


def test_normalize_error_on_bad_birth_time_format():
    state = {**_BASE, "birth_time": "25:99"}
    result = normalize_and_parse(state)
    assert "birth_time" in result["validation_errors"]
