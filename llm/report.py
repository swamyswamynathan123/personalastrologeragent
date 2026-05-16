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


def build_prompt(state: "AstrologerState") -> str:
    chart = state.get("chart_data") or {}
    focus = state.get("report_focus") or "general life reading"
    additional = state.get("additional_info") or ""

    chart_section = ""
    if chart:
        lines = [
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
        chart_section = "\n".join(lines)
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
