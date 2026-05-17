"""
Tests for event-prediction detection and message building in llm/report.py.

Strategy: pure unit tests — no API calls, no chart computation.
Verifies detection logic, event-type classification, and message structure.
"""
import pytest
from llm.report import (
    _is_event_question,
    _detect_event_type,
    _build_event_prediction_messages,
    _build_synastry_event_messages,
    _EVENT_HOUSE_MAP,
)


# ---------------------------------------------------------------------------
# _is_event_question — detection
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("question", [
    "Will I get the job I interviewed for?",
    "Should I invest in real estate this year?",
    "Is June a good time to launch my business?",
    "When should I get married?",
    "When will I meet someone?",
    "What's the likelihood of a promotion this quarter?",
    "Am I going to move cities soon?",
    "Is this a favorable time to travel abroad?",
    "Good time to start a new project?",
    "Predict my career prospects for the next 6 months",
    "What's the timing for a relationship breakthrough?",
    "Should we commit to each other now?",
])
def test_is_event_question_true(question):
    assert _is_event_question(question) is True


@pytest.mark.parametrize("question", [
    "What does my Saturn placement mean?",
    "Tell me about my Moon in Scorpio",
    "Explain the T-Square in my chart",
    "What is my Ascendant ruler?",
    "How does my Firdaria period affect me?",
    "What does Venus retrograde mean for me?",
    "Which house is my Jupiter in?",
])
def test_is_event_question_false(question):
    assert _is_event_question(question) is False


# ---------------------------------------------------------------------------
# _detect_event_type — classification
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("question,expected", [
    ("Will I get the promotion this year?", "career"),
    ("Should I quit my job?", "career"),
    ("Is this a good time to launch my business?", "career"),
    ("When will I meet my life partner?", "relationship"),
    ("Should we get married this year?", "relationship"),
    ("Will there be a breakup?", "relationship"),
    ("Should I invest in stocks now?", "finance"),
    ("Is this a good time to buy property?", "finance"),
    ("Will my health improve this year?", "health"),
    ("Should I have the surgery now?", "health"),
    ("Is this a good time to travel abroad?", "travel"),
    ("Should I relocate to another city?", "travel"),
    ("Will I get published this year?", "creativity"),
    ("Is this a good time to release my album?", "creativity"),
    ("Will things improve for me soon?", "general"),
    ("When is the right time?", "general"),
])
def test_detect_event_type(question, expected):
    assert _detect_event_type(question) == expected


# ---------------------------------------------------------------------------
# _EVENT_HOUSE_MAP — completeness
# ---------------------------------------------------------------------------

def test_event_house_map_has_all_types():
    expected_types = {"career", "relationship", "finance", "health", "travel", "creativity", "general"}
    assert set(_EVENT_HOUSE_MAP.keys()) == expected_types


def test_event_house_map_entries_have_required_keys():
    for event_type, info in _EVENT_HOUSE_MAP.items():
        assert "houses" in info, f"{event_type} missing 'houses'"
        assert "planets" in info, f"{event_type} missing 'planets'"
        assert info["houses"], f"{event_type} has empty 'houses'"
        assert info["planets"], f"{event_type} has empty 'planets'"


# ---------------------------------------------------------------------------
# _build_event_prediction_messages — message structure
# ---------------------------------------------------------------------------

_BASE_STATE = {
    "full_name": "Jane Doe",
    "parsed_dob": "1990-05-15",
    "birth_location": "Mumbai, Maharashtra, India",
    "birth_time": "14:30",
    "birth_time_timezone": "Asia/Kolkata",
    "current_location": "New York, NY, USA",
    "parsed_current_datetime": "2026-05-15T12:00:00+00:00",
    "final_report": "This is the original report.",
    "chart_data": None,
}


def test_build_event_prediction_messages_returns_list():
    msgs = _build_event_prediction_messages(_BASE_STATE, [], "Will I get the job?")
    assert isinstance(msgs, list)
    assert len(msgs) >= 3  # system + assistant + user


def test_build_event_prediction_messages_roles():
    msgs = _build_event_prediction_messages(_BASE_STATE, [], "Will I get the job?")
    roles = [m["role"] for m in msgs]
    assert roles[0] == "system"
    assert roles[1] == "assistant"
    assert roles[-1] == "user"


def test_build_event_prediction_messages_user_content():
    question = "Will I get the promotion this year?"
    msgs = _build_event_prediction_messages(_BASE_STATE, [], question)
    assert msgs[-1]["content"] == question


def test_build_event_prediction_messages_system_has_verdict_format():
    msgs = _build_event_prediction_messages(_BASE_STATE, [], "Will I get the job?")
    system = msgs[0]["content"]
    assert "VERDICT:" in system
    assert "Best Window:" in system
    assert "Key obstacle:" in system
    assert "Confidence:" in system
    assert "Reading:" in system


def test_build_event_prediction_messages_system_names_event_type():
    msgs = _build_event_prediction_messages(_BASE_STATE, [], "Should I invest now?")
    system = msgs[0]["content"]
    assert "FINANCE" in system


def test_build_event_prediction_messages_system_names_houses():
    msgs = _build_event_prediction_messages(_BASE_STATE, [], "Will I get married this year?")
    system = msgs[0]["content"]
    assert "7th" in system


def test_build_event_prediction_messages_includes_original_report():
    msgs = _build_event_prediction_messages(_BASE_STATE, [], "Will I get the job?")
    assistant_msg = next(m for m in msgs if m["role"] == "assistant")
    assert assistant_msg["content"] == "This is the original report."


def test_build_event_prediction_messages_includes_chat_history():
    history = [
        {"role": "user", "content": "Earlier question"},
        {"role": "assistant", "content": "Earlier answer"},
    ]
    msgs = _build_event_prediction_messages(_BASE_STATE, history, "Will I get the job?")
    contents = [m["content"] for m in msgs]
    assert "Earlier question" in contents
    assert "Earlier answer" in contents


def test_build_event_prediction_messages_no_chart_data_no_crash():
    state = {**_BASE_STATE, "chart_data": None}
    msgs = _build_event_prediction_messages(state, [], "Will I get the job?")
    system = msgs[0]["content"]
    assert "unavailable" in system.lower() or "Jane Doe" in system


def test_build_event_prediction_messages_with_minimal_chart():
    state = {**_BASE_STATE, "chart_data": {
        "sun": {"sign": "Taurus", "position": 24.5, "house": "1", "retrograde": False, "dignity": "neutral"},
        "moon": {"sign": "Scorpio", "position": 12.3, "house": "7", "retrograde": False, "dignity": "detriment"},
        "ascendant": {"sign": "Aries", "position": 5.0},
        "midheaven": {"sign": "Capricorn", "position": 10.0},
        "aspects": [],
        "houses": {},
    }}
    msgs = _build_event_prediction_messages(state, [], "Will I get the job?")
    assert msgs[0]["role"] == "system"
    assert "Taurus" in msgs[0]["content"] or "Jane Doe" in msgs[0]["content"]


def test_build_event_prediction_messages_low_temperature_indicator():
    # Temperature is not in message content but verifying the function doesn't crash
    # and returns well-formed messages for all event types
    for event_type_question in [
        "Will I get the job?",
        "Should I invest now?",
        "When will I meet someone?",
        "Will my health improve?",
        "Is this a good time to travel?",
        "Will I publish my book?",
        "Will things get better?",
    ]:
        msgs = _build_event_prediction_messages(_BASE_STATE, [], event_type_question)
        assert msgs[0]["role"] == "system"
        assert msgs[-1]["content"] == event_type_question


# ---------------------------------------------------------------------------
# _build_synastry_event_messages — structure
# ---------------------------------------------------------------------------

_CHART_A = {"sun": {"sign": "Aries", "position": 15.0, "house": "7", "retrograde": False}}
_CHART_B = {"sun": {"sign": "Libra", "position": 22.0, "house": "1", "retrograde": False}}
_SYNASTRY = {
    "cross_aspects": [],
    "composite": {},
    "composite_aspects": [],
    "overlays_a_in_b": [],
    "overlays_b_in_a": [],
}


def test_build_synastry_event_messages_returns_list():
    msgs = _build_synastry_event_messages(
        "Alice", "1990-03-21", _CHART_A,
        "Bob", "1988-11-15", _CHART_B,
        _SYNASTRY, "Original synastry report.",
        [], "Should we get married this year?",
    )
    assert isinstance(msgs, list)
    assert len(msgs) >= 3


def test_build_synastry_event_messages_system_has_verdict_format():
    msgs = _build_synastry_event_messages(
        "Alice", "1990-03-21", _CHART_A,
        "Bob", "1988-11-15", _CHART_B,
        _SYNASTRY, "Original synastry report.",
        [], "When should we commit?",
    )
    system = msgs[0]["content"]
    assert "VERDICT:" in system
    assert "Best Window:" in system
    assert "7th" in system


def test_build_synastry_event_messages_names_both_people():
    msgs = _build_synastry_event_messages(
        "Alice", "1990-03-21", _CHART_A,
        "Bob", "1988-11-15", _CHART_B,
        _SYNASTRY, "Original synastry report.",
        [], "Will we get engaged soon?",
    )
    system = msgs[0]["content"]
    assert "Alice" in system
    assert "Bob" in system


def test_build_synastry_event_messages_user_content_preserved():
    question = "Should we move in together?"
    msgs = _build_synastry_event_messages(
        "Alice", "1990-03-21", _CHART_A,
        "Bob", "1988-11-15", _CHART_B,
        _SYNASTRY, "Original synastry report.",
        [], question,
    )
    assert msgs[-1]["content"] == question
