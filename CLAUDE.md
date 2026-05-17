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

### Two-graph streaming pipeline

`agent/graph.py` exports two compiled graphs:

- **`prepare_graph`** — validation + chart computation only; stops before the LLM call. Used by `app.py` on form submission inside a spinner.
- **`graph`** — full pipeline including `generate_report_node`; used in integration tests.

`app.py` two-stage flow:
1. `prepare_graph.invoke(payload)` in a spinner (~15s, no LLM)
2. Result stored in `st.session_state._prepared_state`
3. On the next render, `st.write_stream(generate_report_stream(prepared))` streams the report live
4. On completion, `st.session_state.report_result` is set, `_prepared_state` cleared, `st.rerun()` called
5. Final render falls into the `elif report_result:` branch — styled dark card with HTML-converted report

The same two-stage pattern applies to synastry (`_synastry_prepared` → `generate_synastry_report_stream`).

### Graph flow

```
START → ingest_inputs → validate_required_fields
          ├─ (missing or errors) → request_follow_up → END
          └─ (ok) → normalize_and_parse
                      ├─ (parse errors) → request_follow_up → END
                      └─ (ok) → compute_astro → [generate_report_node →] END
```

Router functions (`_route_after_validate`, `_route_after_normalize`) use `.get()` not `[]` because `total=False` means keys may be absent.

### State — `agent/state.py`

`AstrologerState` is a `TypedDict` with `total=False`. Key fields:

| Field | Set by | Purpose |
|---|---|---|
| `full_name`, `dob`, `birth_location`, `birth_time`, `birth_time_timezone`, `birth_time_confidence`, `house_system`, `current_location`, `additional_info`, `report_focus`, `current_datetime` | `app.py` form | Raw user inputs |
| `missing_fields`, `validation_errors` | `validate_required_fields` node | Validation state; reset to `[]`/`{}` by `ingest_inputs` each run |
| `parsed_dob`, `parsed_birth_datetime`, `parsed_current_datetime` | `normalize_and_parse` node | ISO 8601 strings with tz offset |
| `chart_data` | `compute_astro` node | Full dict of all computed astrological data |
| `follow_up_message` | `request_follow_up` node | Shown when validation fails |
| `final_report` | `generate_report_node` | Complete report text (not used in streaming path) |

### Validation — `agent/validators.py`

Pure functions, no side effects. Vague birth-time detection uses `re.search(rf"\b{term}\b")` (whole-word) to avoid false positives (e.g. "midnight" rejected because it contains "night").

### Chart computation — `astro/compute.py`

Wraps kerykeion's `AstrologicalSubject` with `online=True` (requires internet for GeoNames geocoding). Geocoding results are SQLite-cached by kerykeion in `cache/` at the project root.

Key functions:
- `compute_chart(...)` — main natal chart; accepts `house_system` ("Placidus"/"Whole Sign"/"Koch"), maps to kerykeion's `houses_system_identifier` ("P"/"W"/"K"). Returns a plain dict.
- `generate_chart_svg(...)` / `generate_transit_svg(...)` — SVG wheel rendering via `KerykeionChartSVG`; both also accept `house_system`.
- Planet attributes are accessed via `_safe_planet()` because kerykeion attribute names vary across versions.
- Major asteroids (Ceres, Pallas, Juno, Vesta) are computed via pyswisseph with `swe.set_ephe_path()` pointing to kerykeion's bundled `sweph/` directory. Body IDs: Ceres=17, Pallas=18, Juno=19, Vesta=20.
- `_HOUSE_SYSTEM_CODES` maps display names to kerykeion single-letter codes.
- All sub-computations (`compute_transits`, `compute_progressions`, `compute_solar_return`, etc.) are wrapped in individual `try/except` blocks inside `compute_astro` node so a single failure degrades gracefully.

### LLM — `llm/report.py`

Uses the OpenAI Python SDK (`gpt-4o`). Key functions:

| Function | Description |
|---|---|
| `build_prompt(state)` | Builds the full natal reading prompt from all chart data |
| `generate_report(state)` | Blocking report generation (used in integration tests) |
| `generate_report_stream(state)` | Generator yielding text chunks; used with `st.write_stream()` |
| `generate_synastry_report(...)` | Blocking synastry report |
| `generate_synastry_report_stream(...)` | Streaming synastry report |
| `answer_followup_stream(state, history, question)` | Streaming follow-up for natal chart questions |
| `answer_synastry_followup_stream(...)` | Streaming follow-up for synastry questions |

`_REPORT_SYSTEM` and `_SYNASTRY_SYSTEM` are module-level constants shared by blocking and streaming variants of each report type.

### Streamlit UI — `app.py`

Session state keys:

| Key | Purpose |
|---|---|
| `report_result` | Final state dict with `final_report` added; persists styled render |
| `chat_history` | List of `{"role", "content"}` dicts for natal follow-up chat |
| `validation_message` | String shown when graph returns a follow-up; `"__error__"` for unexpected failures |
| `_prepared_state` | Intermediate state after `prepare_graph` completes, before streaming |
| `_stream_error` | Error message if streaming fails; enables Retry button |
| `synastry_result` | Synastry result dict including `"report"` |
| `synastry_chat_history` | Follow-up chat for synastry tab |
| `synastry_error` | Error from synastry chart computation |
| `_synastry_prepared` | Intermediate synastry state (charts computed, report not yet streamed) |

The sidebar shows a "Chart at a Glance" summary (Sun ☉, Moon ☽, ASC ↑) above the form when `report_result` is set.

A house system mismatch warning appears in the natal tab when the sidebar selectbox value differs from `report_result["house_system"]`.

## Key Conventions

- `birth_location` and `current_location` are free-text strings in `"City, Region, Country"` format. `compute_astro` splits on commas: `city = parts[0]`, `nation = parts[-1]`.
- `birth_time` is always `"HH:MM"` (24-hour). The `time_input` widget enforces this; validators reject natural-language strings.
- `current_datetime` is always ISO 8601 with a timezone offset — set by `app.py` via `datetime.now(pytz.UTC).isoformat()`.
- `OPENAI_API_KEY` is loaded from `.env` via `python-dotenv`. The key is read at call time inside each function, not at module import.
- kerykeion stores sign names as 3-letter abbreviations ("Vir", "Can") in some attributes. `_SIGN_ABBREV` in `compute.py` maps these to 0-based indices alongside the full `_SIGNS` list.
- Streaming generators use the OpenAI context-manager form (`with client.chat.completions.create(..., stream=True) as stream`) and yield only non-None content chunks.
