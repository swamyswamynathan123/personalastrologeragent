# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

All commands assume the virtualenv is activated (`venv\Scripts\activate` on Windows, `source venv/bin/activate` on macOS/Linux).

```bash
# Run the app
streamlit run app.py

# Run all unit tests (excludes integration tests that require API + internet)
pytest tests/ -v -k "not integration"

# Run a single test file
pytest tests/test_validators.py -v

# Run a single test by name
pytest tests/test_nodes.py::test_normalize_parses_valid_state -v

# Run integration tests (requires OPENAI_API_KEY and internet for kerykeion geocoding)
pytest tests/ -v -m integration
```

## Architecture

The app is a LangGraph `StateGraph` invoked synchronously from a Streamlit form. There is no async code.

**State** — `agent/state.py` defines `AstrologerState` (a `TypedDict` with `total=False`), the single source of truth passed through every node. All nodes return partial dicts; LangGraph merges them.

**Graph flow** — `agent/graph.py`:
```
START → ingest_inputs → validate_required_fields
          ├─ (missing or errors) → request_follow_up → END
          └─ (ok) → normalize_and_parse
                      ├─ (parse errors) → request_follow_up → END
                      └─ (ok) → compute_astro → generate_report_node → END
```
Router functions (`_route_after_validate`, `_route_after_normalize`) use `.get()` not `[]` because `total=False` means keys may be absent.

**Nodes** — `agent/nodes.py`. `compute_astro` swallows all exceptions and returns `{"chart_data": None}` so a geocoding or network failure degrades gracefully instead of crashing. The report prompt in `llm/report.py` handles the `None` case by instructing GPT-4o to work from Sun sign only.

**Validation** — `agent/validators.py` is pure functions with no side effects. Vague birth-time detection uses `re.search(rf"\b{term}\b")` (whole-word) to avoid false positives like "midnight" being rejected because it contains "night".

**Chart computation** — `astro/compute.py` wraps kerykeion's `AstrologicalSubject` with `online=True` (requires internet for GeoNames geocoding). It stores a SQLite geocoding cache in `cache/` at the project root. Planet attributes are accessed defensively via `_safe_planet()` because kerykeion attribute names can vary across versions.

**LLM** — `llm/report.py` uses the OpenAI Python SDK (`gpt-4o`). `generate_report()` builds the initial reading; `answer_followup()` sends the original report as an `assistant` message first so the model has full prior context when answering follow-up questions.

**Streamlit UI** — `app.py` uses `st.session_state` to persist `report_result`, `chat_history`, and `validation_message` across reruns. The graph is called only on form submission; chat answers call `answer_followup()` directly without re-running the graph.

## Key Conventions

- `birth_location` and `current_location` are free-text strings in `"City, Region, Country"` format. `compute_astro` splits on commas to extract `city` (first element) and `nation` (last element) for kerykeion.
- `birth_time` is always `"HH:MM"` (24-hour). The Streamlit `time_input` widget enforces this; validators reject natural-language strings.
- `current_datetime` is always ISO 8601 with a timezone offset — set by `app.py` via `datetime.now(pytz.UTC).isoformat()` and rejected by `validate_current_datetime` if naive.
- `OPENAI_API_KEY` is loaded from `.env` via `python-dotenv`. The key is read at call time inside each function, not at module import.
