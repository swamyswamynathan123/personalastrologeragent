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
    layout="centered",
)

st.title("⭐ Personal Astrologer Agent")
st.markdown(
    "Enter your birth details to receive a personalized, time-aware astrological reading."
)

# --- Session state initialisation ---
if "report_result" not in st.session_state:
    st.session_state.report_result = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "validation_message" not in st.session_state:
    st.session_state.validation_message = None

ALL_TIMEZONES = pytz.all_timezones
DEFAULT_TZ_INDEX = ALL_TIMEZONES.index("UTC")

with st.form("astro_form"):
    st.subheader("Your Birth Details")
    col1, col2 = st.columns(2)

    with col1:
        full_name = st.text_input("Full Name *", placeholder="e.g., Jane Doe")
        dob = st.date_input(
            "Date of Birth *",
            value=None,
            min_value=date(1900, 1, 1),
            max_value=date.today(),
        )
        birth_time = st.time_input("Birth Time *", value=None, step=60)

    with col2:
        birth_location = st.text_input(
            "Birth Location * (City, Region, Country)",
            placeholder="e.g., Mumbai, Maharashtra, India",
        )
        birth_time_timezone = st.selectbox(
            "Birth Timezone *",
            options=ALL_TIMEZONES,
            index=DEFAULT_TZ_INDEX,
            help="Select the timezone for your birth location",
        )
        current_location = st.text_input(
            "Current Location * (City, Region, Country)",
            placeholder="e.g., New York, NY, USA",
        )

    st.subheader("Optional Details")
    report_focus = st.text_input(
        "Report Focus",
        placeholder="e.g., Career, relationships, spiritual growth",
    )
    additional_info = st.text_area(
        "Additional Context",
        placeholder="Share any life events or questions you'd like the reading to address...",
        height=100,
    )

    submitted = st.form_submit_button("Generate My Reading ⭐", type="primary")

# --- Form submission: run the graph ---
if submitted:
    # Reset previous session on new submission
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
        st.error("An unexpected error occurred. Please try again.")

# --- Show validation message ---
if st.session_state.validation_message:
    st.warning("Action Required")
    st.markdown(st.session_state.validation_message)

# --- Show report and chat ---
if st.session_state.report_result:
    result = st.session_state.report_result

    st.success("Your personalized reading is ready!")
    st.divider()

    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.metric("Name", result["full_name"])
    with col_b:
        st.metric("Date of Birth", result["parsed_dob"])
    with col_c:
        st.metric("Birth Location", result["birth_location"])

    st.caption(f"Reading generated as of: {result['parsed_current_datetime']}")
    st.divider()

    st.markdown(result["final_report"])

    # --- Follow-up chat ---
    st.divider()
    st.subheader("💬 Ask a follow-up question")
    st.caption("Ask anything about your chart, placements, timing, or guidance.")

    # Render existing chat history
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Chat input
    question = st.chat_input("e.g. What does my Saturn placement mean for my career?")
    if question:
        # Show user message immediately
        with st.chat_message("user"):
            st.markdown(question)

        # Get astrologer response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                answer = answer_followup(
                    result,
                    st.session_state.chat_history,
                    question,
                )
            st.markdown(answer)

        # Persist to history
        st.session_state.chat_history.append({"role": "user", "content": question})
        st.session_state.chat_history.append({"role": "assistant", "content": answer})
