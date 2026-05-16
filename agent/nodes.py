from __future__ import annotations
from datetime import datetime
from typing import TYPE_CHECKING

import pytz

from agent.validators import validate_all

if TYPE_CHECKING:
    from agent.state import AstrologerState

_FIELD_LABELS = {
    "full_name": "Full Name",
    "dob": "Date of Birth (YYYY-MM-DD)",
    "birth_location": "Birth Location (City, Region, Country)",
    "birth_time": "Birth Time (HH:MM, 24-hour)",
    "current_location": "Current Location (City, Region, Country)",
    "current_datetime": "Current Date & Time",
}


def ingest_inputs(state: "AstrologerState") -> dict:
    """Node 1: Accept payload, reset validation tracking fields."""
    return {
        "full_name": state.get("full_name"),
        "dob": state.get("dob"),
        "birth_location": state.get("birth_location"),
        "birth_time": state.get("birth_time"),
        "birth_time_timezone": state.get("birth_time_timezone"),
        "current_location": state.get("current_location"),
        "additional_info": state.get("additional_info"),
        "report_focus": state.get("report_focus"),
        "current_datetime": state.get("current_datetime"),
        "missing_fields": [],
        "validation_errors": {},
        "parsed_dob": None,
        "parsed_birth_datetime": None,
        "parsed_current_datetime": None,
        "chart_data": None,
        "follow_up_message": None,
        "final_report": None,
    }


def validate_required_fields(state: "AstrologerState") -> dict:
    """Node 2: Run all validation checks; populate missing_fields and validation_errors."""
    missing, errors = validate_all(state)
    return {"missing_fields": missing, "validation_errors": errors}


def request_follow_up(state: "AstrologerState") -> dict:
    """Node 3: Build a user-friendly follow-up message listing all issues."""
    lines = ["Please provide or correct the following information before your reading can be generated:\n"]

    for field in state.get("missing_fields", []):
        label = _FIELD_LABELS.get(field, field)
        lines.append(f"- **{label}** is missing or empty.")

    for field, error in state.get("validation_errors", {}).items():
        label = _FIELD_LABELS.get(field, field)
        lines.append(f"- **{label}**: {error}")

    return {"follow_up_message": "\n".join(lines), "final_report": None}


def normalize_and_parse(state: "AstrologerState") -> dict:
    """Node 4: Parse DOB, birth datetime with timezone, and current datetime."""
    errors: dict = {}

    parsed_dob = state["dob"]  # already validated as YYYY-MM-DD

    # Parse birth time with timezone
    tz_str = (state.get("birth_time_timezone") or "UTC").strip()
    parsed_birth_datetime = None
    try:
        tz = pytz.timezone(tz_str)
        year, month, day = map(int, state["dob"].split("-"))
        h_str, m_str = state["birth_time"].split(":")
        hour, minute = int(h_str), int(m_str)
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            raise ValueError(f"Invalid time values: {hour}:{minute}")
        dt = datetime(year, month, day, hour, minute)
        parsed_birth_datetime = tz.localize(dt).isoformat()
    except pytz.exceptions.UnknownTimeZoneError:
        errors["birth_time_timezone"] = f"Unknown timezone '{tz_str}'. Please use a standard timezone (e.g., 'Asia/Kolkata')."
    except (ValueError, AttributeError) as exc:
        errors["birth_time"] = f"Could not parse birth time '{state.get('birth_time')}': {exc}"

    # Parse current datetime
    parsed_current_datetime = None
    try:
        parsed_current_datetime = datetime.fromisoformat(
            state["current_datetime"].replace("Z", "+00:00")
        ).isoformat()
    except (ValueError, AttributeError) as exc:
        errors["current_datetime"] = f"Could not parse current datetime: {exc}"

    if errors:
        return {"validation_errors": {**state.get("validation_errors", {}), **errors}}

    return {
        "parsed_dob": parsed_dob,
        "parsed_birth_datetime": parsed_birth_datetime,
        "parsed_current_datetime": parsed_current_datetime,
        "validation_errors": {},
    }


def compute_astro(state: "AstrologerState") -> dict:
    """Node 5 (optional): Compute natal chart via kerykeion. Gracefully degrades on failure."""
    try:
        from astro.compute import compute_chart

        birth_dt = datetime.fromisoformat(state["parsed_birth_datetime"])
        location_parts = [p.strip() for p in state["birth_location"].split(",")]
        city = location_parts[0]
        nation = location_parts[-1] if len(location_parts) > 1 else ""

        chart = compute_chart(
            full_name=state["full_name"],
            birth_year=birth_dt.year,
            birth_month=birth_dt.month,
            birth_day=birth_dt.day,
            birth_hour=birth_dt.hour,
            birth_minute=birth_dt.minute,
            city=city,
            nation=nation,
            tz_str=state.get("birth_time_timezone") or "UTC",
        )
        return {"chart_data": chart}
    except Exception:
        return {"chart_data": None}  # report will acknowledge limitation


def generate_report_node(state: "AstrologerState") -> dict:
    """Node 6: Call Claude API to generate the astrological report."""
    from llm.report import generate_report

    report_text = generate_report(state)
    return {"final_report": report_text}
