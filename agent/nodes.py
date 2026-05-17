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
        "birth_time_confidence": state.get("birth_time_confidence"),
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
        from astro.compute import (
            compute_chart, compute_aspects, compute_transits,
            compute_progressions, compute_progressed_aspects,
            compute_aspect_patterns, compute_profection,
            compute_solar_arcs, compute_solar_arc_aspects,
            compute_solar_return, compute_firdaria,
            compute_vedic,
            compute_upcoming_transits,
            compute_eclipse_sensitivity,
            compute_retrograde_stations,
            compute_transit_to_progressed,
            compute_primary_directions,
            compute_lunar_return,
            compute_transit_passes,
            generate_chart_svg, generate_transit_svg,
        )

        birth_dt = datetime.fromisoformat(state["parsed_birth_datetime"])
        location_parts = [p.strip() for p in state["birth_location"].split(",")]
        city = location_parts[0]
        nation = location_parts[-1] if len(location_parts) > 1 else ""
        house_system = state.get("house_system") or "Placidus"

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
            house_system=house_system,
        )

        chart["aspects"] = compute_aspects(chart)
        chart["aspect_patterns"] = compute_aspect_patterns(chart, chart["aspects"])

        try:
            current_dt = datetime.fromisoformat(state["parsed_current_datetime"])
            current_parts = [p.strip() for p in state["current_location"].split(",")]
            current_city = current_parts[0]
            current_nation = current_parts[-1] if len(current_parts) > 1 else ""
            chart["transits"] = compute_transits(
                natal_chart=chart,
                year=current_dt.year,
                month=current_dt.month,
                day=current_dt.day,
                hour=current_dt.hour,
                minute=current_dt.minute,
                city=current_city,
                nation=current_nation,
                tz_str="UTC",
            )
        except Exception:
            chart["transits"] = []

        try:
            current_dt = datetime.fromisoformat(state["parsed_current_datetime"])
            current_parts = [p.strip() for p in state["current_location"].split(",")]
            chart["upcoming_transits"] = compute_upcoming_transits(
                natal_chart=chart,
                current_year=current_dt.year, current_month=current_dt.month,
                current_day=current_dt.day, current_hour=current_dt.hour,
                current_minute=current_dt.minute,
                current_city=current_parts[0],
                current_nation=current_parts[-1] if len(current_parts) > 1 else "",
            )
        except Exception:
            chart["upcoming_transits"] = []

        try:
            current_dt = datetime.fromisoformat(state["parsed_current_datetime"])
            chart["progressions"] = compute_progressions(
                birth_year=birth_dt.year,
                birth_month=birth_dt.month,
                birth_day=birth_dt.day,
                birth_hour=birth_dt.hour,
                birth_minute=birth_dt.minute,
                current_year=current_dt.year,
                current_month=current_dt.month,
                current_day=current_dt.day,
                city=city,
                nation=nation,
                tz_str=state.get("birth_time_timezone") or "UTC",
            )
        except Exception:
            chart["progressions"] = None

        try:
            if chart.get("progressions"):
                chart["progressed_aspects"] = compute_progressed_aspects(chart, chart["progressions"])
            else:
                chart["progressed_aspects"] = []
        except Exception:
            chart["progressed_aspects"] = []

        try:
            if chart.get("progressions"):
                chart["solar_arcs"] = compute_solar_arcs(chart, chart["progressions"])
                chart["solar_arc_aspects"] = compute_solar_arc_aspects(chart, chart["solar_arcs"])
            else:
                chart["solar_arcs"] = {}
                chart["solar_arc_aspects"] = []
        except Exception:
            chart["solar_arcs"] = {}
            chart["solar_arc_aspects"] = []

        try:
            current_dt = datetime.fromisoformat(state["parsed_current_datetime"])
            current_parts = [p.strip() for p in state["current_location"].split(",")]
            chart["solar_return"] = compute_solar_return(
                natal_chart=chart,
                birth_month=birth_dt.month, birth_day=birth_dt.day,
                current_year=current_dt.year, current_month=current_dt.month, current_day=current_dt.day,
                natal_city=city, natal_nation=nation, tz_str=state.get("birth_time_timezone") or "UTC",
                current_city=current_parts[0],
                current_nation=current_parts[-1] if len(current_parts) > 1 else "",
            )
        except Exception:
            chart["solar_return"] = {}

        try:
            current_dt = datetime.fromisoformat(state["parsed_current_datetime"])
            chart["profection"] = compute_profection(
                birth_year=birth_dt.year, birth_month=birth_dt.month, birth_day=birth_dt.day,
                current_year=current_dt.year, current_month=current_dt.month, current_day=current_dt.day,
                chart=chart,
            )
        except Exception:
            chart["profection"] = None

        try:
            current_dt = datetime.fromisoformat(state["parsed_current_datetime"])
            chart["vedic"] = compute_vedic(
                chart,
                birth_year=birth_dt.year, birth_month=birth_dt.month, birth_day=birth_dt.day,
                current_year=current_dt.year, current_month=current_dt.month, current_day=current_dt.day,
            )
        except Exception:
            chart["vedic"] = None

        try:
            current_dt = datetime.fromisoformat(state["parsed_current_datetime"])
            is_day = (chart.get("sect") or {}).get("chart_type") == "day"
            chart["firdaria"] = compute_firdaria(
                birth_year=birth_dt.year, birth_month=birth_dt.month, birth_day=birth_dt.day,
                current_year=current_dt.year, current_month=current_dt.month, current_day=current_dt.day,
                is_day_chart=is_day,
            )
        except Exception:
            chart["firdaria"] = None

        try:
            current_dt = datetime.fromisoformat(state["parsed_current_datetime"])
            chart["eclipse_sensitivity"] = compute_eclipse_sensitivity(
                chart=chart,
                current_year=current_dt.year,
                current_month=current_dt.month,
                current_day=current_dt.day,
                current_hour=current_dt.hour,
                current_minute=current_dt.minute,
            )
        except Exception:
            chart["eclipse_sensitivity"] = []

        try:
            current_dt = datetime.fromisoformat(state["parsed_current_datetime"])
            chart["retrograde_stations"] = compute_retrograde_stations(
                chart=chart,
                current_year=current_dt.year,
                current_month=current_dt.month,
                current_day=current_dt.day,
                current_hour=current_dt.hour,
                current_minute=current_dt.minute,
            )
        except Exception:
            chart["retrograde_stations"] = []

        try:
            if chart.get("progressions"):
                current_dt = datetime.fromisoformat(state["parsed_current_datetime"])
                current_parts = [p.strip() for p in state["current_location"].split(",")]
                chart["transit_to_progressed"] = compute_transit_to_progressed(
                    natal_chart=chart,
                    progressions=chart["progressions"],
                    year=current_dt.year, month=current_dt.month, day=current_dt.day,
                    hour=current_dt.hour, minute=current_dt.minute,
                    city=current_parts[0],
                    nation=current_parts[-1] if len(current_parts) > 1 else "",
                    tz_str="UTC",
                )
            else:
                chart["transit_to_progressed"] = []
        except Exception:
            chart["transit_to_progressed"] = []

        try:
            chart["chart_svg"] = generate_chart_svg(
                full_name=state["full_name"],
                birth_year=birth_dt.year, birth_month=birth_dt.month, birth_day=birth_dt.day,
                birth_hour=birth_dt.hour, birth_minute=birth_dt.minute,
                city=city, nation=nation,
                tz_str=state.get("birth_time_timezone") or "UTC",
                house_system=house_system,
                lat=chart.get("_natal_lat"),
                lng=chart.get("_natal_lng"),
            )
        except Exception:
            chart["chart_svg"] = ""

        try:
            current_dt = datetime.fromisoformat(state["parsed_current_datetime"])
            current_parts = [p.strip() for p in state["current_location"].split(",")]
            chart["transit_svg"] = generate_transit_svg(
                full_name=state["full_name"],
                birth_year=birth_dt.year, birth_month=birth_dt.month, birth_day=birth_dt.day,
                birth_hour=birth_dt.hour, birth_minute=birth_dt.minute,
                city=city, nation=nation,
                tz_str=state.get("birth_time_timezone") or "UTC",
                transit_year=current_dt.year, transit_month=current_dt.month, transit_day=current_dt.day,
                transit_hour=current_dt.hour, transit_minute=current_dt.minute,
                transit_city=current_parts[0],
                transit_nation=current_parts[-1] if len(current_parts) > 1 else "",
                house_system=house_system,
                natal_lat=chart.get("_natal_lat"),
                natal_lng=chart.get("_natal_lng"),
                transit_lat=chart.get("_current_lat"),
                transit_lng=chart.get("_current_lng"),
            )
        except Exception:
            chart["transit_svg"] = ""

        try:
            chart["primary_directions"] = compute_primary_directions(
                natal_chart=chart,
                birth_year=birth_dt.year, birth_month=birth_dt.month, birth_day=birth_dt.day,
                birth_hour=birth_dt.hour, birth_minute=birth_dt.minute,
                current_year=current_dt.year, current_month=current_dt.month,
                current_day=current_dt.day,
                tz_str=state.get("birth_time_timezone") or "UTC",
            )
        except Exception:
            chart["primary_directions"] = []

        try:
            current_dt = datetime.fromisoformat(state["parsed_current_datetime"])
            current_parts = [p.strip() for p in state["current_location"].split(",")]
            chart["lunar_return"] = compute_lunar_return(
                natal_chart=chart,
                current_year=current_dt.year, current_month=current_dt.month,
                current_day=current_dt.day, current_hour=current_dt.hour,
                current_minute=current_dt.minute,
                city=current_parts[0],
                nation=current_parts[-1] if len(current_parts) > 1 else "",
            )
        except Exception:
            chart["lunar_return"] = {}

        try:
            current_dt = datetime.fromisoformat(state["parsed_current_datetime"])
            chart["transit_passes"] = compute_transit_passes(
                natal_chart=chart,
                current_year=current_dt.year, current_month=current_dt.month,
                current_day=current_dt.day, current_hour=current_dt.hour,
                current_minute=current_dt.minute,
            )
        except Exception:
            chart["transit_passes"] = []

        return {"chart_data": chart}
    except Exception:
        return {"chart_data": None}  # report will acknowledge limitation


def generate_report_node(state: "AstrologerState") -> dict:
    """Node 6: Call Claude API to generate the astrological report."""
    from llm.report import generate_report

    report_text = generate_report(state)
    return {"final_report": report_text}
