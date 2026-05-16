from langgraph.graph import StateGraph, END, START

from agent.state import AstrologerState
from agent.nodes import (
    ingest_inputs,
    validate_required_fields,
    request_follow_up,
    normalize_and_parse,
    compute_astro,
    generate_report_node,
)


def _route_after_validate(state: AstrologerState) -> str:
    if state.get("missing_fields") or state.get("validation_errors"):
        return "request_follow_up"
    return "normalize_and_parse"


def _route_after_normalize(state: AstrologerState) -> str:
    if state.get("validation_errors"):
        return "request_follow_up"
    return "compute_astro"


builder = StateGraph(AstrologerState)

builder.add_node("ingest_inputs", ingest_inputs)
builder.add_node("validate_required_fields", validate_required_fields)
builder.add_node("request_follow_up", request_follow_up)
builder.add_node("normalize_and_parse", normalize_and_parse)
builder.add_node("compute_astro", compute_astro)
builder.add_node("generate_report_node", generate_report_node)

builder.add_edge(START, "ingest_inputs")
builder.add_edge("ingest_inputs", "validate_required_fields")
builder.add_conditional_edges(
    "validate_required_fields",
    _route_after_validate,
    path_map={
        "request_follow_up": "request_follow_up",
        "normalize_and_parse": "normalize_and_parse",
    },
)
builder.add_conditional_edges(
    "normalize_and_parse",
    _route_after_normalize,
    path_map={
        "request_follow_up": "request_follow_up",
        "compute_astro": "compute_astro",
    },
)
builder.add_edge("request_follow_up", END)
builder.add_edge("compute_astro", "generate_report_node")
builder.add_edge("generate_report_node", END)

graph = builder.compile()


# ── Prepare graph (validation + chart only, no LLM call) ─────────────────────
# Used by app.py to stream the report separately via generate_report_stream().
_prep = StateGraph(AstrologerState)
_prep.add_node("ingest_inputs", ingest_inputs)
_prep.add_node("validate_required_fields", validate_required_fields)
_prep.add_node("request_follow_up", request_follow_up)
_prep.add_node("normalize_and_parse", normalize_and_parse)
_prep.add_node("compute_astro", compute_astro)

_prep.add_edge(START, "ingest_inputs")
_prep.add_edge("ingest_inputs", "validate_required_fields")
_prep.add_conditional_edges(
    "validate_required_fields",
    _route_after_validate,
    path_map={
        "request_follow_up": "request_follow_up",
        "normalize_and_parse": "normalize_and_parse",
    },
)
_prep.add_conditional_edges(
    "normalize_and_parse",
    _route_after_normalize,
    path_map={
        "request_follow_up": "request_follow_up",
        "compute_astro": "compute_astro",
    },
)
_prep.add_edge("request_follow_up", END)
_prep.add_edge("compute_astro", END)

prepare_graph = _prep.compile()
