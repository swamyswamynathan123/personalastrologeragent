from __future__ import annotations
from datetime import datetime, date

import pytz
import streamlit as st
from dotenv import load_dotenv

from agent.graph import graph, prepare_graph
from agent.state import AstrologerState
from llm.report import answer_followup_stream, generate_report_stream, generate_synastry_report_stream, answer_synastry_followup_stream, generate_weekly_forecast_stream, generate_monthly_forecast_stream, generate_yearly_forecast_stream, generate_overall_forecast_stream
from astro.compute import compute_chart, compute_synastry, compute_transit_calendar, compute_daily_sky
from cache.report_cache import purge_expired
from storage.db import init_db, save_natal, save_synastry, list_charts, load_chart, delete_chart

load_dotenv()
purge_expired()
init_db()

st.set_page_config(
    page_title="Personal Astrologer Agent",
    page_icon="⭐",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;500;600&family=Lora:ital,wght@0,400;0,600;1,400&family=Raleway:wght@300;400;500;600&display=swap');

/* ── Global typography ───────────────────────────────────────────── */
html, body, [class*="css"] {
    font-family: "Lora", "Georgia", serif;
}

/* ── Page background ─────────────────────────────────────────────── */
.stApp {
    background-color: #08081a;
    background-image:
        radial-gradient(ellipse at 15% 15%, rgba(80,50,140,0.18) 0%, transparent 55%),
        radial-gradient(ellipse at 85% 85%, rgba(40,25,90,0.22) 0%, transparent 55%);
    color: #f0ebe3;
}

/* ── Sidebar ─────────────────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background-color: #0b0b1c;
    border-right: 1px solid #202040;
}
[data-testid="stSidebar"] .stForm { background: transparent; }
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] .stTextInput label,
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stDateInput label,
[data-testid="stSidebar"] .stTimeInput label,
[data-testid="stSidebar"] .stTextArea label {
    color: #aa99cc !important;
    font-family: "Raleway", sans-serif !important;
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.09em;
    text-transform: uppercase;
}
[data-testid="stSidebar"] input,
[data-testid="stSidebar"] select,
[data-testid="stSidebar"] textarea {
    background-color: #10102a !important;
    border: 1px solid #2a2a50 !important;
    color: #f0ebe3 !important;
    border-radius: 6px !important;
    font-family: "Lora", serif !important;
    font-size: 0.88rem !important;
}
[data-testid="stSidebar"] input:focus,
[data-testid="stSidebar"] textarea:focus {
    border-color: #6644aa !important;
    box-shadow: 0 0 0 2px rgba(102,68,170,0.2) !important;
}
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    font-family: "Cinzel", serif !important;
    color: #b898e8 !important;
    letter-spacing: 0.06em;
}
[data-testid="stSidebar"] h4 {
    font-family: "Raleway", sans-serif !important;
    font-size: 0.68rem !important;
    font-weight: 600 !important;
    color: #8877aa !important;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    margin: 1.3rem 0 0.35rem !important;
    padding-bottom: 0.3rem;
    border-bottom: 1px solid #181830;
}
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] li,
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] span {
    color: #d4ccc4 !important;
    font-size: 0.86rem;
}
[data-testid="stSidebar"] small,
[data-testid="stSidebar"] [data-testid="stCaptionContainer"],
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {
    color: #8877aa !important;
    font-family: "Raleway", sans-serif !important;
}

/* ── Help / tooltip icons ────────────────────────────────────────── */
[data-testid="stTooltipIcon"] { opacity: 1 !important; }
[data-testid="stTooltipIcon"] svg circle {
    fill: #5533aa !important;
    stroke: #5533aa !important;
}
[data-testid="stTooltipIcon"] svg path,
[data-testid="stTooltipIcon"] svg line,
[data-testid="stTooltipIcon"] svg rect {
    fill: #ffffff !important;
    stroke: #ffffff !important;
}
[data-testid="stTooltipIcon"]:hover svg circle {
    fill: #8855cc !important;
    stroke: #8855cc !important;
}
[data-testid="stTooltipIcon"]:hover svg path,
[data-testid="stTooltipIcon"]:hover svg line,
[data-testid="stTooltipIcon"]:hover svg rect {
    fill: #ffffff !important;
    stroke: #ffffff !important;
}

/* ── Tooltip popup ───────────────────────────────────────────────── */
[data-testid="stTooltipContent"], [data-testid="stTooltipContent"] *,
div[role="tooltip"], div[role="tooltip"] *,
div[data-baseweb="tooltip"], div[data-baseweb="tooltip"] *,
div[data-baseweb="popover"], div[data-baseweb="popover"] * {
    background-color: #14142e !important;
    color: #ece8e0 !important;
    border-color: #30305a !important;
    font-family: "Lora", serif !important;
    font-size: 0.84rem !important;
    line-height: 1.7 !important;
}

/* ── Generate button ─────────────────────────────────────────────── */
.stButton > button[kind="primary"],
.stFormSubmitButton > button[kind="primary"] {
    background: linear-gradient(135deg, #3d2080 0%, #6633bb 50%, #8855dd 100%);
    background-size: 200% 200%;
    border: none;
    color: #fff;
    font-family: "Cinzel", serif;
    font-size: 0.88rem;
    letter-spacing: 0.1em;
    border-radius: 8px;
    padding: 0.68rem 1.4rem;
    transition: all 0.3s ease;
    box-shadow: 0 4px 22px rgba(100,60,200,0.35);
}
.stButton > button[kind="primary"]:hover,
.stFormSubmitButton > button[kind="primary"]:hover {
    background-position: right center;
    box-shadow: 0 6px 30px rgba(130,80,220,0.5);
    transform: translateY(-1px);
}
.stButton > button[kind="primary"]:active,
.stFormSubmitButton > button[kind="primary"]:active {
    transform: translateY(0);
}

/* ── Secondary buttons ───────────────────────────────────────────── */
.stButton > button[kind="secondary"],
[data-testid="baseButton-secondary"] {
    background: transparent !important;
    border: 1px solid #2a2a50 !important;
    color: #b0a0cc !important;
    font-family: "Raleway", sans-serif;
    font-size: 0.8rem;
    letter-spacing: 0.04em;
    border-radius: 6px;
    transition: all 0.2s ease;
}
.stButton > button[kind="secondary"]:hover,
[data-testid="baseButton-secondary"]:hover {
    background: #14143a !important;
    border-color: #5533aa !important;
    color: #ddd0ff !important;
}

/* ── Page header ─────────────────────────────────────────────────── */
.page-header {
    padding: 2rem 0 1.4rem;
    border-bottom: 1px solid #1e1e3a;
    margin-bottom: 1.8rem;
    text-align: center;
}
.page-header h1 {
    margin: 0;
    font-family: "Cinzel", serif;
    font-size: 2.2rem;
    font-weight: 500;
    background: linear-gradient(135deg, #c8a8f8 0%, #a0c4ff 45%, #c8a8f8 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    letter-spacing: 0.08em;
}
.page-header p {
    margin: 0.5rem 0 0;
    color: #9988cc;
    font-style: italic;
    font-size: 0.92rem;
    letter-spacing: 0.02em;
}

/* ── Birth data card ─────────────────────────────────────────────── */
.birth-data-card {
    display: flex;
    flex-wrap: wrap;
    background: linear-gradient(135deg, #0c0c24 0%, #101028 100%);
    border: 1px solid #222244;
    border-radius: 12px;
    padding: 1.2rem 1.6rem;
    margin-bottom: 1.4rem;
    box-shadow: 0 4px 28px rgba(60,40,120,0.18);
    gap: 0;
}
.bdc-item {
    flex: 1;
    min-width: 130px;
    padding: 0.3rem 1.2rem 0.3rem 0;
    border-right: 1px solid #1e1e3a;
}
.bdc-item:last-child { border-right: none; }
.bdc-label {
    display: block;
    font-family: "Raleway", sans-serif;
    font-size: 0.63rem;
    font-weight: 600;
    letter-spacing: 0.13em;
    text-transform: uppercase;
    color: #8877aa;
    margin-bottom: 0.22rem;
}
.bdc-value {
    display: block;
    font-family: "Lora", serif;
    font-size: 0.92rem;
    font-weight: 600;
    color: #e0d4fc;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.bdc-sub {
    display: block;
    font-family: "Raleway", sans-serif;
    font-size: 0.68rem;
    color: #8877aa;
    margin-top: 0.12rem;
    font-style: italic;
}

/* ── Report card ─────────────────────────────────────────────────── */
.report-card {
    background: linear-gradient(180deg, #0c0c22 0%, #0a0a1e 100%);
    border: 1px solid #1e1e3a;
    border-radius: 14px;
    padding: 2.4rem 2.8rem;
    margin-bottom: 1.6rem;
    line-height: 1.95;
    color: #ede8e0;
    box-shadow: 0 8px 48px rgba(50,30,110,0.2);
}
.report-card h1,
.report-card h2,
.report-card h3,
.report-card h4 {
    font-family: "Cinzel", serif;
    color: #cca8ff;
    font-size: 0.84rem;
    font-weight: 500;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    border: none;
    border-left: 3px solid #7744cc;
    padding: 0.25rem 0 0.25rem 0.85rem;
    margin-top: 2.2rem;
    margin-bottom: 0.9rem;
    background: linear-gradient(90deg, rgba(100,60,200,0.1) 0%, transparent 100%);
    border-radius: 0 4px 4px 0;
}
.report-card h1:first-child,
.report-card h2:first-child,
.report-card h3:first-child,
.report-card h4:first-child { margin-top: 0; }
.report-card hr { display: none; }
.report-card strong { color: #ddd0ff; }
.report-card em { color: #c8bce8; }
.report-card li { margin-bottom: 0.45rem; padding-left: 0.2rem; }
.report-card li::marker { color: #8855cc; }
.report-card p { margin-bottom: 0.95rem; }

/* ── Chart SVG wrapper ───────────────────────────────────────────── */
.chart-svg-wrapper {
    background: #0c0c22;
    border: 1px solid #1e1e3a;
    border-radius: 12px;
    padding: 1rem;
    margin-bottom: 0.6rem;
}
.chart-svg-wrapper img { width: 100%; height: auto; display: block; }

/* ── Metric cards (fallback) ─────────────────────────────────────── */
[data-testid="stMetric"] {
    background: #0e0e26;
    border: 1px solid #1e1e3a;
    border-radius: 10px;
    padding: 0.85rem 1rem;
}
[data-testid="stMetricLabel"] {
    color: #8877aa !important;
    font-family: "Raleway", sans-serif !important;
    font-size: 0.65rem;
    text-transform: uppercase;
    letter-spacing: 0.1em;
}
[data-testid="stMetricValue"] {
    color: #ddd0ff !important;
    font-family: "Lora", serif !important;
    font-size: 0.95rem;
}

/* ── Chat ────────────────────────────────────────────────────────── */
[data-testid="stChatMessage"] {
    background: #0e0e26;
    border: 1px solid #1e1e3a;
    border-radius: 10px;
    margin-bottom: 0.6rem;
    color: #ede8e0 !important;
}
[data-testid="stChatMessage"] p,
[data-testid="stChatMessage"] li,
[data-testid="stChatMessage"] span,
[data-testid="stChatMessage"] div { color: #ede8e0 !important; }
[data-testid="stChatMessage"] strong { color: #ddd0ff !important; }
[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] { color: #ede8e0 !important; }
.stChatInputContainer textarea {
    background: #10102a !important;
    border: 1px solid #2a2a50 !important;
    color: #f0ebe3 !important;
    border-radius: 8px !important;
    font-family: "Lora", serif !important;
}

/* ── Download buttons ────────────────────────────────────────────── */
[data-testid="stDownloadButton"] > button {
    background: transparent !important;
    border: 1px solid #2a2a50 !important;
    color: #b0a0cc !important;
    font-family: "Raleway", sans-serif;
    font-size: 0.8rem;
    letter-spacing: 0.04em;
    border-radius: 6px;
    transition: all 0.2s ease;
}
[data-testid="stDownloadButton"] > button:hover {
    background: #14143a !important;
    border-color: #5533aa !important;
    color: #ddd0ff !important;
}

/* ── Alerts ──────────────────────────────────────────────────────── */
[data-testid="stAlert"] {
    border-radius: 10px;
    font-family: "Lora", serif;
}

/* ── Tabs ────────────────────────────────────────────────────────── */
[data-testid="stTabs"] [data-baseweb="tab"] {
    font-family: "Raleway", sans-serif;
    font-size: 0.78rem;
    font-weight: 500;
    letter-spacing: 0.05em;
    color: #9988bb !important;
    background: transparent;
    border-bottom: 2px solid transparent;
    padding: 0.55rem 1rem;
    transition: color 0.2s ease;
}
[data-testid="stTabs"] [data-baseweb="tab"]:hover { color: #b0a0d0 !important; }
[data-testid="stTabs"] [data-baseweb="tab"][aria-selected="true"] {
    font-weight: 600;
    color: #c8a8f8 !important;
    border-bottom: 2px solid #6633bb !important;
}
[data-testid="stTabs"] [data-baseweb="tab-list"] {
    border-bottom: 1px solid #1e1e3a;
    gap: 0.1rem;
    background: transparent;
}

/* ── Dividers ────────────────────────────────────────────────────── */
hr { border-color: #181830; }

/* ── Expanders ───────────────────────────────────────────────────── */
[data-testid="stExpander"] summary {
    font-family: "Raleway", sans-serif;
    font-size: 0.8rem;
    letter-spacing: 0.05em;
    color: #8877aa !important;
}
[data-testid="stExpander"] summary:hover { color: #b0a0d0 !important; }
[data-testid="stExpander"] {
    border: 1px solid #1e1e3a !important;
    border-radius: 8px !important;
    background: #0e0e26 !important;
}
[data-testid="stExpander"] p,
[data-testid="stExpander"] span,
[data-testid="stExpander"] div,
[data-testid="stExpander"] small,
[data-testid="stExpander"] label { color: #c8c0c0 !important; }
[data-testid="stExpander"] strong { color: #ddd0ff !important; }

/* ── Multiselect ─────────────────────────────────────────────────── */
[data-testid="stSidebar"] [data-testid="stMultiSelect"] [data-baseweb="select"] {
    background: #10102a !important;
    border-color: #2a2a50 !important;
}
[data-testid="stSidebar"] [data-testid="stMultiSelect"] [data-baseweb="select"] > div {
    background: #10102a !important;
    color: #b0a0cc !important;
}
[data-testid="stSidebar"] [data-testid="stMultiSelect"] input {
    color: #b0a0cc !important;
    background: transparent !important;
    caret-color: #b0a0cc !important;
}
[data-testid="stSidebar"] [data-testid="stMultiSelect"] [data-baseweb="tag"] {
    background-color: #33228a !important;
    color: #d4bfff !important;
    border-radius: 4px !important;
}
[data-testid="stSidebar"] [data-testid="stMultiSelect"] svg { fill: #b0a0cc !important; }
[data-testid="stSidebar"] [data-testid="stMultiSelect"] [data-baseweb="select"] > div:last-child {
    background: transparent !important;
}
[data-testid="stSidebar"] [data-testid="stMultiSelect"] ul { background: #10102a !important; }
[data-testid="stSidebar"] [data-testid="stMultiSelect"] li {
    background: #10102a !important;
    color: #b0a0cc !important;
}
[data-testid="stSidebar"] [data-testid="stMultiSelect"] li:hover { background: #1a1a40 !important; }

/* ── Placeholder panel ───────────────────────────────────────────── */
.placeholder-panel {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 65vh;
    text-align: center;
    gap: 0.9rem;
}
.placeholder-panel .astro-glyph {
    font-size: 3.8rem;
    opacity: 0.15;
    line-height: 1;
}
.placeholder-panel h3 {
    font-family: "Cinzel", serif;
    color: #6666aa;
    font-size: 1.15rem;
    letter-spacing: 0.1em;
    margin: 0;
}
.placeholder-panel p {
    font-style: italic;
    margin: 0;
    font-size: 0.88rem;
    color: #5a5a88;
    line-height: 1.7;
}

/* ── Chat section header ─────────────────────────────────────────── */
.chat-section-header {
    padding: 1.2rem 0 0.4rem;
    border-top: 1px solid #181830;
    margin-top: 0.5rem;
}
.chat-section-header p {
    font-family: "Cinzel", serif;
    color: #9988cc;
    font-size: 0.82rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin: 0 0 0.3rem;
}
.chat-section-header small {
    font-family: "Raleway", sans-serif;
    font-size: 0.75rem;
    color: #6a6a99;
    font-style: italic;
}
</style>
""", unsafe_allow_html=True)

# --- Session state initialisation ---
if "f_birth_time_timezone" not in st.session_state:
    st.session_state["f_birth_time_timezone"] = "UTC"
if "f_report_focus" not in st.session_state:
    st.session_state["f_report_focus"] = []
if "report_result" not in st.session_state:
    st.session_state.report_result = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "validation_message" not in st.session_state:
    st.session_state.validation_message = None
if "synastry_result" not in st.session_state:
    st.session_state.synastry_result = None
if "synastry_chat_history" not in st.session_state:
    st.session_state.synastry_chat_history = []
if "synastry_error" not in st.session_state:
    st.session_state.synastry_error = None
if "_prepared_state" not in st.session_state:
    st.session_state._prepared_state = None
if "_synastry_prepared" not in st.session_state:
    st.session_state._synastry_prepared = None
if "_stream_error" not in st.session_state:
    st.session_state._stream_error = None
if "_chart_cache_key" not in st.session_state:
    st.session_state._chart_cache_key = None
if "_chart_cache_prepared" not in st.session_state:
    st.session_state._chart_cache_prepared = None
if "_synastry_cache_key" not in st.session_state:
    st.session_state._synastry_cache_key = None
if "_synastry_cache_prepared" not in st.session_state:
    st.session_state._synastry_cache_prepared = None
if "_transit_calendar" not in st.session_state:
    st.session_state._transit_calendar = None
if "_transit_calendar_key" not in st.session_state:
    st.session_state._transit_calendar_key = None
if "_save_toast" not in st.session_state:
    st.session_state._save_toast = None
if "_pending_load" not in st.session_state:
    st.session_state._pending_load = None
if "_daily_sky" not in st.session_state:
    st.session_state._daily_sky = None
if "_daily_sky_date" not in st.session_state:
    st.session_state._daily_sky_date = None
if "_weekly_forecast" not in st.session_state:
    st.session_state._weekly_forecast = None
if "_weekly_forecast_date" not in st.session_state:
    st.session_state._weekly_forecast_date = None
if "_monthly_forecast" not in st.session_state:
    st.session_state._monthly_forecast = None
if "_monthly_forecast_month" not in st.session_state:
    st.session_state._monthly_forecast_month = None
if "_yearly_forecast" not in st.session_state:
    st.session_state._yearly_forecast = None
if "_yearly_forecast_year" not in st.session_state:
    st.session_state._yearly_forecast_year = None
if "_overall_forecast" not in st.session_state:
    st.session_state._overall_forecast = None
if "_overall_forecast_year" not in st.session_state:
    st.session_state._overall_forecast_year = None

# Drain a pending chart load into widget keys before any widget is instantiated
if st.session_state._pending_load is not None:
    _pl = st.session_state._pending_load
    st.session_state._pending_load = None
    from datetime import date as _ld, time as _lt
    try:
        _yy, _mm, _dd = map(int, (_pl.get("parsed_dob") or "1990-01-01").split("-"))
        st.session_state["f_dob"] = _ld(_yy, _mm, _dd)
    except Exception:
        pass
    try:
        _hh, _min = map(int, (_pl.get("birth_time") or "12:00").split(":"))
        st.session_state["f_birth_time"] = _lt(_hh, _min)
    except Exception:
        pass
    st.session_state["f_full_name"] = _pl.get("full_name") or ""
    st.session_state["f_birth_location"] = _pl.get("birth_location") or ""
    st.session_state["f_birth_time_timezone"] = _pl.get("birth_time_timezone") or "UTC"
    st.session_state["f_birth_time_confidence"] = _pl.get("birth_time_confidence") or "exact"
    st.session_state["f_house_system"] = _pl.get("house_system") or "Placidus"
    st.session_state["f_current_location"] = _pl.get("current_location") or ""
    st.session_state["f_additional_info"] = _pl.get("additional_info") or ""
    _focus_str = _pl.get("report_focus") or ""
    _focus_opts = [
        "Career & Purpose", "Relationships & Love", "Finance & Wealth",
        "Health & Vitality", "Spirituality & Growth", "Family & Home",
        "Creativity & Expression", "Travel & Adventure",
    ]
    st.session_state["f_report_focus"] = [
        f.strip() for f in _focus_str.split(",") if f.strip() in _focus_opts
    ] if _focus_str else []

ALL_TIMEZONES = pytz.all_timezones
DEFAULT_TZ_INDEX = ALL_TIMEZONES.index("UTC")


def _render_svg(svg: str) -> None:
    """Render an SVG string as a responsive image in a dark-themed wrapper."""
    import base64
    b64 = base64.b64encode(svg.encode("utf-8")).decode("utf-8")
    st.markdown(
        f'<div class="chart-svg-wrapper">'
        f'<img src="data:image/svg+xml;base64,{b64}" '
        f'style="width:100%;height:auto;display:block;" /></div>',
        unsafe_allow_html=True,
    )


def _birth_data_card(state: dict) -> None:
    """Render an elegant birth data summary card."""
    dob = state.get("parsed_dob") or ""
    birth_loc = state.get("birth_location") or ""
    birth_time_val = state.get("birth_time") or ""
    tz_val = state.get("birth_time_timezone") or ""
    current_loc = state.get("current_location") or ""
    reading_date = (state.get("parsed_current_datetime") or "")[:10]
    house_sys = state.get("house_system") or ""
    focus = state.get("report_focus") or ""

    items = [
        ("Name", state.get("full_name") or "—", ""),
        ("Date of Birth", dob, birth_loc),
        ("Birth Time", birth_time_val, tz_val),
        ("Current Location", current_loc, f"Reading: {reading_date}"),
    ]
    if house_sys:
        items.append(("House System", house_sys, f"Focus: {focus}" if focus else ""))

    items_html = "".join(
        f'<div class="bdc-item">'
        f'<span class="bdc-label">{label}</span>'
        f'<span class="bdc-value">{value}</span>'
        + (f'<span class="bdc-sub">{sub}</span>' if sub else "")
        + "</div>"
        for label, value, sub in items
    )
    st.markdown(f'<div class="birth-data-card">{items_html}</div>', unsafe_allow_html=True)

# ── Sidebar: input form ───────────────────────────────────────────────────────
_FOCUS_OPTIONS = [
    "Career & Purpose",
    "Relationships & Love",
    "Finance & Wealth",
    "Health & Vitality",
    "Spirituality & Growth",
    "Family & Home",
    "Creativity & Expression",
    "Travel & Adventure",
]

with st.sidebar:
    st.markdown(
        '<h2 style="font-family:Cinzel,serif;font-size:1.05rem;font-weight:500;'
        'letter-spacing:0.1em;color:#b898e8;margin:0.5rem 0 1rem;">✦ Your Chart Details</h2>',
        unsafe_allow_html=True,
    )

    # ── Chart at a Glance + Today's Sky (shown above form once a reading exists) ──
    _glance_result = st.session_state.report_result
    if _glance_result and _glance_result.get("chart_data"):
        _gcd = _glance_result["chart_data"]
        _g_sun = (_gcd.get("sun") or {})
        _g_moon = (_gcd.get("moon") or {})
        _g_asc = (_gcd.get("ascendant") or {})
        if _g_sun.get("sign") or _g_moon.get("sign") or _g_asc.get("sign"):
            st.markdown(f"""
<div style="background:#0c0c24;border:1px solid #1e1e3a;border-radius:10px;
            padding:0.85rem 1rem;margin-bottom:0.8rem;">
  <div style="font-family:Raleway,sans-serif;font-size:0.6rem;font-weight:600;
              letter-spacing:0.13em;text-transform:uppercase;color:#8877aa;
              margin-bottom:0.55rem;">Chart at a Glance</div>
  <div style="display:flex;gap:0;">
    <div style="flex:1;text-align:center;border-right:1px solid #181830;padding:0 0.4rem;">
      <div style="font-size:1rem;color:#ffd580;margin-bottom:0.15rem;">☉</div>
      <div style="font-family:Lora,serif;font-size:0.78rem;color:#e0d4fc;">{_g_sun.get('sign','—')}</div>
    </div>
    <div style="flex:1;text-align:center;border-right:1px solid #181830;padding:0 0.4rem;">
      <div style="font-size:1rem;color:#aac8ff;margin-bottom:0.15rem;">☽</div>
      <div style="font-family:Lora,serif;font-size:0.78rem;color:#e0d4fc;">{_g_moon.get('sign','—')}</div>
    </div>
    <div style="flex:1;text-align:center;padding:0 0.4rem;">
      <div style="font-size:1rem;color:#a8f0d0;margin-bottom:0.15rem;">↑</div>
      <div style="font-family:Lora,serif;font-size:0.78rem;color:#e0d4fc;">{_g_asc.get('sign','—')}</div>
    </div>
  </div>
</div>""", unsafe_allow_html=True)

        # Today's Sky
        _today_date = date.today().isoformat()
        if st.session_state._daily_sky_date != _today_date or st.session_state._daily_sky is None:
            try:
                _sky_computed = compute_daily_sky(
                    natal_chart=_gcd,
                    current_year=date.today().year,
                    current_month=date.today().month,
                    current_day=date.today().day,
                )
                st.session_state._daily_sky = _sky_computed
                st.session_state._daily_sky_date = _today_date
            except Exception:
                st.session_state._daily_sky = {}

        _sky = st.session_state._daily_sky or {}
        if _sky:
            st.markdown("**🔭 Today's Sky**")
            _moon_sign = _sky.get("moon_sign") or "—"
            _moon_deg = _sky.get("moon_degree", "")
            _voc_badge = " *(VOC)*" if _sky.get("moon_voc") else ""
            st.caption(f"🌙 Moon in {_moon_sign} {_moon_deg}°{_voc_badge}")
            _ct = _sky.get("closest_transit")
            if _ct:
                st.caption(f"⚡ {_ct['summary']}")
            _retro = _sky.get("retrograde_planets") or []
            if _retro:
                st.caption("Rx: " + ", ".join(f"{r['planet'].title()} in {r['sign']}" for r in _retro))

        st.divider()

    with st.form("astro_form"):
        st.caption("Fields marked * are required. Hover the ⓘ icon on any field for guidance.")

        st.markdown("#### Birth Information")
        full_name = st.text_input(
            "Full Name *",
            placeholder="e.g., Jane Doe",
            key="f_full_name",
            help="Used to personalise your reading. Can be your full name or a preferred name.",
        )
        dob = st.date_input(
            "Date of Birth *",
            value=None,
            min_value=date(1900, 1, 1),
            max_value=date.today(),
            key="f_dob",
            help="Your exact birth date determines your Sun sign and all planetary positions in the natal chart.",
        )
        birth_time = st.time_input(
            "Birth Time *",
            value=None,
            step=60,
            key="f_birth_time",
            help=(
                "The single most important field after date of birth. "
                "Even 15 minutes can shift your Ascendant sign and all 12 house cusps, "
                "changing a significant portion of the reading. "
                "Check your birth certificate or hospital records for the most accurate time."
            ),
        )
        birth_time_confidence = st.selectbox(
            "Birth Time Confidence",
            options=["exact", "approximate", "unknown"],
            index=0,
            key="f_birth_time_confidence",
            help=(
                "How certain are you of the birth time? "
                "Exact = from official records. "
                "Approximate = you were told a rough time (±30 min). "
                "Unknown = no time available. "
                "Approximate/unknown softens Ascendant and house interpretations and adds a birth-time rectification section to your report."
            ),
        )
        birth_location = st.text_input(
            "Birth Location *",
            placeholder="e.g., Mumbai, Maharashtra, India",
            key="f_birth_location",
            help=(
                "The city where you were born. Used to calculate your Ascendant, "
                "Midheaven, and all 12 house cusps. "
                "Format: City, Region, Country. "
                "Be as specific as possible — a large country alone (e.g., 'India') is not sufficient."
            ),
        )
        birth_time_timezone = st.selectbox(
            "Birth Timezone *",
            options=ALL_TIMEZONES,
            key="f_birth_time_timezone",
            help=(
                "The timezone of your birth location — not your current timezone. "
                "For example, someone born in Mumbai uses Asia/Kolkata even if they now live in New York. "
                "Search by city name or region (e.g., 'Kolkata', 'London', 'New_York')."
            ),
        )
        house_system = st.selectbox(
            "House System",
            options=["Placidus", "Whole Sign", "Koch"],
            index=0,
            key="f_house_system",
            help=(
                "Determines how the sky is divided into 12 life areas (houses). "
                "Placidus is the standard in modern Western astrology. "
                "Whole Sign is the oldest system, used in Hellenistic and Vedic traditions — each sign = one house. "
                "Koch is popular in German-speaking countries and emphasises the MC axis. "
                "If you're unsure, leave as Placidus."
            ),
        )
        current_location = st.text_input(
            "Current Location *",
            placeholder="e.g., New York, NY, USA",
            key="f_current_location",
            help=(
                "Where you live right now. Used to calculate current planetary transits, "
                "your Solar Return chart (annual forecast), and Lunar Return chart (monthly forecast). "
                "Format: City, Region, Country."
            ),
        )

        st.markdown("#### Optional")
        additional_info = st.text_area(
            "Additional Context",
            placeholder="e.g., I'm considering a career change and recently ended a long relationship…",
            height=100,
            key="f_additional_info",
            help=(
                "Share anything you'd like the reading to address — recent life events, "
                "decisions you're facing, relationships, career questions, or health concerns. "
                "The more specific you are, the more relevant the guidance will be."
            ),
        )

        st.markdown("#### Report Focus")
        st.caption("Adds a dedicated deep-dive section on your chosen life areas. The rest of the reading remains comprehensive.")
        _focus_selections = st.multiselect(
            "Report Focus",
            options=_FOCUS_OPTIONS,
            key="f_report_focus",
            label_visibility="collapsed",
            placeholder="Select focus areas (optional)...",
            help="Select one or more life areas for a focused analysis section at the end of your report.",
        )
        report_focus = ", ".join(_focus_selections) if _focus_selections else None

        submitted = st.form_submit_button(
            "Generate My Reading ⭐",
            type="primary",
            use_container_width=True,
        )

    # My Charts panel — outside the form so buttons work independently
    st.divider()
    with st.expander("📚 My Saved Charts", expanded=False):
        _saved = list_charts()
        if not _saved:
            st.markdown("No saved charts yet. Generate a reading and click **Save Reading**.")
        else:
            for _c in _saved:
                _icon = "⭐" if _c["chart_type"] == "natal" else "💞"
                _date = _c["created_at"][:10]
                st.markdown(f"{_icon} **{_c['name']}** · {_date}")
                _col2, _col3 = st.columns([3, 1])
                with _col2:
                    if st.button("Load", key=f"load_{_c['id']}", use_container_width=True):
                        _loaded = load_chart(_c["id"])
                        if _loaded:
                            if _c["chart_type"] == "natal":
                                st.session_state.report_result = _loaded
                                st.session_state.chat_history = []
                                st.session_state.validation_message = None
                                st.session_state._prepared_state = None
                                st.session_state._transit_calendar = None
                                # Schedule form repopulation for the next run
                                st.session_state._pending_load = _loaded
                            else:
                                st.session_state.synastry_result = _loaded
                            st.rerun()
                with _col3:
                    if st.button("✕", key=f"del_{_c['id']}", use_container_width=True):
                        delete_chart(_c["id"])
                        st.rerun()


# --- Form submission: validate + compute chart, then stream report in the tab ---
if submitted:
    st.session_state.report_result = None
    st.session_state.chat_history = []
    st.session_state.validation_message = None
    st.session_state._prepared_state = None
    st.session_state._stream_error = None

    # Cache key covers every field that affects chart computation
    _today = datetime.now(pytz.UTC).date().isoformat()
    _cache_key = (
        (full_name or "").strip().lower(),
        dob.strftime("%Y-%m-%d") if dob else None,
        (birth_location or "").strip().lower(),
        birth_time.strftime("%H:%M") if birth_time else None,
        birth_time_timezone,
        house_system,
        (current_location or "").strip().lower(),
        _today,
    )

    if (
        _cache_key == st.session_state._chart_cache_key
        and st.session_state._chart_cache_prepared is not None
    ):
        # Birth details unchanged — reuse cached chart, regenerate report only
        _cached = st.session_state._chart_cache_prepared
        st.session_state._prepared_state = {
            **_cached,
            "report_focus": report_focus.strip() if report_focus else None,
            "additional_info": additional_info.strip() if additional_info else None,
            "current_datetime": datetime.now(pytz.UTC).isoformat(),
        }
        st.info("Chart cached — regenerating report with updated focus/context.", icon="⚡")
    else:
        payload: AstrologerState = {
            "full_name": full_name.strip() if full_name else None,
            "dob": dob.strftime("%Y-%m-%d") if dob else None,
            "birth_location": birth_location.strip() if birth_location else None,
            "birth_time": birth_time.strftime("%H:%M") if birth_time else None,
            "birth_time_timezone": birth_time_timezone,
            "birth_time_confidence": birth_time_confidence,
            "house_system": house_system,
            "current_location": current_location.strip() if current_location else None,
            "additional_info": additional_info.strip() if additional_info else None,
            "report_focus": report_focus.strip() if report_focus else None,
            "current_datetime": datetime.now(pytz.UTC).isoformat(),
            "missing_fields": [],
            "validation_errors": {},
            "parsed_dob": None,
            "parsed_birth_datetime": None,
            "parsed_current_datetime": None,
            "chart_data": None,
            "follow_up_message": None,
            "final_report": None,
        }

        from agent.nodes import (
            ingest_inputs as _ingest, validate_required_fields as _validate,
            normalize_and_parse as _normalize, request_follow_up as _follow_up,
            compute_astro as _compute_astro,
        )
        with st.status("Consulting the stars...", expanded=True) as _status:
            _status.write("🔮 Validating your birth details...")
            _s = {**payload, **_ingest(payload)}
            _s = {**_s, **_validate(_s)}
            if _s.get("missing_fields") or _s.get("validation_errors"):
                _s = {**_s, **_follow_up(_s)}
                prepared = _s
            else:
                _status.write("📅 Parsing birth time & timezone...")
                _norm = _normalize(_s)
                _s = {**_s, **_norm}
                if _s.get("validation_errors"):
                    _s = {**_s, **_follow_up(_s)}
                    prepared = _s
                else:
                    _chart = _compute_astro(_s, _progress_cb=_status.write)
                    _s = {**_s, **_chart}
                    prepared = _s
            _status.update(
                label="Chart ready! ✨" if prepared.get("parsed_birth_datetime") else "Please review the details below.",
                state="complete" if prepared.get("parsed_birth_datetime") else "error",
            )

        if prepared.get("follow_up_message"):
            st.session_state.validation_message = prepared["follow_up_message"]
        elif prepared.get("parsed_birth_datetime"):
            st.session_state._prepared_state = prepared
            st.session_state._chart_cache_key = _cache_key
            st.session_state._chart_cache_prepared = prepared
        else:
            st.session_state.validation_message = "__error__"

# ── Main area: output ─────────────────────────────────────────────────────────
st.markdown("""
<div class="page-header">
  <h1>✦ Personal Astrologer</h1>
  <p>Your natal chart, decoded by artificial intelligence</p>
</div>
""", unsafe_allow_html=True)

if st.session_state._save_toast:
    st.success(st.session_state._save_toast)
    st.session_state._save_toast = None

natal_tab, weekly_tab, monthly_tab, yearly_tab, overall_tab, calendar_tab, synastry_tab = st.tabs(["My Reading", "🌟 This Week", "🌙 This Month", "☀️ This Year", "🔮 Overall", "Transit Calendar", "Compatibility / Synastry"])

with natal_tab:
    if st.session_state.validation_message == "__error__":
        st.error("An unexpected error occurred. Please try again.")

    elif st.session_state.validation_message:
        st.warning("Please correct the following before your reading can be generated:")
        st.markdown(st.session_state.validation_message)

    elif st.session_state._prepared_state:
        prepared = st.session_state._prepared_state

        _birth_data_card(prepared)
        st.divider()

        # Chart SVGs
        _cd0 = prepared.get("chart_data") or {}
        chart_svg = _cd0.get("chart_svg") or ""
        vedic_svg = _cd0.get("vedic_svg") or ""
        transit_svg = _cd0.get("transit_svg") or ""
        if chart_svg or vedic_svg or transit_svg:
            tab_labels = []
            if chart_svg:
                tab_labels.append("Natal Chart")
            if transit_svg:
                tab_labels.append("Transit Overlay")
            if vedic_svg:
                tab_labels.append("Vedic Chart")
            chart_tabs = st.tabs(tab_labels)
            tab_idx = 0
            if chart_svg:
                with chart_tabs[tab_idx]:
                    _render_svg(chart_svg)
                tab_idx += 1
            if transit_svg:
                with chart_tabs[tab_idx]:
                    _render_svg(transit_svg)
                tab_idx += 1
            if vedic_svg:
                with chart_tabs[tab_idx]:
                    _render_svg(vedic_svg)
            st.divider()

        if st.session_state._stream_error:
            st.error(f"Report generation failed: {st.session_state._stream_error}")
            if st.button("Retry", type="primary"):
                st.session_state._stream_error = None
                st.rerun()
        else:
            try:
                st.caption("✨ Generating in 3 parts — personality & soul first, then cosmic timing, then advanced windows & Vedic analysis. Each part streams live as it's written...")
                report_text = st.write_stream(generate_report_stream(prepared))
                st.session_state.report_result = {**prepared, "final_report": report_text}
                st.session_state._prepared_state = None
                st.rerun()
            except Exception as exc:
                st.session_state._stream_error = str(exc)
                st.rerun()

    elif st.session_state.report_result:
        result = st.session_state.report_result

        _birth_data_card(result)
        st.divider()

        # Chart wheels — regenerate SVGs if missing (e.g. loaded from saved charts where SVGs are stripped)
        _cd1 = result.get("chart_data") or {}
        _needs_regen = (
            (not _cd1.get("chart_svg") or not _cd1.get("vedic_svg"))
            and _cd1.get("_natal_lat") is not None
            and result.get("parsed_birth_datetime")
        )
        if _needs_regen:
            try:
                from astro.compute import generate_chart_svg as _gen_svg, generate_vedic_chart_svg as _gen_vedic_svg
                _bdt = datetime.fromisoformat(result["parsed_birth_datetime"])
                _lat = _cd1["_natal_lat"]
                _lng = _cd1["_natal_lng"]
                _tz = result.get("birth_time_timezone") or "UTC"
                _hs = result.get("house_system") or "Placidus"
                _name = result.get("full_name", "")
                _updates = {}
                if not _cd1.get("chart_svg"):
                    _svg = _gen_svg(
                        full_name=_name,
                        birth_year=_bdt.year, birth_month=_bdt.month, birth_day=_bdt.day,
                        birth_hour=_bdt.hour, birth_minute=_bdt.minute,
                        city="", nation="", tz_str=_tz, house_system=_hs,
                        lat=_lat, lng=_lng,
                    )
                    if _svg:
                        _updates["chart_svg"] = _svg
                if not _cd1.get("vedic_svg"):
                    _vsvg = _gen_vedic_svg(
                        full_name=_name,
                        birth_year=_bdt.year, birth_month=_bdt.month, birth_day=_bdt.day,
                        birth_hour=_bdt.hour, birth_minute=_bdt.minute,
                        tz_str=_tz, lat=_lat, lng=_lng,
                    )
                    if _vsvg:
                        _updates["vedic_svg"] = _vsvg
                if _updates:
                    _cd1 = {**_cd1, **_updates}
                    st.session_state.report_result = {**result, "chart_data": _cd1}
            except Exception:
                pass
        chart_svg = _cd1.get("chart_svg") or ""
        vedic_svg = _cd1.get("vedic_svg") or ""
        transit_svg = _cd1.get("transit_svg") or ""
        if chart_svg or vedic_svg or transit_svg:
            tab_labels = []
            if chart_svg:
                tab_labels.append("Natal Chart")
            if transit_svg:
                tab_labels.append("Transit Overlay")
            if vedic_svg:
                tab_labels.append("Vedic Chart")
            chart_tabs = st.tabs(tab_labels)
            tab_idx = 0
            if chart_svg:
                with chart_tabs[tab_idx]:
                    _render_svg(chart_svg)
                    st.download_button(
                        "Download Natal SVG", data=chart_svg,
                        file_name=f"natal_{result['full_name'].replace(' ', '_')}.svg",
                        mime="image/svg+xml",
                    )
                tab_idx += 1
            if transit_svg:
                with chart_tabs[tab_idx]:
                    _render_svg(transit_svg)
                    st.download_button(
                        "Download Transit SVG", data=transit_svg,
                        file_name=f"transit_{result['full_name'].replace(' ', '_')}.svg",
                        mime="image/svg+xml",
                    )
                tab_idx += 1
            if vedic_svg:
                with chart_tabs[tab_idx]:
                    _render_svg(vedic_svg)
                    st.download_button(
                        "Download Vedic SVG", data=vedic_svg,
                        file_name=f"vedic_{result['full_name'].replace(' ', '_')}.svg",
                        mime="image/svg+xml",
                    )
            st.divider()

        # Regenerate report button
        _regen_col, _ = st.columns([1, 3])
        with _regen_col:
            if st.button("↺ Regenerate Reading", key="regen_natal", use_container_width=True):
                from cache.report_cache import make_report_key, delete_report as _del_report
                _new_focus = ", ".join(st.session_state.get("f_report_focus") or []) or None
                _rk = make_report_key(
                    dob=result.get("parsed_dob") or "",
                    birth_location=result.get("birth_location") or "",
                    birth_time=result.get("birth_time") or "",
                    birth_time_timezone=result.get("birth_time_timezone") or "UTC",
                    house_system=result.get("house_system") or "Placidus",
                    current_location=result.get("current_location") or "",
                    current_date=(result.get("parsed_current_datetime") or "")[:10],
                    report_focus=_new_focus or "",
                    additional_info=result.get("additional_info") or "",
                )
                _del_report(_rk)
                st.session_state._prepared_state = {
                    **result,
                    "report_focus": _new_focus,
                    "current_datetime": datetime.now(pytz.UTC).isoformat(),
                    "parsed_current_datetime": datetime.now(pytz.UTC).isoformat(),
                }
                st.session_state.report_result = None
                st.session_state._stream_error = None
                st.rerun()

        # House system mismatch warning
        if result.get("house_system") and result.get("house_system") != house_system:
            st.info(
                f"House system changed to **{house_system}** — this reading used **{result['house_system']}**. "
                "Click **Generate My Reading** to update your chart."
            )

        # Report rendered in a styled card
        import markdown as _md
        _report_html_body = _md.markdown(result["final_report"], extensions=["extra"])
        st.markdown(
            f'<div class="report-card">{_report_html_body}</div>',
            unsafe_allow_html=True,
        )

        # Downloads
        _chart_svg_block = (
            f'<div style="display:flex;justify-content:center;margin:1.5rem 0;">'
            f'<div style="max-width:560px;">{chart_svg}</div></div>'
        ) if chart_svg else ""
        _html_export = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<title>Astrology Reading — {result['full_name']}</title>
<style>
  body{{font-family:Georgia,serif;max-width:820px;margin:0 auto;padding:2rem;color:#1a1a2e;line-height:1.8}}
  h1{{color:#4a2d7a;border-bottom:2px solid #c8a8f8;padding-bottom:.5rem}}
  h2{{color:#6644aa;margin-top:2rem}}
  strong{{color:#4a2d7a}}
  .meta{{color:#666;font-style:italic;margin-bottom:2rem}}
  @media print{{body{{padding:1rem}}}}
</style></head>
<body>
<h1>Natal Chart Reading for {result['full_name']}</h1>
<p class="meta">Born {result['parsed_dob']} · {result['birth_location']} · Reading as of {result['parsed_current_datetime']}</p>
{_chart_svg_block}
{_report_html_body}
</body></html>"""

        from export.pdf import natal_pdf as _natal_pdf
        _safe_name = result["full_name"].replace(" ", "_")
        dl_col1, dl_col2, dl_col3 = st.columns(3)
        with dl_col1:
            st.download_button(
                label="Download as Markdown",
                data=result["final_report"],
                file_name=f"reading_{_safe_name}.md",
                mime="text/markdown",
            )
        with dl_col2:
            st.download_button(
                label="Download as HTML",
                data=_html_export,
                file_name=f"reading_{_safe_name}.html",
                mime="text/html",
            )
        with dl_col3:
            try:
                # Pass _cd1 so the PDF gets SVGs whether freshly generated or
                # regenerated after loading from the database (which strips SVGs).
                _pdf_bytes = _natal_pdf({**result, "chart_data": _cd1})
                st.download_button(
                    label="Download as PDF",
                    data=_pdf_bytes,
                    file_name=f"reading_{_safe_name}.pdf",
                    mime="application/pdf",
                )
            except Exception:
                st.caption("PDF export unavailable")

        # Save reading
        _save_col, _ = st.columns([1, 3])
        with _save_col:
            if st.button("💾 Save Reading", key="save_natal", use_container_width=True):
                save_natal(result)
                st.session_state._save_toast = "Reading saved — find it under My Saved Charts in the sidebar."
                st.rerun()

        # Follow-up chat
        st.markdown("""
<div class="chat-section-header">
  <p>Ask a Follow-up Question</p>
  <small>Ask anything about your chart, placements, timing, or specific guidance.</small>
</div>
""", unsafe_allow_html=True)

        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        question = st.chat_input("e.g. What does my Saturn placement mean for my career?")
        if question:
            st.session_state.chat_history.append({"role": "user", "content": question})
            with st.chat_message("user"):
                st.markdown(question)

            with st.chat_message("assistant"):
                answer = st.write_stream(
                    answer_followup_stream(result, st.session_state.chat_history, question)
                )

            st.session_state.chat_history.append({"role": "assistant", "content": answer})
            st.rerun()

    else:
        st.markdown("""
        <div class="placeholder-panel">
          <div class="astro-glyph">☽ ☉ ↑</div>
          <h3>Your Reading Awaits</h3>
          <p>Enter your birth details in the sidebar<br>and click <strong>Generate My Reading</strong> to begin.</p>
        </div>
        """, unsafe_allow_html=True)

_PLANET_COLORS = {
    "jupiter": "#44bb88",
    "saturn":  "#aaaacc",
    "uranus":  "#66ccdd",
    "neptune": "#7788dd",
    "pluto":   "#cc6677",
}
_ASPECT_SYMBOLS = {
    "Conjunction": "☌", "Sextile": "✶", "Trine": "△",
    "Square": "□", "Opposition": "☍",
}


def _render_transit_timeline(transit_passes: list[dict]) -> None:
    """Gantt-style plotly chart showing 12-month outer-planet transit passes."""
    if not transit_passes:
        st.info("Transit timeline data not available. Click **↺ Regenerate Reading** in the My Reading tab to recompute your chart with timing data.")
        return

    try:
        import plotly.graph_objects as go
        from datetime import date as _date, timedelta
    except ImportError:
        st.caption("Install plotly to view the timeline chart.")
        return

    today = _date.today()
    rows = []
    for p in transit_passes:
        tp = p.get("transiting_planet", "")
        np_ = p.get("natal_planet", "").replace("_", " ").title()
        aspect = p.get("aspect", "")
        passes = p.get("passes") or []
        if not passes:
            continue
        try:
            start = _date.fromisoformat(passes[0]["date"])
            end = _date.fromisoformat(passes[-1]["date"]) if len(passes) > 1 else start + timedelta(days=14)
        except (KeyError, ValueError):
            continue
        sym = _ASPECT_SYMBOLS.get(aspect, "·")
        label = f"{tp.capitalize()} {sym} {np_}"
        multi = len(passes) > 1
        rows.append({
            "label": label,
            "start": start,
            "end": end,
            "planet": tp,
            "multi": multi,
            "passes": len(passes),
        })

    if not rows:
        st.caption("No transit pass dates available to plot.")
        return

    rows.sort(key=lambda r: r["start"])

    fig = go.Figure()
    for i, r in enumerate(rows):
        color = _PLANET_COLORS.get(r["planet"], "#9988bb")
        width = 18 if r["multi"] else 10
        hover = (
            f"<b>{r['label']}</b><br>"
            f"{'Multi-pass (' + str(r['passes']) + ' exact contacts)' if r['multi'] else 'Single pass'}<br>"
            f"First exact: {r['start']}<br>"
            + (f"Last exact: {r['end']}" if r["multi"] else "")
        )
        fig.add_trace(go.Bar(
            x=[r["end"].isoformat()],
            y=[r["label"]],
            base=[r["start"].isoformat()],
            orientation="h",
            marker_color=color,
            marker_line_color=color,
            marker_opacity=0.85,
            width=width,
            hovertemplate=hover + "<extra></extra>",
            showlegend=False,
        ))

    fig.add_shape(
        type="line",
        x0=today.isoformat(), x1=today.isoformat(),
        y0=0, y1=1,
        xref="x", yref="paper",
        line=dict(color="#ffffff", width=1, dash="dot"),
        opacity=0.4,
    )
    fig.add_annotation(
        x=today.isoformat(), y=1,
        xref="x", yref="paper",
        text="Today", showarrow=False,
        font=dict(color="#ccbbee", size=11),
        xanchor="left", yanchor="bottom",
    )

    fig.update_layout(
        height=max(250, len(rows) * 32 + 80),
        margin=dict(l=0, r=20, t=20, b=40),
        paper_bgcolor="#12122a",
        plot_bgcolor="#12122a",
        font=dict(color="#e0d4fc", family="Georgia, serif", size=12),
        xaxis=dict(
            type="date",
            range=[today.isoformat(), (today + timedelta(days=365)).isoformat()],
            gridcolor="#2e2e4e",
            tickformat="%b %Y",
            tickcolor="#6655aa",
        ),
        yaxis=dict(gridcolor="#2e2e4e", autorange="reversed"),
        barmode="overlay",
    )
    st.plotly_chart(fig, width="stretch")


_ASPECT_NATURE = {
    "conjunction": ("neutral", "☌", "#7788dd"),
    "sextile":     ("harmonious", "✶", "#44bb88"),
    "trine":       ("harmonious", "△", "#44bb88"),
    "square":      ("challenging", "□", "#cc6644"),
    "opposition":  ("challenging", "☍", "#cc6644"),
}

_MONTH_NAMES = {
    "01": "January", "02": "February", "03": "March", "04": "April",
    "05": "May",     "06": "June",     "07": "July",  "08": "August",
    "09": "September", "10": "October", "11": "November", "12": "December",
}


def _render_calendar(calendar: dict[str, list[dict]]) -> None:
    if not calendar:
        st.info("No significant outer-planet transits found in this window.")
        return
    for month_key, events in calendar.items():
        year, mo = month_key.split("-")
        st.markdown(f"#### {_MONTH_NAMES.get(mo, mo)} {year}")
        rows = []
        for e in events:
            nature, symbol, color = _ASPECT_NATURE.get(e["aspect"], ("neutral", "·", "#aaaaaa"))
            t_planet = e["transiting_planet"].capitalize()
            n_planet = e["natal_planet"].replace("_", " ").title()
            retro = " ℞" if e["retrograde"] else ""
            exact = e["exact_date"] or e["first_date"]
            rows.append(
                f'<tr>'
                f'<td style="color:#d4bfff;padding:4px 10px;">{t_planet}{retro}</td>'
                f'<td style="color:{color};text-align:center;padding:4px 8px;">{symbol} {e["aspect"].capitalize()}</td>'
                f'<td style="color:#c8c0b0;padding:4px 10px;">{n_planet}</td>'
                f'<td style="color:#9988bb;padding:4px 10px;">{exact}</td>'
                f'<td style="color:{color};padding:4px 10px;font-size:0.82rem;">{nature.capitalize()}</td>'
                f'</tr>'
            )
        table_html = (
            '<table style="width:100%;border-collapse:collapse;font-family:Georgia,serif;font-size:0.9rem;">'
            '<thead><tr>'
            '<th style="color:#9988bb;text-align:left;padding:4px 10px;border-bottom:1px solid #2e2e4e;">Planet</th>'
            '<th style="color:#9988bb;text-align:center;padding:4px 8px;border-bottom:1px solid #2e2e4e;">Aspect</th>'
            '<th style="color:#9988bb;text-align:left;padding:4px 10px;border-bottom:1px solid #2e2e4e;">Natal Point</th>'
            '<th style="color:#9988bb;text-align:left;padding:4px 10px;border-bottom:1px solid #2e2e4e;">~Date</th>'
            '<th style="color:#9988bb;text-align:left;padding:4px 10px;border-bottom:1px solid #2e2e4e;">Nature</th>'
            '</tr></thead><tbody>'
            + "".join(rows)
            + "</tbody></table>"
        )
        st.markdown(table_html, unsafe_allow_html=True)
        st.markdown("")


with weekly_tab:
    _result_for_weekly = st.session_state.report_result
    if not _result_for_weekly:
        st.info("Generate your natal reading first (My Reading tab), then come back here for your personalised weekly forecast.")
    else:
        _today_str = date.today().isoformat()
        _has_fresh_forecast = (
            st.session_state._weekly_forecast is not None
            and st.session_state._weekly_forecast_date == _today_str
        )

        st.markdown(
            f"### This Week's Forecast for {_result_for_weekly.get('full_name', 'You')}",
            unsafe_allow_html=False,
        )
        st.caption(f"Week of {_today_str} · Personalised from your natal chart")

        if _has_fresh_forecast:
            import markdown as _wmd
            _weekly_html = _wmd.markdown(st.session_state._weekly_forecast, extensions=["extra"])
            st.markdown(f'<div class="report-card">{_weekly_html}</div>', unsafe_allow_html=True)
            if st.button("🔄 Refresh Forecast", key="weekly_refresh"):
                st.session_state._weekly_forecast = None
                st.session_state._weekly_forecast_date = None
                st.rerun()
        else:
            if st.button("✨ Generate This Week's Forecast", key="weekly_generate", type="primary"):
                _weekly_state = {**_result_for_weekly}
                _weekly_state["parsed_current_datetime"] = datetime.now(pytz.UTC).isoformat()
                with st.spinner("Reading the week ahead... ✨"):
                    _weekly_chunks = list(generate_weekly_forecast_stream(_weekly_state))
                _weekly_text = "".join(_weekly_chunks)
                st.session_state._weekly_forecast = _weekly_text
                st.session_state._weekly_forecast_date = _today_str
                st.rerun()

with monthly_tab:
    _result_for_monthly = st.session_state.report_result
    if not _result_for_monthly:
        st.info("Generate your natal reading first (My Reading tab), then come back here for your personalised monthly forecast.")
    else:
        _this_month = date.today().strftime("%Y-%m")
        _has_fresh_monthly = (
            st.session_state._monthly_forecast is not None
            and st.session_state._monthly_forecast_month == _this_month
        )

        st.markdown(
            f"### {date.today().strftime('%B %Y')} Forecast for {_result_for_monthly.get('full_name', 'You')}",
            unsafe_allow_html=False,
        )
        st.caption(f"Personalised from your natal chart · Refreshes each calendar month")

        if _has_fresh_monthly:
            import markdown as _mmd
            _monthly_html = _mmd.markdown(st.session_state._monthly_forecast, extensions=["extra"])
            st.markdown(f'<div class="report-card">{_monthly_html}</div>', unsafe_allow_html=True)
            if st.button("🔄 Refresh Forecast", key="monthly_refresh"):
                st.session_state._monthly_forecast = None
                st.session_state._monthly_forecast_month = None
                st.rerun()
        else:
            if st.button("✨ Generate Monthly Forecast", key="monthly_generate", type="primary"):
                _monthly_state = {**_result_for_monthly}
                _monthly_state["parsed_current_datetime"] = datetime.now(pytz.UTC).isoformat()
                with st.spinner("Mapping the month ahead... ✨"):
                    _monthly_chunks = list(generate_monthly_forecast_stream(_monthly_state))
                _monthly_text = "".join(_monthly_chunks)
                st.session_state._monthly_forecast = _monthly_text
                st.session_state._monthly_forecast_month = _this_month
                st.rerun()

with yearly_tab:
    _result_for_yearly = st.session_state.report_result
    if not _result_for_yearly:
        st.info("Generate your natal reading first (My Reading tab), then come back here for your personalised annual forecast.")
    else:
        _this_year = str(date.today().year)
        _has_fresh_yearly = (
            st.session_state._yearly_forecast is not None
            and st.session_state._yearly_forecast_year == _this_year
        )

        st.markdown(
            f"### {_this_year} Annual Forecast for {_result_for_yearly.get('full_name', 'You')}",
            unsafe_allow_html=False,
        )
        st.caption(f"Personalised from your natal chart · Refreshes each calendar year")

        if _has_fresh_yearly:
            import markdown as _ymd
            _yearly_html = _ymd.markdown(st.session_state._yearly_forecast, extensions=["extra"])
            st.markdown(f'<div class="report-card">{_yearly_html}</div>', unsafe_allow_html=True)
            if st.button("🔄 Refresh Forecast", key="yearly_refresh"):
                st.session_state._yearly_forecast = None
                st.session_state._yearly_forecast_year = None
                st.rerun()
        else:
            if st.button("✨ Generate Annual Forecast", key="yearly_generate", type="primary"):
                _yearly_state = {**_result_for_yearly}
                _yearly_state["parsed_current_datetime"] = datetime.now(pytz.UTC).isoformat()
                with st.spinner("Charting your year ahead... ✨"):
                    _yearly_chunks = list(generate_yearly_forecast_stream(_yearly_state))
                _yearly_text = "".join(_yearly_chunks)
                st.session_state._yearly_forecast = _yearly_text
                st.session_state._yearly_forecast_year = _this_year
                st.rerun()

with overall_tab:
    _result_for_overall = st.session_state.report_result
    if not _result_for_overall:
        st.info("Generate your natal reading first (My Reading tab), then come back here for your comprehensive life-arc forecast.")
    else:
        _this_year_o = str(date.today().year)
        _has_fresh_overall = (
            st.session_state._overall_forecast is not None
            and st.session_state._overall_forecast_year == _this_year_o
        )

        st.markdown(
            f"### Overall Forecast for {_result_for_overall.get('full_name', 'You')}",
            unsafe_allow_html=False,
        )
        st.caption("A comprehensive synthesis across all time frames — now through the next 2–5 years · Refreshes each calendar year")

        if _has_fresh_overall:
            import markdown as _omd
            _overall_html = _omd.markdown(st.session_state._overall_forecast, extensions=["extra"])
            st.markdown(f'<div class="report-card">{_overall_html}</div>', unsafe_allow_html=True)
            if st.button("🔄 Refresh Forecast", key="overall_refresh"):
                st.session_state._overall_forecast = None
                st.session_state._overall_forecast_year = None
                st.rerun()
        else:
            if st.button("✨ Generate Overall Forecast", key="overall_generate", type="primary"):
                _overall_state = {**_result_for_overall}
                _overall_state["parsed_current_datetime"] = datetime.now(pytz.UTC).isoformat()
                with st.spinner("Synthesising your complete cosmic picture... ✨"):
                    _overall_chunks = list(generate_overall_forecast_stream(_overall_state))
                _overall_text = "".join(_overall_chunks)
                st.session_state._overall_forecast = _overall_text
                st.session_state._overall_forecast_year = _this_year_o
                st.rerun()

with calendar_tab:
    result_for_cal = st.session_state.report_result
    if not result_for_cal:
        st.markdown("""
        <div class="placeholder-panel">
          <div class="icon">🗓️</div>
          <p>Generate your natal reading first,<br>then view your 12-month transit calendar here.</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("### 📊 12-Month Transit Timeline")
        st.caption(
            "Each bar shows when an outer planet forms a major aspect to a natal point. "
            "Wider bars = multi-pass (retrograde) transits. Hover for exact dates."
        )
        _timeline_passes = (result_for_cal.get("chart_data") or {}).get("transit_passes") or []
        _render_transit_timeline(_timeline_passes)

        st.divider()
        st.markdown("### 🗓️ Month-by-Month Transit Calendar")
        st.caption(
            "Shows when Jupiter, Saturn, Uranus, Neptune, and Pluto form major aspects "
            "to your natal points over the next 12 months. ℞ = planet is retrograde."
        )

        _cal_key = st.session_state._chart_cache_key
        if (
            st.session_state._transit_calendar is not None
            and st.session_state._transit_calendar_key == _cal_key
        ):
            _render_calendar(st.session_state._transit_calendar)
        else:
            if st.button("Compute Transit Calendar ✨", type="primary"):
                _cd = result_for_cal.get("chart_data") or {}
                _cur_dt_str = result_for_cal.get("parsed_current_datetime") or ""
                try:
                    from datetime import datetime as _dt
                    _cur_dt = _dt.fromisoformat(_cur_dt_str)
                    _loc_parts = [p.strip() for p in (result_for_cal.get("current_location") or "London, UK").split(",")]
                    _city = _loc_parts[0]
                    _nation = _loc_parts[-1] if len(_loc_parts) > 1 else ""
                    with st.spinner("Scanning the skies for the next 12 months… ✨ (this may take ~30 seconds)"):
                        _cal = compute_transit_calendar(
                            natal_chart=_cd,
                            current_year=_cur_dt.year,
                            current_month=_cur_dt.month,
                            current_day=_cur_dt.day,
                            current_hour=_cur_dt.hour,
                            current_minute=_cur_dt.minute,
                            current_city=_city,
                            current_nation=_nation,
                        )
                    st.session_state._transit_calendar = _cal
                    st.session_state._transit_calendar_key = _cal_key
                    st.rerun()
                except Exception as _cal_exc:
                    st.error(f"Could not compute transit calendar: {_cal_exc}")
            else:
                st.caption("Click the button above to scan the next 12 months of transits for your chart.")


with synastry_tab:
    if not st.session_state.report_result:
        st.info(
            "Generate your natal reading first (sidebar → **Generate My Reading**), "
            "then return here to explore compatibility."
        )
    else:
        result_a = st.session_state.report_result
        chart_a = result_a.get("chart_data") or {}

        st.markdown("""
        <div style="padding:0.8rem 0 1rem;">
          <p style="color:#9988bb;font-style:italic;margin:0;">Enter a second person's birth details to receive a full synastry reading.</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(
            f"**Person A (You):** {result_a['full_name']} · {result_a['parsed_dob']} · {result_a['birth_location']}"
        )

        with st.form("synastry_form"):
            st.markdown("#### Person B — Birth Details")
            b_col1, b_col2 = st.columns(2)
            with b_col1:
                b_name = st.text_input("Full Name *", placeholder="e.g., John Smith", key="syn_name")
                b_dob = st.date_input(
                    "Date of Birth *", value=None,
                    min_value=date(1900, 1, 1), max_value=date.today(),
                    key="syn_dob",
                )
                b_birth_time = st.time_input("Birth Time *", value=None, step=60, key="syn_time")
            with b_col2:
                b_location = st.text_input(
                    "Birth Location *", placeholder="City, Region, Country", key="syn_loc"
                )
                b_timezone = st.selectbox(
                    "Birth Timezone *", options=ALL_TIMEZONES, index=DEFAULT_TZ_INDEX, key="syn_tz"
                )

            syn_submitted = st.form_submit_button(
                "Explore Compatibility ✨", type="primary", use_container_width=True
            )

        if syn_submitted:
            st.session_state.synastry_result = None
            st.session_state.synastry_chat_history = []
            st.session_state.synastry_error = None
            st.session_state._synastry_prepared = None

            b_errors = []
            if not b_name or not b_name.strip():
                b_errors.append("Full Name is required.")
            if not b_dob:
                b_errors.append("Date of Birth is required.")
            if not b_birth_time:
                b_errors.append("Birth Time is required.")
            if not b_location or not b_location.strip():
                b_errors.append("Birth Location is required.")

            if b_errors:
                for err in b_errors:
                    st.warning(err)
            else:
                _syn_cache_key = (
                    st.session_state._chart_cache_key,
                    (b_name or "").strip().lower(),
                    b_dob.strftime("%Y-%m-%d") if b_dob else None,
                    (b_location or "").strip().lower(),
                    b_birth_time.strftime("%H:%M") if b_birth_time else None,
                    b_timezone,
                )

                if (
                    _syn_cache_key == st.session_state._synastry_cache_key
                    and st.session_state._synastry_cache_prepared is not None
                ):
                    st.session_state._synastry_prepared = st.session_state._synastry_cache_prepared
                    st.info("Charts cached — regenerating synastry report.", icon="⚡")
                else:
                    try:
                        _tz_b = pytz.timezone(b_timezone)
                        _b_dt = _tz_b.localize(datetime(
                            b_dob.year, b_dob.month, b_dob.day,
                            b_birth_time.hour, b_birth_time.minute,
                        ))
                        b_parts = [p.strip() for p in b_location.split(",")]
                        b_city = b_parts[0]
                        b_nation = b_parts[-1] if len(b_parts) > 1 else ""

                        with st.spinner("Computing charts and synastry... ✨"):
                            chart_b = compute_chart(
                                full_name=b_name.strip(),
                                birth_year=_b_dt.year,
                                birth_month=_b_dt.month,
                                birth_day=_b_dt.day,
                                birth_hour=_b_dt.hour,
                                birth_minute=_b_dt.minute,
                                city=b_city,
                                nation=b_nation,
                                tz_str=b_timezone,
                                house_system=result_a.get("house_system") or "Placidus",
                            )
                            synastry = compute_synastry(chart_a, chart_b)

                        _syn_prep = {
                            "name_a": result_a["full_name"],
                            "dob_a": result_a["parsed_dob"],
                            "loc_a": result_a["birth_location"],
                            "chart_a": chart_a,
                            "name_b": b_name.strip(),
                            "dob_b": b_dob.strftime("%Y-%m-%d"),
                            "loc_b": b_location.strip(),
                            "chart_b": chart_b,
                            "synastry": synastry,
                        }
                        st.session_state._synastry_prepared = _syn_prep
                        st.session_state._synastry_cache_key = _syn_cache_key
                        st.session_state._synastry_cache_prepared = _syn_prep
                    except Exception as exc:
                        st.session_state.synastry_error = str(exc)

        if st.session_state.synastry_error:
            st.error(f"An error occurred: {st.session_state.synastry_error}")

        elif st.session_state._synastry_prepared:
            prep = st.session_state._synastry_prepared

            st.divider()
            s_col1, s_col2 = st.columns(2)
            with s_col1:
                st.metric("Person A", prep["name_a"])
                st.caption(f"{prep['dob_a']} · {prep['loc_a']}")
            with s_col2:
                st.metric("Person B", prep["name_b"])
                st.caption(f"{prep['dob_b']} · {prep['loc_b']}")
            st.divider()

            st.caption("✨ Drafting your compatibility reading (pass 1) → reviewing for accuracy (pass 2) → verifying facts against both charts (pass 3) — this takes ~30 seconds...")
            _syn_current_date = datetime.now(pytz.UTC).strftime("%Y-%m-%d")
            syn_report_text = st.write_stream(generate_synastry_report_stream(
                name_a=prep["name_a"], dob_a=prep["dob_a"], loc_a=prep["loc_a"], chart_a=prep["chart_a"],
                name_b=prep["name_b"], dob_b=prep["dob_b"], loc_b=prep["loc_b"], chart_b=prep["chart_b"],
                synastry=prep["synastry"],
                current_date=_syn_current_date,
            ))

            st.session_state.synastry_result = {**prep, "report": syn_report_text}
            st.session_state._synastry_prepared = None
            st.rerun()

        elif st.session_state.synastry_result:
            syn = st.session_state.synastry_result

            st.divider()
            s_col1, s_col2 = st.columns(2)
            with s_col1:
                st.metric("Person A", syn["name_a"])
                st.caption(f"{syn['dob_a']} · {syn['loc_a']}")
            with s_col2:
                st.metric("Person B", syn["name_b"])
                st.caption(f"{syn['dob_b']} · {syn['loc_b']}")
            st.divider()

            # Synastry downloads
            import markdown as _md2
            _syn_html_body = _md2.markdown(syn["report"], extensions=["extra"])
            st.markdown(
                f'<div class="report-card">{_syn_html_body}</div>',
                unsafe_allow_html=True,
            )

            _syn_html = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<title>Synastry — {syn['name_a']} &amp; {syn['name_b']}</title>
<style>
  body{{font-family:Georgia,serif;max-width:820px;margin:0 auto;padding:2rem;color:#1a1a2e;line-height:1.8}}
  h1{{color:#4a2d7a;border-bottom:2px solid #c8a8f8;padding-bottom:.5rem}}
  h2{{color:#6644aa;margin-top:2rem}}
  strong{{color:#4a2d7a}}
  .meta{{color:#666;font-style:italic;margin-bottom:2rem}}
</style></head>
<body>
<h1>Synastry: {syn['name_a']} &amp; {syn['name_b']}</h1>
<p class="meta">{syn['name_a']} ({syn['dob_a']}, {syn['loc_a']}) · {syn['name_b']} ({syn['dob_b']}, {syn['loc_b']})</p>
{_syn_html_body}
</body></html>"""

            from export.pdf import synastry_pdf as _synastry_pdf
            _syn_safe = f"synastry_{syn['name_a'].replace(' ', '_')}_{syn['name_b'].replace(' ', '_')}"
            syn_dl1, syn_dl2, syn_dl3 = st.columns(3)
            with syn_dl1:
                st.download_button(
                    label="Download as Markdown",
                    data=syn["report"],
                    file_name=f"{_syn_safe}.md",
                    mime="text/markdown",
                )
            with syn_dl2:
                st.download_button(
                    label="Download as HTML",
                    data=_syn_html,
                    file_name=f"{_syn_safe}.html",
                    mime="text/html",
                )
            with syn_dl3:
                try:
                    _syn_pdf_bytes = _synastry_pdf(syn)
                    st.download_button(
                        label="Download as PDF",
                        data=_syn_pdf_bytes,
                        file_name=f"{_syn_safe}.pdf",
                        mime="application/pdf",
                    )
                except Exception:
                    st.caption("PDF export unavailable")

            # Save synastry
            _syn_save_col, _ = st.columns([1, 3])
            with _syn_save_col:
                if st.button("💾 Save Reading", key="save_synastry", use_container_width=True):
                    save_synastry(syn)
                    st.session_state._save_toast = "Compatibility reading saved — find it under My Saved Charts in the sidebar."
                    st.rerun()

            # Synastry follow-up chat
            st.divider()
            st.subheader("💬 Ask About Your Compatibility")
            st.caption("Ask anything about your synastry, shared themes, or relationship timing.")

            for msg in st.session_state.synastry_chat_history:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

            syn_question = st.chat_input(
                "e.g. What does our Venus-Mars conjunction mean for romance?",
                key="syn_chat",
            )
            if syn_question:
                st.session_state.synastry_chat_history.append({"role": "user", "content": syn_question})
                with st.chat_message("user"):
                    st.markdown(syn_question)

                with st.chat_message("assistant"):
                    syn_answer = st.write_stream(
                        answer_synastry_followup_stream(
                            name_a=syn["name_a"], dob_a=syn["dob_a"], chart_a=syn["chart_a"],
                            name_b=syn["name_b"], dob_b=syn["dob_b"], chart_b=syn["chart_b"],
                            synastry=syn["synastry"], synastry_report=syn["report"],
                            chat_history=st.session_state.synastry_chat_history,
                            question=syn_question,
                        )
                    )

                st.session_state.synastry_chat_history.append({"role": "assistant", "content": syn_answer})
                st.rerun()
