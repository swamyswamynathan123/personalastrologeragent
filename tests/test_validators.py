import pytest
from agent.validators import (
    find_missing_fields,
    validate_dob_format,
    validate_birth_time,
    validate_current_datetime,
    validate_all,
)

COMPLETE_PAYLOAD = {
    "full_name": "Jane Doe",
    "dob": "1990-05-15",
    "birth_location": "Mumbai, Maharashtra, India",
    "birth_time": "14:30",
    "current_location": "New York, NY, USA",
    "current_datetime": "2026-05-15T12:00:00+00:00",
}


# --- find_missing_fields ---

def test_no_missing_fields_when_all_present():
    assert find_missing_fields(COMPLETE_PAYLOAD) == []


def test_detects_missing_dob():
    p = {**COMPLETE_PAYLOAD, "dob": None}
    assert "dob" in find_missing_fields(p)


def test_detects_missing_full_name():
    p = {**COMPLETE_PAYLOAD, "full_name": ""}
    assert "full_name" in find_missing_fields(p)


def test_detects_missing_birth_time():
    p = {k: v for k, v in COMPLETE_PAYLOAD.items() if k != "birth_time"}
    assert "birth_time" in find_missing_fields(p)


def test_detects_missing_current_datetime():
    p = {**COMPLETE_PAYLOAD, "current_datetime": "  "}
    assert "current_datetime" in find_missing_fields(p)


# --- validate_dob_format ---

def test_valid_dob():
    ok, msg = validate_dob_format("1990-05-15")
    assert ok is True
    assert msg == ""


def test_dob_wrong_separator():
    ok, msg = validate_dob_format("15/05/1990")
    assert ok is False
    assert "YYYY-MM-DD" in msg


def test_dob_impossible_date():
    ok, msg = validate_dob_format("1990-13-45")
    assert ok is False


def test_dob_partial_format():
    ok, msg = validate_dob_format("1990-5-15")
    assert ok is False


# --- validate_birth_time ---

def test_valid_birth_time_24h():
    ok, msg = validate_birth_time("14:30")
    assert ok is True


def test_valid_birth_time_midnight():
    ok, msg = validate_birth_time("00:00")
    assert ok is True


def test_birth_time_vague_morning():
    ok, msg = validate_birth_time("morning")
    assert ok is False
    assert "vague" in msg.lower() or "exact" in msg.lower()


def test_birth_time_vague_afternoon():
    ok, msg = validate_birth_time("afternoon")
    assert ok is False


def test_birth_time_empty():
    ok, msg = validate_birth_time("")
    assert ok is False


def test_birth_time_unknown():
    ok, msg = validate_birth_time("unknown")
    assert ok is False


# --- validate_current_datetime ---

def test_valid_current_datetime_with_offset():
    ok, msg = validate_current_datetime("2026-05-15T12:00:00+00:00")
    assert ok is True


def test_valid_current_datetime_utc_z():
    ok, msg = validate_current_datetime("2026-05-15T12:00:00Z")
    assert ok is True


def test_invalid_current_datetime_empty():
    ok, msg = validate_current_datetime("")
    assert ok is False


def test_invalid_current_datetime_bad_format():
    ok, msg = validate_current_datetime("May 15 2026")
    assert ok is False


# --- validate_all ---

def test_validate_all_returns_empty_on_valid():
    missing, errors = validate_all(COMPLETE_PAYLOAD)
    assert missing == []
    assert errors == {}


def test_validate_all_catches_missing_and_bad_dob():
    p = {**COMPLETE_PAYLOAD, "full_name": None, "dob": "15-05-1990"}
    missing, errors = validate_all(p)
    assert "full_name" in missing
    assert "dob" in errors
