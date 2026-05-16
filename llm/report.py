from __future__ import annotations
import os
from typing import TYPE_CHECKING

import openai
from dotenv import load_dotenv

if TYPE_CHECKING:
    from agent.state import AstrologerState

load_dotenv()

_HOUSE_THEMES = {
    1: "Self, Identity, Appearance",
    2: "Resources, Values, Money",
    3: "Communication, Siblings, Short Travel",
    4: "Home, Family, Roots",
    5: "Creativity, Romance, Children, Pleasure",
    6: "Work, Health, Service, Daily Routines",
    7: "Partnerships, Marriage, Open Enemies",
    8: "Transformation, Shared Resources, Sexuality, Rebirth",
    9: "Philosophy, Higher Education, Long Travel, Beliefs",
    10: "Career, Public Reputation, Authority",
    11: "Friendships, Groups, Hopes, Social Causes",
    12: "Hidden Matters, Spirituality, Self-Undoing, Karma",
}


def _format_planet(label: str, data: dict | None) -> str:
    if not data:
        return f"- {label}: data unavailable"
    retro = " (retrograde)" if data.get("retrograde") else ""
    house = f", House {data['house']}" if data.get("house") else ""
    dignity = f" [{data['dignity']}]" if data.get("dignity") else ""
    return f"- {label}: {data['sign']} {data['position']}°{retro}{house}{dignity}"


def _format_aspects(aspects: list[dict]) -> str:
    if not aspects:
        return "No major natal aspects computed."
    lines = []
    for a in aspects:
        p1 = a["planet1"].replace("_", " ").title()
        p2 = a["planet2"].replace("_", " ").title()
        direction = "applying" if a.get("applying") else "separating"
        lines.append(f"- {p1} {a['aspect']} {p2} (orb {a['orb']}°, {direction})")
    return "\n".join(lines)


def _format_transits(transits: list[dict]) -> str:
    if not transits:
        return "No significant transits active right now (within 3° orb)."
    lines = []
    for t in transits:
        tp = t["transiting_planet"].capitalize()
        np_ = t["natal_planet"].capitalize()
        direction = "applying" if t.get("applying") else "separating"
        lines.append(f"- Transiting {tp} {t['aspect']} natal {np_} (orb {t['orb']}°, {direction})")
    return "\n".join(lines)


def _format_nodes(chart: dict) -> str:
    nn = chart.get("north_node")
    sn = chart.get("south_node")
    lines = []
    if nn:
        house = f", House {nn['house']}" if nn.get("house") else ""
        lines.append(f"- North Node (Life Direction / Future Path): {nn['sign']} {nn['position']}°{house}")
    else:
        lines.append("- North Node: unavailable")
    if sn:
        lines.append(f"- South Node (Past Karma / Innate Gifts): {sn['sign']} {sn['position']}°")
    else:
        lines.append("- South Node: unavailable")
    return "\n".join(lines)


def _format_balance(balance: dict) -> str:
    if not balance:
        return "Balance data unavailable."
    elements = balance.get("elements", {})
    modalities = balance.get("modalities", {})
    el_str = " | ".join(f"{k} {v}" for k, v in elements.items())
    mod_str = " | ".join(f"{k} {v}" for k, v in modalities.items())
    return f"- Elements: {el_str}\n- Modalities: {mod_str}"


def _format_chart_ruler(chart_ruler: dict | None) -> str:
    if not chart_ruler:
        return "Chart ruler unavailable (Ascendant data missing)."
    planet = chart_ruler["planet"].capitalize()
    asc_sign = chart_ruler.get("asc_sign", "")
    sign = chart_ruler.get("sign", "unknown")
    pos = chart_ruler.get("position", 0)
    house = f", House {chart_ruler['house']}" if chart_ruler.get("house") else ""
    retro = " (retrograde)" if chart_ruler.get("retrograde") else ""
    dignity = f" [{chart_ruler['dignity']}]" if chart_ruler.get("dignity") else ""
    return f"- {asc_sign} Ascendant → ruled by {planet} in {sign} {pos}°{retro}{house}{dignity}"


def _format_houses(houses: dict) -> str:
    if not houses:
        return "House cusp data unavailable."
    lines = []
    for num in range(1, 13):
        h = houses.get(str(num))
        theme = _HOUSE_THEMES.get(num, "")
        if h and h.get("sign"):
            lines.append(f"- House {num} ({theme}): {h['sign']} {h['position']}°")
        else:
            lines.append(f"- House {num} ({theme}): unavailable")
    return "\n".join(lines)


def build_prompt(state: "AstrologerState") -> str:
    chart = state.get("chart_data") or {}
    focus = state.get("report_focus") or "general life reading"
    additional = state.get("additional_info") or ""

    if chart:
        placements = "\n".join([
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
        ])
        ruler_section = "## Chart Ruler\n" + _format_chart_ruler(chart.get("chart_ruler"))
        balance_section = "## Elemental & Modal Balance\n" + _format_balance(chart.get("balance") or {})
        nodes_section = "## Lunar Nodes\n" + _format_nodes(chart)
        houses_section = "## House Cusps\n" + _format_houses(chart.get("houses") or {})
        aspects_section = "## Natal Aspects\n" + _format_aspects(chart.get("aspects") or [])
        transits_section = "## Current Transits (as of report date)\n" + _format_transits(chart.get("transits") or [])
        chart_section = "\n\n".join([placements, ruler_section, balance_section, nodes_section, houses_section, aspects_section, transits_section])
    else:
        chart_section = "## Natal Chart\nChart computation was unavailable. Base interpretations on Sun sign and general astrology."

    additional_section = f"\n**Additional Context from User:** {additional}" if additional else ""

    return f"""You are a professional, empathetic, and highly knowledgeable astrologer.

Generate a comprehensive, personalized astrological reading for the person below.
Only use the chart data provided — do NOT invent placements, transits, or aspects not listed here.
Dignity levels: domicile (strongest) > exaltation (strong) > no dignity (neutral) > detriment (weakened) > fall (most challenged).
For aspects: applying aspects (planets still moving toward exact) are currently intensifying; separating aspects are past their peak and more ingrained.
Use the elemental and modal balance to characterise overall temperament before interpreting individual placements.

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
1. **Personal Overview** — Core personality traits from Sun, Moon, Ascendant, and key natal aspects
2. **Life Direction & Karmic Themes** — Insights from the North/South Node axis and 12th/8th house placements
3. **Current Cosmic Climate** — Active transits (applying ones are most urgent), and what they mean for this person now
4. **Key Life Themes** — 3–4 dominant themes from house rulers, stelliums, and applying natal aspects
5. **Practical Guidance** — Specific, actionable advice for the coming weeks grounded in the active transits
6. **Favorable Timing** — Suggest favorable days or periods based on applying transits and chart patterns

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
        nodes_text = _format_nodes(chart)
        ruler_text = _format_chart_ruler(chart.get("chart_ruler"))
        aspects_text = _format_aspects(chart.get("aspects") or [])
        transits_text = _format_transits(chart.get("transits") or [])
        chart_summary = (
            f"{placements}\n\nChart Ruler:\n{ruler_text}"
            f"\n\nLunar Nodes:\n{nodes_text}"
            f"\n\nNatal Aspects:\n{aspects_text}"
            f"\n\nCurrent Transits:\n{transits_text}"
        )
    else:
        chart_summary = "Natal chart data unavailable."

    system = (
        f"You are an expert Western astrologer. You have already provided a full reading for "
        f"{state['full_name']} (born {state['parsed_dob']} in {state['birth_location']}, "
        f"birth time {state['birth_time']} {state.get('birth_time_timezone', '')}).\n\n"
        f"Their chart data:\n{chart_summary}\n\n"
        "Answer the user's follow-up questions based on their chart and your previous reading. "
        "Applying aspects and transits are currently intensifying — prioritize these when discussing timing. "
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
