from __future__ import annotations
from datetime import datetime, date

import pytz
import streamlit as st
from dotenv import load_dotenv

from agent.graph import graph
from agent.state import AstrologerState
from llm.report import answer_followup

load_dotenv()

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
}
.stChatInputContainer textarea {
    background: #1e1e38 !important;
    border: 1px solid #3a3a60 !important;
    color: #e8e0d0 !important;
    border-radius: 8px !important;
}

/* ── Alert / info boxes ──────────────────────────────────────────── */
[data-testid="stAlert"] {
    border-radius: 8px;
}

/* ── Divider ─────────────────────────────────────────────────────── */
hr { border-color: #2e2e4e; }

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

ALL_TIMEZONES = pytz.all_timezones
DEFAULT_TZ_INDEX = ALL_TIMEZONES.index("UTC")

# ── Sidebar: input form ───────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⭐ Your Details")

    with st.form("astro_form"):
        st.markdown("#### Birth Information")
        full_name = st.text_input("Full Name *", placeholder="e.g., Jane Doe")
        dob = st.date_input(
            "Date of Birth *",
            value=None,
            min_value=date(1900, 1, 1),
            max_value=date.today(),
        )
        birth_time = st.time_input("Birth Time *", value=None, step=60)
        birth_location = st.text_input(
            "Birth Location *",
            placeholder="City, Region, Country",
        )
        birth_time_timezone = st.selectbox(
            "Birth Timezone *",
            options=ALL_TIMEZONES,
            index=DEFAULT_TZ_INDEX,
        )
        current_location = st.text_input(
            "Current Location *",
            placeholder="City, Region, Country",
        )

        st.markdown("#### Optional")
        report_focus = st.text_input(
            "Report Focus",
            placeholder="Career, relationships, spiritual growth…",
        )
        additional_info = st.text_area(
            "Additional Context",
            placeholder="Life events or questions to address…",
            height=100,
        )

        submitted = st.form_submit_button(
            "Generate My Reading ⭐",
            type="primary",
            use_container_width=True,
        )

# --- Form submission: run the graph ---
if submitted:
    st.session_state.report_result = None
    st.session_state.chat_history = []
    st.session_state.validation_message = None

    payload: AstrologerState = {
        "full_name": full_name.strip() if full_name else None,
        "dob": dob.strftime("%Y-%m-%d") if dob else None,
        "birth_location": birth_location.strip() if birth_location else None,
        "birth_time": birth_time.strftime("%H:%M") if birth_time else None,
        "birth_time_timezone": birth_time_timezone,
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

    with st.spinner("Consulting the stars... ✨"):
        result = graph.invoke(payload)

    if result.get("follow_up_message"):
        st.session_state.validation_message = result["follow_up_message"]
    elif result.get("final_report"):
        st.session_state.report_result = result
    else:
        st.session_state.validation_message = "__error__"

# ── Main area: output ─────────────────────────────────────────────────────────
st.markdown("""
<div class="page-header">
  <h1>⭐ Personal Astrologer</h1>
  <p>A personalized natal chart reading powered by AI</p>
</div>
""", unsafe_allow_html=True)

if st.session_state.validation_message == "__error__":
    st.error("An unexpected error occurred. Please try again.")

elif st.session_state.validation_message:
    st.warning("Please correct the following before your reading can be generated:")
    st.markdown(st.session_state.validation_message)

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
    st.divider()

    # Report rendered in a styled card
    st.markdown(
        f'<div class="report-card">{result["final_report"]}</div>',
        unsafe_allow_html=True,
    )

    # Download button
    st.download_button(
        label="Download Reading",
        data=result["final_report"],
        file_name=f"reading_{result['full_name'].replace(' ', '_')}.md",
        mime="text/markdown",
    )

    # Follow-up chat
    st.divider()
    st.subheader("💬 Ask a Follow-up Question")
    st.caption("Ask anything about your chart, placements, timing, or guidance.")

    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    question = st.chat_input("e.g. What does my Saturn placement mean for my career?")
    if question:
        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                answer = answer_followup(
                    result,
                    st.session_state.chat_history,
                    question,
                )
            st.markdown(answer)

        st.session_state.chat_history.append({"role": "user", "content": question})
        st.session_state.chat_history.append({"role": "assistant", "content": answer})

else:
    st.markdown("""
    <div class="placeholder-panel">
      <div class="icon">🔭</div>
      <p>Fill in your birth details in the sidebar<br>and click <strong>Generate My Reading</strong> to begin.</p>
    </div>
    """, unsafe_allow_html=True)
