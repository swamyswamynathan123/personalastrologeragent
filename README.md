# Personal Astrologer Agent

A full-featured astrological reading app powered by LangGraph, OpenAI GPT-4o, and Streamlit. Enter your birth details to receive a personalized, multi-technique reading with live streaming output, then ask follow-up questions in a chat interface.

## Features

**Natal Reading**
- Validates all birth inputs and prompts for corrections when data is missing or malformed
- Computes a comprehensive natal chart via kerykeion + swisseph
- Streams the GPT-4o report token-by-token for immediate feedback
- Follow-up chat retains full chart context across multiple questions
- Export report as Markdown or HTML (with embedded SVG chart wheel)

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
| Vedic overlay | Sidereal positions (Lahiri), nakshatra, Vimshottari dasha, yogas |
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

`app.py` uses `prepare_graph` on form submission (spinner, ~15s), then streams the report via `generate_report_stream()` with `st.write_stream()`. After streaming completes, `st.rerun()` re-renders the page in the styled cached branch.

## Requirements

- Python 3.11+
- An OpenAI API key
- Internet access (kerykeion uses GeoNames for geocoding)

## Setup

1. Clone the repository and create a virtual environment:

   ```bash
   python -m venv venv
   ```

2. Activate the virtualenv and install dependencies:

   ```bash
   venv\Scripts\activate        # Windows
   source venv/bin/activate     # macOS/Linux

   pip install -r requirements.txt
   ```

3. Copy `.env.example` to `.env` and add your key:

   ```
   OPENAI_API_KEY=sk-...
   ```

## Running the App

**Windows:**
```bat
run.bat
```

**macOS/Linux:**
```bash
source venv/bin/activate
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
│   └── report.py       # Prompt building, streaming/blocking report and synastry generation
├── tests/
│   ├── test_validators.py
│   ├── test_nodes.py
│   └── test_graph.py
├── app.py              # Streamlit UI (sidebar form, natal tab, synastry tab)
├── run.bat             # Windows launcher
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
| Timezone handling | pytz |
| Markdown → HTML export | markdown |
