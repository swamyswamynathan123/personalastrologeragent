# Personal Astrologer Agent

A full-featured astrological reading app powered by LangGraph, OpenAI GPT-4o, and Streamlit. Enter your birth details to receive a personalized, multi-technique reading with live streaming output, then ask follow-up questions in a chat interface.

## Features

**Natal Reading**
- Validates all birth inputs and prompts for corrections when data is missing or malformed
- Computes a comprehensive natal chart via kerykeion + swisseph
- Streams the GPT-4o report live in 3 focused parts (identity & soul → cosmic timing → advanced windows & Vedic)
- Follow-up chat retains full chart context across multiple questions
- Export report as Markdown, HTML (with embedded SVG chart wheel), or PDF
- Report is cached in SQLite so reloads are instant

**Sidebar — Daily Digest**
- **Chart at a Glance** — Sun, Moon, ASC signs shown above the form once a reading exists
- **Today's Sky** — live Moon sign/degree, void-of-course status, closest outer-planet transit, retrograde planets
- **Daily Digest** — AI-generated 2–3 sentence personalised paragraph synthesising the day's sky for this specific chart; cached daily, refreshable on demand

**Chart Wheels (4 tabs)**
| Tab | Description |
|---|---|
| Natal Chart | Western tropical wheel with house cusps (Placidus / Whole Sign / Koch) |
| Kundali | North Indian Lagna chart using sidereal Lahiri positions; full planet names, retrograde marked (R) |
| Transit Overlay | Current sky overlaid on the natal wheel |
| Vedic Chart | Sidereal wheel via kerykeion |

**Vimshottari Dasha** (inside Vedic chart tab)
- Current Mahadasha and Antardasha with progress bars and end dates
- Birth Moon nakshatra identification
- Full 120-year mahadasha timeline table

**Transit Calendar** (collapsible, next 35 days)
- Exact aspect dates between transiting planets (Sun–Saturn) and natal positions
- Colour-coded: green = trine/sextile, red = square/opposition, blue = conjunction
- Computed live from today's date — always current

**Transit Timeline**
- Gantt-style chart showing when each outer planet forms a major aspect to a natal point over the next 12 months
- Hover a bar for exact dates and orb

**Forecasts**
- Four AI-generated forward-looking reports: Weekly (7 days), Monthly (30 days), Yearly (12 months), Overall (2–3 years)
- Each forecast streams live from the current transit and timing state

**Synastry / Compatibility**
- Computes inter-chart aspects, house overlays, and composite chart for two people
- Streams the compatibility reading live
- Follow-up chat for synastry questions

**Chart Techniques**
| Technique | Detail |
|---|---|
| Natal planets | Sun–Pluto + Chiron, ASC, MC, house placements, dignity, retrograde |
| Major asteroids | Ceres, Pallas, Juno, Vesta (via swisseph) |
| Lunar nodes | Mean North/South Node |
| House cusps | All 12, with rulers and their natal condition |
| Natal aspects | Conjunction, Sextile, Square, Trine, Opposition with applying/separating |
| Aspect patterns | Grand Trine, T-Square, Yod, Grand Cross, Kite, Stellium |
| Current transits | Outer and inner planets to natal chart (3° orb) |
| Upcoming transits | Outer planets only, next 90 days with exact dates |
| Secondary progressions | Progressed Sun, Moon, inner planets, ASC, MC |
| Solar arc directions | Arc positions + aspects to natal chart |
| Solar return | Annual return chart with angular planets and highlighted houses |
| Annual profection | Age-based house activation and lord of the year |
| Firdaria | Persian time lords — major and sub-period |
| Vimshottari Dasha | Moon nakshatra → Mahadasha / Antardasha with progress bars and full timeline |
| Vedic overlay | Sidereal positions (Lahiri), nakshatra, yogas, navamsha |
| Elemental/modal balance | Fire/Earth/Air/Water, Cardinal/Fixed/Mutable counts |
| Planetary sect | Day/night chart, in-sect vs. out-of-sect planets |
| Lunar phase | Natal Moon phase archetype |
| Part of Fortune & Spirit | Arabic lots (day/night formula) |
| Fixed stars | Conjunctions within 1° orb to planets and angles |
| Antiscia | Solstice-point connections (antiscia + contra-antiscia) |
| Mutual receptions | Planets in each other's signs |
| Anaretic degrees | Planets at 29° |
| House system | Placidus, Whole Sign, or Koch (user-selectable) |

## Architecture

Two compiled LangGraph graphs handle different phases:

```
prepare_graph (fast — no LLM):
  START → ingest_inputs → validate_required_fields
            ├─ (issues) → request_follow_up → END
            └─ (ok) → normalize_and_parse
                        ├─ (issues) → request_follow_up → END
                        └─ (ok) → compute_astro → END

graph (full pipeline — used in tests):
  ... same as above, then → generate_report_node → END
```

`app.py` uses `prepare_graph` on form submission (spinner, ~15–25s), then streams the report via `generate_report_stream()` with `st.write_stream()`. The stream makes **3 sequential GPT-4o calls** — Part 1 (identity & soul, ~10–15s), Part 2 (cosmic timing, ~10–15s), Part 3 (advanced windows & Vedic, ~10–15s) — yielding tokens live between each call. After streaming completes, `st.rerun()` re-renders the page in the styled cached branch.

## Requirements

- Python 3.11+
- An OpenAI API key
- Internet access (kerykeion uses GeoNames for geocoding)

## Setup

1. Clone the repository.

2. Copy `.env.example` to `.env` and add your key:

   ```
   OPENAI_API_KEY=sk-...
   ```

3. Run the app — the launcher handles everything else automatically.

## Running the App

**Windows (recommended):**
```bat
run.bat
```
`run.bat` auto-creates the virtual environment and installs dependencies on first run, then launches Streamlit. Subsequent runs skip setup and start immediately.

**macOS/Linux:**
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Opens at `http://localhost:8501`.

## Running Tests

```bash
# Unit tests (no API key or internet required)
pytest tests/ -v -k "not integration"

# Integration tests (requires OPENAI_API_KEY + internet)
pytest tests/ -v -m integration
```

## Project Structure

```
├── agent/
│   ├── graph.py        # Two compiled StateGraphs: graph + prepare_graph
│   ├── nodes.py        # Node functions (ingest, validate, normalize, compute, generate)
│   ├── state.py        # AstrologerState TypedDict
│   └── validators.py   # Pure validation functions
├── astro/
│   └── compute.py      # kerykeion + swisseph chart computation (all techniques)
├── llm/
│   └── report.py       # 3-call streaming pipeline, prompt builders, synastry, follow-up, daily digest
├── export/
│   └── pdf.py          # PDF export with embedded SVG wheels via reportlab + svglib
├── tests/
│   ├── test_validators.py
│   ├── test_nodes.py
│   ├── test_graph.py
│   └── test_pipeline.py  # LLM streaming pipeline tests
├── cache/              # SQLite report cache + kerykeion geocoding cache (auto-created)
├── storage/            # Saved charts and readings (auto-created)
├── app.py              # Streamlit UI — sidebar, natal, synastry, forecasts, transit calendar tabs
├── run.bat             # Windows launcher — auto-creates venv and installs deps on first run
├── USERS.md            # End-user documentation
└── requirements.txt
```

## Tech Stack

| Component | Library |
|---|---|
| Workflow orchestration | LangGraph |
| Natal chart computation | kerykeion |
| Asteroid / ephemeris data | pyswisseph |
| LLM | OpenAI GPT-4o |
| UI | Streamlit |
| Transit timeline chart | Plotly |
| PDF export | reportlab + svglib |
| Timezone handling | pytz |
| Markdown → HTML export | markdown |

## Documentation

See [USERS.md](USERS.md) for the full end-user guide covering birth details, house systems, reading sections, saved charts, the transit calendar, compatibility, forecasts, follow-up chat, and a glossary.
