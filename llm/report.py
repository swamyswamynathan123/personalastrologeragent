from __future__ import annotations
import os
from typing import TYPE_CHECKING

import openai
from dotenv import load_dotenv

if TYPE_CHECKING:
    from agent.state import AstrologerState

load_dotenv()


def _format_planet(label: str, data: dict | None) -> str:
    if not data:
        return f"- {label}: data unavailable"
    retro = " (retrograde)" if data.get("retrograde") else ""
    house = f", House {data['house']}" if data.get("house") else ""
    return f"- {label}: {data['sign']} {data['position']}°{retro}{house}"


def _format_aspects(aspects: list[dict]) -> str:
    if not aspects:
        return "No major natal aspects computed."
    lines = []
    for a in aspects:
        p1 = a["planet1"].capitalize()
        p2 = a["planet2"].capitalize()
        lines.append(f"- {p1} {a['aspect']} {p2} (orb {a['orb']}°)")
    return "\n".join(lines)


def _format_transits(transits: list[dict]) -> str:
    if not transits:
        return "No significant transits active right now (within 3° orb)."
    lines = []
    for t in transits:
        tp = t["transiting_planet"].capitalize()
        np_ = t["natal_planet"].capitalize()
        lines.append(f"- Transiting {tp} {t['aspect']} natal {np_} (orb {t['orb']}°)")
    return "\n".join(lines)


def build_prompt(state: "AstrologerState") -> str:
    chart = state.get("chart_data") or {}
    focus = state.get("report_focus") or "general life reading"
    additional = state.get("additional_info") or ""

    chart_section = ""
    if chart:
        placements = [
            "## Natal Chart Placements",
            _format_planet("Sun", chart.get("sun")),
            _format_planet("Moon", chart.get("moon")),
            f"- Ascendant: {chart['ascendant']['sign']} {chart['ascendant']['position']}°" if chart.get("ascendant") else "- Ascendant: unavailable",
            f"- Midheaven: {chart['midheaven']['sign']} {chart['midheaven']['position']}°" if chart.get("midheaven") else "- Midheaven: unavailable",
            _format_planet("Mercury", chart.get("mercury")),
            _format_planet("Venus", chart.get("venus")),
            _format_planet("Mars", chart.get("mars")),
            _format_planet("Jupiter", chart.get("jupiter")),
            _format_planet("Saturn", chart.get("saturn")),
            _format_planet("Uranus", chart.get("uranus")),
            _format_planet("Neptune", chart.get("neptune")),
            _format_planet("Pluto", chart.get("pluto")),
        ]
        aspects_section = ["", "## Natal Aspects", _format_aspects(chart.get("aspects") or [])]
        transits_section = ["", "## Current Transits (as of report date)", _format_transits(chart.get("transits") or [])]
        chart_section = "\n".join(placements + aspects_section + transits_section)
    else:
        chart_section = "## Natal Chart\nChart computation was unavailable. Base interpretations on Sun sign and general astrology."

    additional_section = f"\n**Additional Context from User:** {additional}" if additional else ""

    return f"""You are a professional, empathetic, and highly knowledgeable astrologer.

Generate a comprehensive, personalized astrological reading for the person below.
Only use the chart data provided — do NOT invent placements, transits, or aspects not listed here.

## Person Details
- **Full Name:** {state['full_name']}
- **Date of Birth:** {state['parsed_dob']}
- **Birth Location:** {state['birth_location']}
- **Birth Time:** {state['birth_time']} ({state.get('birth_time_timezone', 'timezone not specified')})
- **Current Location:** {state['current_location']}
- **Report Generated As Of:** {state['parsed_current_datetime']}
- **Report Focus:** {focus}
{additional_section}

{chart_section}

## Instructions
Write the report in clear, friendly, professional language. Structure it with these sections:
1. **Personal Overview** — Core personality traits from Sun, Moon, and Ascendant placements
2. **Current Cosmic Climate** — What the skies say for this person right now, based on the report date
3. **Key Life Themes** — 3–4 dominant themes active in their chart at this time
4. **Practical Guidance** — Specific, actionable advice for the coming weeks
5. **Favorable Timing** — Suggest favorable days or periods in the near future based on their chart

Tone: warm, empowering, specific to this individual. Do not make vague generalizations.
"""


def answer_followup(state: "AstrologerState", chat_history: list[dict], question: str) -> str:
    client = openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"])

    chart = state.get("chart_data") or {}
    if chart:
        placements = "\n".join([
            _format_planet("Sun", chart.get("sun")),
            _format_planet("Moon", chart.get("moon")),
            _format_planet("Mercury", chart.get("mercury")),
            _format_planet("Venus", chart.get("venus")),
            _format_planet("Mars", chart.get("mars")),
            _format_planet("Jupiter", chart.get("jupiter")),
            _format_planet("Saturn", chart.get("saturn")),
            f"- Ascendant: {chart['ascendant']['sign']} {chart['ascendant']['position']}°" if chart.get("ascendant") else "- Ascendant: unavailable",
        ])
        aspects_text = _format_aspects(chart.get("aspects") or [])
        transits_text = _format_transits(chart.get("transits") or [])
        chart_summary = f"{placements}\n\nNatal Aspects:\n{aspects_text}\n\nCurrent Transits:\n{transits_text}"
    else:
        chart_summary = "Natal chart data unavailable."

    system = (
        f"You are an expert Western astrologer. You have already provided a full reading for "
        f"{state['full_name']} (born {state['parsed_dob']} in {state['birth_location']}, "
        f"birth time {state['birth_time']} {state.get('birth_time_timezone', '')}).\n\n"
        f"Their natal chart:\n{chart_summary}\n\n"
        "Answer the user's follow-up questions based on their chart and your previous reading. "
        "Be specific and grounded in the chart data — do NOT invent placements not listed above. "
        "Keep responses warm, concise, and actionable."
    )

    messages = [
        {"role": "system", "content": system},
        {"role": "assistant", "content": state["final_report"]},
        *chat_history,
        {"role": "user", "content": question},
    ]

    response = client.chat.completions.create(
        model="gpt-4o",
        max_tokens=1024,
        messages=messages,
    )

    return response.choices[0].message.content


def generate_report(state: "AstrologerState") -> str:
    client = openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"])

    response = client.chat.completions.create(
        model="gpt-4o",
        max_tokens=2048,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an expert Western astrologer with deep knowledge of natal charts, "
                    "transits, progressions, and psychological astrology. Be specific, insightful, and kind."
                ),
            },
            {"role": "user", "content": build_prompt(state)},
        ],
    )

    return response.choices[0].message.content
