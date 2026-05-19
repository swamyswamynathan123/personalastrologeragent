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
1. `prepare_graph.invoke(payload)` in a spinner (~15–25s, no LLM)
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

| Function | Description |
|---|---|
| `compute_chart(...)` | Main natal chart; accepts `house_system` ("Placidus"/"Whole Sign"/"Koch"). Returns plain dict. |
| `generate_chart_svg(...)` | Western natal wheel via `KerykeionChartSVG`; accepts `house_system`. |
| `generate_transit_svg(...)` | Transit overlay wheel; accepts `house_system`. |
| `generate_vedic_chart_svg(...)` | Vedic (sidereal) wheel via kerykeion. |
| `generate_kundali_svg(chart_data, full_name)` | North Indian Kundali (Lagna) chart SVG. Uses `chart_data["vedic"]["sidereal"]` positions computed by `compute_vedic()`. No API call required. |
| `compute_vimshottari_dasha(chart_data, birth_datetime)` | Computes Vimshottari Mahadasha / Antardasha periods from Moon's sidereal nakshatra. Returns a dict with `mahadashas`, `current_mahadasha`, `antardashas`, `current_antardasha`, `nakshatra`, `birth_lord`. Uses `_DASHA_ORDER`, `_DASHA_YEARS`, `_NAK_LORDS` constants. |
| `compute_transit_calendar(chart_data, from_date, days=35)` | Scans the next N days using pyswisseph for exact transit aspects (local-minimum-orb dates) to natal positions. Returns list of `{date, transit_planet, natal_planet, aspect, orb}` dicts. Tracks Sun through Saturn vs all natal planets + ASC + MC. |
| `compute_daily_sky(natal_chart, year, month, day, ...)` | Returns today's sky snapshot: Moon sign/degree/VOC, retrograde planets, closest outer-planet transit summary. Used for the sidebar "Today's Sky" section. |

Other notes:
- Planet attributes are accessed via `_safe_planet()` because kerykeion attribute names vary across versions.
- Major asteroids (Ceres, Pallas, Juno, Vesta) are computed via pyswisseph with `swe.set_ephe_path()`. Body IDs: Ceres=17, Pallas=18, Juno=19, Vesta=20.
- `_HOUSE_SYSTEM_CODES` maps display names to kerykeion single-letter codes.
- All sub-computations are wrapped in individual `try/except` blocks inside `compute_astro` so a single failure degrades gracefully.
- `_DASHA_ORDER` = `["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]`. `_NAK_LORDS[i] = _DASHA_ORDER[i % 9]` gives the ruling planet for each of the 27 nakshatras (Ashwini = Ketu).

### LLM — `llm/report.py`

Uses the OpenAI Python SDK (`gpt-4o`). Key functions:

| Function | Description |
|---|---|
| `_person_header(state)` | Helper returning the person-details block shared across all 3 prompts |
| `_build_identity_prompt(state)` | Sections 1–3 (Personal Overview, Life Direction, Current Phase) — natal data + progressions |
| `_build_timing_prompt(state)` | Sections 4–7 (Cosmic Climate, Key Themes, Practical Guidance, Favorable Timing) — transits, firdaria, profection, solar arcs |
| `_build_advanced_prompt(state)` | Sections 8–10 (Top 5 Windows table, Vedic Full Reading, optional Focus Deep Dive) |
| `generate_report(state)` | Blocking report generation (used in integration tests); single call |
| `generate_report_stream(state)` | Generator making **3 sequential streaming API calls** (identity → timing → advanced), yielding text chunks live; checks cache before calling; writes to cache on completion |
| `generate_synastry_report(...)` | Blocking synastry report |
| `generate_synastry_report_stream(...)` | Streaming synastry report (single call) |
| `answer_followup_stream(state, history, question)` | Streaming follow-up for natal chart questions |
| `answer_synastry_followup_stream(...)` | Streaming follow-up for synastry questions |
| `generate_daily_digest(full_name, sun_sign, moon_sign, asc_sign, today_date, sky, active_transits, dasha)` | Short blocking call (max 160 tokens, temperature 0.82) producing a 2–3 sentence personalised daily digest. Synthesises Moon sign/VOC, closest transit, retrograde planets, inner transits, and current dasha period. Used by the sidebar. |

`_REPORT_SYSTEM` and `_SYNASTRY_SYSTEM` are module-level constants shared by blocking and streaming variants of each report type.

**3-call streaming pipeline** — `generate_report_stream` iterates over:
```python
_calls = [
    (_build_identity_prompt(state),  4096, "Sections 1–3"),
    (_build_timing_prompt(state),    4096, "Sections 4–7"),
    (_build_advanced_prompt(state),  4096, "Sections 8–10"),
]
```
Each call uses `with client.chat.completions.create(..., stream=True) as stream` and yields `chunk.choices[0].delta.content` for non-None deltas. A `"---"` separator is yielded between calls. The full concatenated text is written to the SQLite cache on completion.

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
| `_daily_sky` | Dict from `compute_daily_sky`; cached for the day |
| `_daily_sky_date` | ISO date string; used to invalidate `_daily_sky` at midnight |
| `_daily_digest` | AI-generated 2–3 sentence daily digest string; cached for the day |
| `_daily_digest_key` | Cache key: `f"{full_name}\|{parsed_dob}\|{today_date}"` — regenerates when date or person changes |

**UI helper functions** (defined above the sidebar block):

| Function | Purpose |
|---|---|
| `_render_svg(svg)` | Renders SVG string as a responsive base64 image in a dark wrapper |
| `_render_dasha_section(dasha)` | Shows current Mahadasha + Antardasha with progress bars and a full timeline table; rendered inside the Vedic chart tab |
| `_render_transit_calendar(chart_data, from_dt_iso)` | Calls `compute_transit_calendar` live, groups results by date, renders a colour-coded aspect table (green = trine/sextile, red = square/opposition, blue = conjunction) |
| `_birth_data_card(state)` | Birth data summary card shown at the top of the natal reading |

The sidebar shows:
1. **Chart at a Glance** (Sun ☉ / Moon ☽ / ASC ↑) when `report_result` is set
2. **Today's Sky** raw data (Moon sign/VOC, closest outer-planet transit, retrograde planets)
3. **Daily Digest** — AI paragraph below Today's Sky; cached by `_daily_digest_key`; has a `↺` refresh button

Chart tabs order (natal reading): **Natal Chart → Kundali → Transit Overlay → Vedic Chart**

The Vedic Chart tab includes a `_render_dasha_section` block showing the Vimshottari Dasha for the person.

Below the chart tabs: a collapsible **"📅 Transit Calendar — Next 35 Days"** expander calling `_render_transit_calendar` live on every open.

A house system mismatch warning appears in the natal tab when the sidebar selectbox value differs from `report_result["house_system"]`.

## Key Conventions

- `birth_location` and `current_location` are free-text strings in `"City, Region, Country"` format. `compute_astro` splits on commas: `city = parts[0]`, `nation = parts[-1]`.
- `birth_time` is always `"HH:MM"` (24-hour). The `time_input` widget enforces this; validators reject natural-language strings.
- `current_datetime` is always ISO 8601 with a timezone offset — set by `app.py` via `datetime.now(pytz.UTC).isoformat()`.
- `OPENAI_API_KEY` is loaded from `.env` via `python-dotenv`. The key is read at call time inside each function, not at module import.
- kerykeion stores sign names as 3-letter abbreviations ("Vir", "Can") in some attributes. `_SIGN_ABBREV` in `compute.py` maps these to 0-based indices alongside the full `_SIGNS` list.
- Streaming generators use the OpenAI context-manager form (`with client.chat.completions.create(..., stream=True) as stream`) and yield only non-None content chunks.
- `chart_data["vimshottari_dasha"]` is computed by `compute_vimshottari_dasha` inside `compute_astro` node and stored permanently (it is based on birth data, not the current date). `chart_data["kundali_svg"]`, `chart_data["chart_svg"]`, `chart_data["vedic_svg"]` are stripped from the DB on save (`_strip_svgs`) and regenerated on load when `_natal_lat` is available.
- The Transit Calendar (`compute_transit_calendar`) is computed fresh in the UI (not stored), so it always reflects today's date.
