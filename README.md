# Personal Astrologer Agent

A stateful astrological reading app powered by LangGraph, OpenAI GPT-4o, and Streamlit. Enter your birth details to receive a personalized natal chart interpretation, then ask follow-up questions in a chat interface.

## Features

- Validates birth details and prompts for corrections when data is missing or malformed
- Computes a full Western natal chart (Sun through Pluto, Ascendant, Midheaven) via kerykeion
- Generates a structured astrological report with GPT-4o
- Follow-up chat lets you ask questions about your chart after the reading

## Architecture

```
Streamlit Form
      │
      ▼
LangGraph StateGraph
  ├── IngestInputs
  ├── ValidateRequiredFields
  │       ├── (issues) ──► RequestFollowUp ──► END
  │       └── (ok)
  ├── NormalizeAndParse
  │       ├── (issues) ──► RequestFollowUp ──► END
  │       └── (ok)
  ├── ComputeAstro (kerykeion)
  └── GenerateReport (GPT-4o) ──► END
```

## Requirements

- Python 3.11+
- An OpenAI API key

## Setup

1. Clone the repository and create a virtual environment:

   ```bash
   python -m venv venv
   ```

2. Install dependencies:

   ```bash
   venv\Scripts\pip install -r requirements.txt   # Windows
   # or
   venv/bin/pip install -r requirements.txt        # macOS/Linux
   ```

3. Copy `.env.example` to `.env` and add your OpenAI API key:

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

The app opens at `http://localhost:8501`.

## Running Tests

```bash
venv\Scripts\pytest tests/ -v -k "not integration"
```

Integration tests (require API key + internet access):

```bash
venv\Scripts\pytest tests/ -v -m integration
```

## Project Structure

```
├── agent/
│   ├── graph.py        # LangGraph StateGraph definition
│   ├── nodes.py        # Node functions (ingest, validate, normalize, compute, generate)
│   ├── state.py        # AstrologerState TypedDict
│   └── validators.py   # Pure validation functions
├── astro/
│   └── compute.py      # kerykeion natal chart wrapper
├── llm/
│   └── report.py       # GPT-4o report generation and follow-up chat
├── tests/
│   ├── test_validators.py
│   ├── test_nodes.py
│   └── test_graph.py
├── app.py              # Streamlit UI
├── run.bat             # Windows launcher
└── requirements.txt
```

## Tech Stack

| Component | Library |
|---|---|
| Workflow orchestration | LangGraph |
| Natal chart computation | kerykeion |
| LLM | OpenAI GPT-4o |
| UI | Streamlit |
| Timezone handling | pytz |
