import re
from datetime import date, datetime
from typing import Tuple, List, Dict

REQUIRED_FIELDS = [
    "full_name",
    "dob",
    "birth_location",
    "birth_time",
    "current_location",
    "current_datetime",
]

_DOB_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")

_VAGUE_BIRTH_TIME_TERMS = {
    "morning", "afternoon", "evening", "night", "dawn",
    "dusk", "noon", "unknown", "approximate", "approx",
}


def find_missing_fields(payload: dict) -> List[str]:
    missing = []
    for field in REQUIRED_FIELDS:
        val = payload.get(field)
        if val is None or (isinstance(val, str) and not val.strip()):
            missing.append(field)
    return missing


def validate_dob_format(dob: str) -> Tuple[bool, str]:
    if not isinstance(dob, str):
        return False, "Date of birth must be a string in YYYY-MM-DD format (e.g., 1990-05-15)."
    if not _DOB_PATTERN.match(dob):
        return False, f"Date of birth '{dob}' must be in YYYY-MM-DD format (e.g., 1990-05-15)."
    try:
        date.fromisoformat(dob)
        return True, ""
    except ValueError:
        return False, f"'{dob}' is not a valid calendar date."


def _is_vague(lower: str) -> bool:
    for term in _VAGUE_BIRTH_TIME_TERMS:
        if re.search(rf"\b{re.escape(term)}\b", lower):
            return True
    return False


def validate_birth_time(birth_time: str) -> Tuple[bool, str]:
    if not birth_time or not birth_time.strip():
        return False, "Birth time is required. Please provide an exact time (e.g., 14:30 or 2:30 PM)."
    lower = birth_time.strip().lower()
    if _is_vague(lower):
        return (
            False,
            f"Birth time '{birth_time}' is too vague. Please provide an exact time in HH:MM format (24-hour) or HH:MM AM/PM.",
        )
    return True, ""


def validate_current_datetime(current_datetime: str) -> Tuple[bool, str]:
    if not current_datetime or not current_datetime.strip():
        return False, "Current datetime must be provided by the application."
    try:
        dt = datetime.fromisoformat(current_datetime.strip().replace("Z", "+00:00"))
        if dt.tzinfo is None:
            return False, "Current datetime must include a timezone offset (e.g., 2026-05-15T14:30:00+00:00)."
        return True, ""
    except ValueError:
        return False, f"Current datetime '{current_datetime}' is not a valid ISO 8601 datetime."


def validate_all(payload: dict) -> Tuple[List[str], Dict[str, str]]:
    missing = find_missing_fields(payload)
    errors: Dict[str, str] = {}

    if "dob" not in missing:
        ok, msg = validate_dob_format(payload["dob"])
        if not ok:
            errors["dob"] = msg

    if "birth_time" not in missing:
        ok, msg = validate_birth_time(payload["birth_time"])
        if not ok:
            errors["birth_time"] = msg

    if "current_datetime" not in missing:
        ok, msg = validate_current_datetime(payload["current_datetime"])
        if not ok:
            errors["current_datetime"] = msg

    return missing, errors
