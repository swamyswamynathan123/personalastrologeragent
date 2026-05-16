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
        if not h or not h.get("sign"):
            lines.append(f"- House {num} ({theme}): unavailable")
            continue
        ruler = h.get("ruler")
        if ruler:
            retro = " (retrograde)" if ruler.get("retrograde") else ""
            house_pos = f", House {ruler['house']}" if ruler.get("house") else ""
            dignity = f" [{ruler['dignity']}]" if ruler.get("dignity") else ""
            ruler_str = f" → ruler {ruler['planet'].capitalize()} in {ruler['sign']} {ruler['position']}°{retro}{house_pos}{dignity}"
        else:
            ruler_str = ""
        lines.append(f"- House {num} ({theme}): {h['sign']} {h['position']}°{ruler_str}")
    return "\n".join(lines)


def _format_solar_arcs(solar_arcs: dict) -> str:
    if not solar_arcs:
        return "Solar arc directions unavailable."
    arc = solar_arcs.get("arc", 0)
    lines = [f"(Solar arc: {arc}° — each degree ≈ 1 year of life)"]
    for key, label in [
        ("sun", "Arc Sun"), ("moon", "Arc Moon"), ("mercury", "Arc Mercury"),
        ("venus", "Arc Venus"), ("mars", "Arc Mars"), ("jupiter", "Arc Jupiter"),
        ("saturn", "Arc Saturn"), ("ascendant", "Arc Ascendant"), ("midheaven", "Arc Midheaven"),
    ]:
        data = solar_arcs.get(key)
        if data:
            dignity = f" [{data['dignity']}]" if data.get("dignity") else ""
            lines.append(f"- {label}: {data['sign']} {data['position']}°{dignity}")
        else:
            lines.append(f"- {label}: unavailable")
    return "\n".join(lines)


def _format_solar_arc_aspects(aspects: list[dict]) -> str:
    if not aspects:
        return "No solar arc aspects within 1° orb of natal chart points."
    lines = []
    for a in aspects:
        dp = a["directed_planet"].replace("arc_", "Arc ").replace("_", " ").title()
        np_ = a["natal_planet"].replace("_", " ").title()
        direction = "applying" if a.get("applying") else "separating"
        lines.append(f"- {dp} {a['aspect']} natal {np_} (orb {a['orb']}°, {direction})")
    return "\n".join(lines)


def _format_aspect_patterns(patterns: list[dict]) -> str:
    if not patterns:
        return "No major aspect patterns detected."
    lines = []
    for p in patterns:
        planets_str = ", ".join(pl.replace("_", " ").title() for pl in p["planets"])
        apex = f" — apex: {p['apex'].replace('_', ' ').title()}" if p.get("apex") else ""
        element = f" ({p['element']})" if p.get("element") else ""
        lines.append(f"- **{p['type']}**{element}: {planets_str}{apex}")
    return "\n".join(lines)


def _format_profection(profection: dict | None) -> str:
    if not profection:
        return "Annual profection unavailable."
    house = profection["profected_house"]
    theme = _HOUSE_THEMES.get(house, "")
    lord = (profection.get("lord_of_year") or "unknown").capitalize()
    lord_sign = profection.get("lord_sign", "unknown")
    lord_pos = profection.get("lord_position", "?")
    lord_house = f", House {profection['lord_house']}" if profection.get("lord_house") else ""
    retro = " (retrograde)" if profection.get("lord_retrograde") else ""
    dignity = f" [{profection['lord_dignity']}]" if profection.get("lord_dignity") else ""
    return (
        f"- Age {profection['age']} → House {house} profection year ({theme})\n"
        f"- Lord of the Year: {lord} in {lord_sign} {lord_pos}°{retro}{lord_house}{dignity}"
    )


def _format_progressed_aspects(prog_aspects: list[dict]) -> str:
    if not prog_aspects:
        return "No progressed aspects within 1° orb of natal chart points."
    lines = []
    for a in prog_aspects:
        pp = a["progressed_planet"].replace("_", " ").title()
        np_ = a["natal_planet"].replace("_", " ").title()
        direction = "applying" if a.get("applying") else "separating"
        lines.append(f"- {pp} {a['aspect']} natal {np_} (orb {a['orb']}°, {direction})")
    return "\n".join(lines)


def _format_progressions(prog: dict | None) -> str:
    if not prog:
        return "Secondary progressions unavailable."
    date_str = prog.get("progressed_date", "unknown")
    lines = [f"(Progressed date: {date_str} — each year of life = 1 day after birth)"]
    for label, key in [("Sun", "sun"), ("Moon", "moon"), ("Mercury", "mercury"),
                        ("Venus", "venus"), ("Mars", "mars")]:
        data = prog.get(key)
        if data:
            retro = " (retrograde)" if data.get("retrograde") else ""
            house = f", House {data['house']}" if data.get("house") else ""
            dignity = f" [{data['dignity']}]" if data.get("dignity") else ""
            lines.append(f"- Progressed {label}: {data['sign']} {data['position']}°{retro}{house}{dignity}")
        else:
            lines.append(f"- Progressed {label}: unavailable")
    for label, key in [("Ascendant", "ascendant"), ("Midheaven", "midheaven")]:
        data = prog.get(key)
        if data:
            lines.append(f"- Progressed {label}: {data['sign']} {data['position']}°")
        else:
            lines.append(f"- Progressed {label}: unavailable")
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
            _format_planet("Chiron", chart.get("chiron")),
        ])
        ruler_section = "## Chart Ruler\n" + _format_chart_ruler(chart.get("chart_ruler"))
        balance_section = "## Elemental & Modal Balance\n" + _format_balance(chart.get("balance") or {})
        nodes_section = "## Lunar Nodes\n" + _format_nodes(chart)
        houses_section = "## House Cusps\n" + _format_houses(chart.get("houses") or {})
        aspects_section = "## Natal Aspects\n" + _format_aspects(chart.get("aspects") or [])
        patterns_section = "## Aspect Patterns\n" + _format_aspect_patterns(chart.get("aspect_patterns") or [])
        transits_section = "## Current Transits (as of report date)\n" + _format_transits(chart.get("transits") or [])
        progressions_section = "## Secondary Progressions\n" + _format_progressions(chart.get("progressions"))
        prog_aspects_section = "## Progressed Aspects to Natal Chart\n" + _format_progressed_aspects(chart.get("progressed_aspects") or [])
        solar_arcs_section = "## Solar Arc Directions\n" + _format_solar_arcs(chart.get("solar_arcs") or {})
        solar_arc_aspects_section = "## Solar Arc Aspects to Natal Chart\n" + _format_solar_arc_aspects(chart.get("solar_arc_aspects") or [])
        profection_section = "## Annual Profection\n" + _format_profection(chart.get("profection"))
        chart_section = "\n\n".join([
            placements, ruler_section, balance_section, nodes_section, houses_section,
            aspects_section, patterns_section, transits_section,
            progressions_section, prog_aspects_section,
            solar_arcs_section, solar_arc_aspects_section,
            profection_section,
        ])
    else:
        chart_section = "## Natal Chart\nChart computation was unavailable. Base interpretations on Sun sign and general astrology."

    additional_section = f"\n**Additional Context from User:** {additional}" if additional else ""

    return f"""You are a professional, empathetic, and highly knowledgeable astrologer.

Generate a comprehensive, personalized astrological reading for the person below.
Only use the chart data provided — do NOT invent placements, transits, or aspects not listed here.
Dignity levels: domicile (strongest) > exaltation (strong) > no dignity (neutral) > detriment (weakened) > fall (most challenged).
For aspects: applying aspects (planets still moving toward exact) are currently intensifying; separating aspects are past their peak and more ingrained.
Use the elemental and modal balance to characterise overall temperament before interpreting individual placements.
Progressed Sun and Moon show the current life phase; a progressed sign change is a major threshold event worth highlighting.
Chiron represents core wounds and healing gifts; interpret its sign, house, and aspects as long-term soul work.
Progressed aspects to natal planets (1° orb) mark pivotal turning points — applying ones are currently activating.
Aspect patterns (Grand Trine, T-Square, Grand Cross, Yod) are the dominant structural themes of the chart — address them prominently.
The Annual Profection lord of the year is the single most important planet for the current 12-month period; weave it through timing and guidance.
Solar arc aspects within 1° orb are major life events activating now; applying solar arc aspects are imminent (within ~1 year), separating ones just passed. Treat them as concrete external turning points distinct from the more interior story told by progressions.

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
1. **Personal Overview** — Core personality traits from Sun, Moon, Ascendant, chart ruler, and elemental balance
2. **Life Direction & Karmic Themes** — Insights from the North/South Node axis and 12th/8th house placements
3. **Current Life Phase** — What the progressed Sun and Moon reveal about the chapter this person is in right now; highlight any recent or imminent sign changes
4. **Current Cosmic Climate** — Active transits (applying ones are most urgent) and what they mean personally, referencing house rulers for context
5. **Key Life Themes** — 3–4 dominant themes from natal aspects, house rulers, and dignity levels
6. **Practical Guidance** — Specific, actionable advice for the coming weeks grounded in applying transits and progressions
7. **Favorable Timing** — Suggest favorable days or periods based on applying transits and progressed Moon sign

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
            _format_planet("Chiron", chart.get("chiron")),
            f"- Ascendant: {chart['ascendant']['sign']} {chart['ascendant']['position']}°" if chart.get("ascendant") else "- Ascendant: unavailable",
        ])
        nodes_text = _format_nodes(chart)
        ruler_text = _format_chart_ruler(chart.get("chart_ruler"))
        aspects_text = _format_aspects(chart.get("aspects") or [])
        transits_text = _format_transits(chart.get("transits") or [])
        prog_text = _format_progressions(chart.get("progressions"))
        prog_aspects_text = _format_progressed_aspects(chart.get("progressed_aspects") or [])
        patterns_text = _format_aspect_patterns(chart.get("aspect_patterns") or [])
        profection_text = _format_profection(chart.get("profection"))
        solar_arcs_text = _format_solar_arcs(chart.get("solar_arcs") or {})
        solar_arc_aspects_text = _format_solar_arc_aspects(chart.get("solar_arc_aspects") or [])
        chart_summary = (
            f"{placements}\n\nChart Ruler:\n{ruler_text}"
            f"\n\nLunar Nodes:\n{nodes_text}"
            f"\n\nNatal Aspects:\n{aspects_text}"
            f"\n\nAspect Patterns:\n{patterns_text}"
            f"\n\nCurrent Transits:\n{transits_text}"
            f"\n\nSecondary Progressions:\n{prog_text}"
            f"\n\nProgressed Aspects to Natal:\n{prog_aspects_text}"
            f"\n\nSolar Arc Directions:\n{solar_arcs_text}"
            f"\n\nSolar Arc Aspects to Natal:\n{solar_arc_aspects_text}"
            f"\n\nAnnual Profection:\n{profection_text}"
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
        max_tokens=4096,
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
