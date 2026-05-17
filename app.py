from __future__ import annotations
from datetime import datetime, date

import pytz
import streamlit as st
from dotenv import load_dotenv

from agent.graph import graph, prepare_graph
from agent.state import AstrologerState
from llm.report import answer_followup_stream, generate_report_stream, generate_synastry_report_stream, answer_synastry_followup_stream
from astro.compute import compute_chart, compute_synastry, compute_transit_calendar
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
/* ── Global typography ───────────────────────────────────────────── */
html, body, [class*="css"] {
    font-family: "Georgia", "Times New Roman", serif;
}

/* Page background */
.stApp {
    background-color: #0f0f1a;
    color: #e8e0d0;
}

/* ── Sidebar ─────────────────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background-color: #16162a;
    border-right: 1px solid #2e2e4e;
}
[data-testid="stSidebar"] .stForm {
    background: transparent;
}
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] .stTextInput label,
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stDateInput label,
[data-testid="stSidebar"] .stTimeInput label,
[data-testid="stSidebar"] .stTextArea label {
    color: #c8b8e8 !important;
    font-size: 0.82rem;
    letter-spacing: 0.04em;
    text-transform: uppercase;
}
[data-testid="stSidebar"] input,
[data-testid="stSidebar"] select,
[data-testid="stSidebar"] textarea {
    background-color: #1e1e38 !important;
    border: 1px solid #3a3a60 !important;
    color: #e8e0d0 !important;
    border-radius: 6px !important;
}
[data-testid="stSidebar"] input:focus,
[data-testid="stSidebar"] textarea:focus {
    border-color: #8866cc !important;
    box-shadow: 0 0 0 2px rgba(136,102,204,0.25) !important;
}
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] h4,
[data-testid="stSidebar"] h5,
[data-testid="stSidebar"] h6 {
    color: #d4bfff !important;
}

/* ── Primary button ──────────────────────────────────────────────── */
.stButton > button[kind="primary"],
.stFormSubmitButton > button[kind="primary"] {
    background: linear-gradient(135deg, #6644aa 0%, #9966cc 100%);
    border: none;
    color: #fff;
    font-family: "Georgia", serif;
    letter-spacing: 0.06em;
    border-radius: 8px;
    padding: 0.55rem 1.2rem;
    transition: opacity 0.2s ease;
}
.stButton > button[kind="primary"]:hover,
.stFormSubmitButton > button[kind="primary"]:hover {
    opacity: 0.88;
}

/* ── Secondary / default buttons ─────────────────────────────────── */
.stButton > button[kind="secondary"] {
    background: #1e1e38 !important;
    border: 1px solid #3a3a60 !important;
    color: #d4bfff !important;
    font-family: "Georgia", serif;
    border-radius: 8px;
    transition: background 0.2s ease, border-color 0.2s ease;
}
.stButton > button[kind="secondary"]:hover {
    background: #2a2a50 !important;
    border-color: #8866cc !important;
    color: #e8d8ff !important;
}

/* ── Page header ─────────────────────────────────────────────────── */
.page-header {
    padding: 2rem 0 1.2rem;
    border-bottom: 1px solid #2e2e4e;
    margin-bottom: 1.6rem;
}
.page-header h1 {
    margin: 0;
    font-size: 2.2rem;
    color: #d4bfff;
    letter-spacing: 0.02em;
}
.page-header p {
    margin: 0.4rem 0 0;
    color: #9988bb;
    font-style: italic;
    font-size: 1rem;
}

/* ── Report card ─────────────────────────────────────────────────── */
.report-card {
    background: #16162a;
    border: 1px solid #2e2e4e;
    border-radius: 12px;
    padding: 2rem 2.4rem;
    margin-bottom: 1.5rem;
    line-height: 1.85;
    color: #e8e0d0;
}
.report-card h2 {
    color: #c8a8f8;
    font-size: 1.15rem;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    border-bottom: 1px solid #2e2e4e;
    padding-bottom: 0.5rem;
    margin-top: 1.6rem;
}
.report-card h2:first-child { margin-top: 0; }
.report-card strong { color: #d4bfff; }
.report-card li { margin-bottom: 0.3rem; }

/* ── Metric cards ────────────────────────────────────────────────── */
[data-testid="stMetric"] {
    background: #1e1e38;
    border: 1px solid #2e2e4e;
    border-radius: 10px;
    padding: 0.9rem 1rem;
}
[data-testid="stMetricLabel"] { color: #9988bb !important; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; }
[data-testid="stMetricValue"] { color: #d4bfff !important; font-size: 1.1rem; }

/* ── Chat ────────────────────────────────────────────────────────── */
[data-testid="stChatMessage"] {
    background: #1e1e38;
    border: 1px solid #2e2e4e;
    border-radius: 10px;
    margin-bottom: 0.5rem;
    color: #e8e0d0 !important;
}
[data-testid="stChatMessage"] p,
[data-testid="stChatMessage"] li,
[data-testid="stChatMessage"] span,
[data-testid="stChatMessage"] div {
    color: #e8e0d0 !important;
}
[data-testid="stChatMessage"] strong {
    color: #d4bfff !important;
}
[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] {
    color: #e8e0d0 !important;
}
.stChatInputContainer textarea {
    background: #1e1e38 !important;
    border: 1px solid #3a3a60 !important;
    color: #e8e0d0 !important;
    border-radius: 8px !important;
}

/* ── Download buttons ────────────────────────────────────────────── */
[data-testid="stDownloadButton"] > button {
    background: #1e1e38 !important;
    border: 1px solid #3a3a60 !important;
    color: #d4bfff !important;
    border-radius: 8px;
    transition: background 0.2s ease, border-color 0.2s ease;
}
[data-testid="stDownloadButton"] > button:hover {
    background: #2a2a50 !important;
    border-color: #8866cc !important;
    color: #e8d8ff !important;
}

/* ── Alert / info boxes ──────────────────────────────────────────── */
[data-testid="stAlert"] {
    border-radius: 8px;
}

/* ── Tabs ────────────────────────────────────────────────────────── */
[data-testid="stTabs"] [data-baseweb="tab"] {
    color: #9988bb !important;
    background: transparent;
    border-bottom: 2px solid transparent;
}
[data-testid="stTabs"] [data-baseweb="tab"]:hover {
    color: #d4bfff !important;
}
[data-testid="stTabs"] [data-baseweb="tab"][aria-selected="true"] {
    color: #d4bfff !important;
    border-bottom: 2px solid #8866cc !important;
}
[data-testid="stTabs"] [data-baseweb="tab-list"] {
    border-bottom: 1px solid #2e2e4e;
    gap: 0.5rem;
}

/* ── Divider ─────────────────────────────────────────────────────── */
hr { border-color: #2e2e4e; }

/* ── Expanders ───────────────────────────────────────────────────── */
[data-testid="stExpander"] summary {
    color: #c8b8e8 !important;
    font-family: "Georgia", serif;
}
[data-testid="stExpander"] summary:hover {
    color: #d4bfff !important;
}
[data-testid="stExpander"] {
    border: 1px solid #2e2e4e !important;
    border-radius: 8px !important;
    background: #1e1e38 !important;
}
[data-testid="stExpander"] p,
[data-testid="stExpander"] span,
[data-testid="stExpander"] div,
[data-testid="stExpander"] small,
[data-testid="stExpander"] label {
    color: #c8c0b0 !important;
}
[data-testid="stExpander"] strong {
    color: #d4bfff !important;
}

/* ── Placeholder panel ───────────────────────────────────────────── */
.placeholder-panel {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 60vh;
    color: #555577;
    text-align: center;
    gap: 0.6rem;
}
.placeholder-panel .icon { font-size: 3.5rem; }
.placeholder-panel p { font-style: italic; margin: 0; }
</style>
""", unsafe_allow_html=True)

# --- Session state initialisation ---
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
    """Render an SVG string as a responsive image via base64 data URL."""
    import base64
    b64 = base64.b64encode(svg.encode("utf-8")).decode("utf-8")
    st.markdown(
        f'<div style="background:#fff;border-radius:12px;padding:1rem;">'
        f'<img src="data:image/svg+xml;base64,{b64}" '
        f'style="width:100%;height:auto;display:block;" /></div>',
        unsafe_allow_html=True,
    )

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
    st.markdown("## ⭐ Your Details")

    with st.form("astro_form"):
        st.markdown("#### Birth Information")
        full_name = st.text_input("Full Name *", placeholder="e.g., Jane Doe", key="f_full_name")
        dob = st.date_input(
            "Date of Birth *",
            value=None,
            min_value=date(1900, 1, 1),
            max_value=date.today(),
            key="f_dob",
        )
        birth_time = st.time_input("Birth Time *", value=None, step=60, key="f_birth_time")
        birth_time_confidence = st.selectbox(
            "Birth Time Confidence",
            options=["exact", "approximate", "unknown"],
            index=0,
            key="f_birth_time_confidence",
            help="How certain are you of the birth time? Approximate/unknown softens house-based interpretations.",
        )
        birth_location = st.text_input(
            "Birth Location *",
            placeholder="City, Region, Country",
            key="f_birth_location",
        )
        birth_time_timezone = st.selectbox(
            "Birth Timezone *",
            options=ALL_TIMEZONES,
            index=DEFAULT_TZ_INDEX,
            key="f_birth_time_timezone",
        )
        house_system = st.selectbox(
            "House System",
            options=["Placidus", "Whole Sign", "Koch"],
            index=0,
            key="f_house_system",
            help="Placidus is standard Western. Whole Sign is used in Hellenistic & Vedic traditions. Koch is popular in German-speaking countries.",
        )
        current_location = st.text_input(
            "Current Location *",
            placeholder="City, Region, Country",
            key="f_current_location",
        )

        st.markdown("#### Optional")
        additional_info = st.text_area(
            "Additional Context",
            placeholder="Life events or questions to address…",
            height=100,
            key="f_additional_info",
        )

        st.markdown("#### Report Focus")
        _focus_selections = st.pills(
            "Report Focus",
            options=_FOCUS_OPTIONS,
            selection_mode="multi",
            key="f_report_focus",
            label_visibility="collapsed",
        )
        report_focus = ", ".join(_focus_selections) if _focus_selections else None
        if report_focus:
            st.caption(f"Selected: {report_focus}")

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

        with st.spinner("Computing your chart... ✨"):
            prepared = prepare_graph.invoke(payload)

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
  <h1>⭐ Personal Astrologer</h1>
  <p>A personalized natal chart reading powered by AI</p>
</div>
""", unsafe_allow_html=True)

if st.session_state._save_toast:
    st.success(st.session_state._save_toast)
    st.session_state._save_toast = None

natal_tab, calendar_tab, synastry_tab = st.tabs(["My Reading", "Transit Calendar", "Compatibility / Synastry"])

with natal_tab:
    if st.session_state.validation_message == "__error__":
        st.error("An unexpected error occurred. Please try again.")

    elif st.session_state.validation_message:
        st.warning("Please correct the following before your reading can be generated:")
        st.markdown(st.session_state.validation_message)

    elif st.session_state._prepared_state:
        prepared = st.session_state._prepared_state

        # Metadata strip
        col_a, col_b, col_c, col_d = st.columns(4)
        with col_a:
            st.metric("Name", prepared["full_name"])
        with col_b:
            st.metric("Date of Birth", prepared["parsed_dob"])
        with col_c:
            st.metric("Birth Location", prepared["birth_location"])
        with col_d:
            st.metric("Current Location", prepared["current_location"])

        st.caption(f"Reading generated as of {prepared['parsed_current_datetime']}")
        if prepared.get("report_focus"):
            st.caption(f"Focus: {prepared['report_focus']}")
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
                st.caption("✨ Drafting your reading (pass 1) → reviewing for consistency (pass 2) → verifying facts against your chart (pass 3) — this takes ~30 seconds...")
                report_text = st.write_stream(generate_report_stream(prepared))
                st.session_state.report_result = {**prepared, "final_report": report_text}
                st.session_state._prepared_state = None
                st.rerun()
            except Exception as exc:
                st.session_state._stream_error = str(exc)
                st.rerun()

    elif st.session_state.report_result:
        result = st.session_state.report_result

        # Metadata strip
        col_a, col_b, col_c, col_d = st.columns(4)
        with col_a:
            st.metric("Name", result["full_name"])
        with col_b:
            st.metric("Date of Birth", result["parsed_dob"])
        with col_c:
            st.metric("Birth Location", result["birth_location"])
        with col_d:
            st.metric("Current Location", result["current_location"])

        st.caption(f"Reading generated as of {result['parsed_current_datetime']}")
        if result.get("report_focus"):
            st.caption(f"Focus: {result['report_focus']}")
        st.divider()

        # Chart wheels (natal + transit overlay)
        _cd1 = result.get("chart_data") or {}
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
                _pdf_bytes = _natal_pdf(result)
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
        st.divider()
        st.subheader("💬 Ask a Follow-up Question")
        st.caption("Ask anything about your chart, placements, timing, or guidance.")

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
          <div class="icon">🔭</div>
          <p>Fill in your birth details in the sidebar<br>and click <strong>Generate My Reading</strong> to begin.</p>
        </div>
        """, unsafe_allow_html=True)

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
        st.markdown("### 🗓️ 12-Month Outer-Planet Transit Calendar")
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
