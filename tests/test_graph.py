import pytest
from agent.graph import graph

_VALID_STATE = {
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


def test_graph_follow_up_when_name_missing():
    state = {**_VALID_STATE, "full_name": None}
    result = graph.invoke(state)
    assert result["follow_up_message"] is not None
    assert result["final_report"] is None


def test_graph_follow_up_when_dob_format_wrong():
    state = {**_VALID_STATE, "dob": "15-05-1990"}
    result = graph.invoke(state)
    assert result["follow_up_message"] is not None
    assert result["final_report"] is None


def test_graph_follow_up_when_birth_time_vague():
    state = {**_VALID_STATE, "birth_time": "morning"}
    result = graph.invoke(state)
    assert result["follow_up_message"] is not None


def test_graph_follow_up_when_multiple_fields_missing():
    state = {**_VALID_STATE, "full_name": None, "birth_location": ""}
    result = graph.invoke(state)
    msg = result["follow_up_message"]
    assert "full_name" in msg or "Full Name" in msg
    assert "birth_location" in msg or "Birth Location" in msg


@pytest.mark.integration
def test_graph_produces_report_for_valid_state():
    """Requires ANTHROPIC_API_KEY and internet. Run with: pytest -m integration"""
    result = graph.invoke(_VALID_STATE.copy())
    assert result["final_report"] is not None
    assert len(result["final_report"]) > 100
    assert result["follow_up_message"] is None
