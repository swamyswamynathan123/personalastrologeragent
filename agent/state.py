from typing import TypedDict, Optional, List, Dict, Any


class AstrologerState(TypedDict, total=False):
    # --- Raw inputs (from Streamlit payload) ---
    full_name: Optional[str]
    dob: Optional[str]                      # expected YYYY-MM-DD
    birth_location: Optional[str]           # "City, Region, Country"
    birth_time: Optional[str]               # "HH:MM" (24-hour)
    birth_time_timezone: Optional[str]      # pytz timezone string, e.g. "Asia/Kolkata"
    birth_time_confidence: Optional[str]    # "exact", "approximate", or "unknown"
    current_location: Optional[str]         # "City, Region, Country"
    additional_info: Optional[str]
    report_focus: Optional[str]
    current_datetime: Optional[str]         # ISO 8601 with timezone, set by Streamlit app

    # --- Validation tracking ---
    missing_fields: List[str]
    validation_errors: Dict[str, str]       # field -> error message

    # --- Parsed / normalized values ---
    parsed_dob: Optional[str]               # YYYY-MM-DD after validation
    parsed_birth_datetime: Optional[str]    # ISO 8601 with tz offset
    parsed_current_datetime: Optional[str]  # ISO 8601 with tz offset

    # --- Computed astrology data ---
    chart_data: Optional[Dict[str, Any]]

    # --- Output ---
    follow_up_message: Optional[str]
    final_report: Optional[str]
