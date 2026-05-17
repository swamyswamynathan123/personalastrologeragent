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


def _format_fixed_stars(conjunctions: list[dict]) -> str:
    if not conjunctions:
        return "No natal planets or angles within 1° of a major fixed star."
    lines = []
    nature_map = {"benefic": "fortunate", "malefic": "challenging", "mixed": "mixed"}
    for c in conjunctions:
        body = c["body"].replace("_", " ").title()
        nature_tag = nature_map.get(c["nature"], "")
        lines.append(f"- {body} conjunct {c['star']} (orb {c['orb']}°, {nature_tag}) — {c['keywords']}")
    return "\n".join(lines)


def _format_anaretic_degrees(anaretic: list[dict]) -> str:
    if not anaretic:
        return "No planets or points at the anaretic degree (29°)."
    lines = []
    for a in anaretic:
        body = a["body"].replace("_", " ").title()
        lines.append(
            f"- {body} at 29° {a['sign']} — finishing energy; urgency to resolve unfinished themes before the next sign chapter begins"
        )
    return "\n".join(lines)


def _format_sect(sect: dict) -> str:
    if not sect:
        return "Sect data unavailable."
    chart_type = sect.get("chart_type", "unknown").capitalize()
    is_day = chart_type == "Day"
    planets = sect.get("planets", {})

    lines = [f"({chart_type} chart — Sun {'above' if is_day else 'below'} the horizon at birth)"]
    for planet, data in planets.items():
        in_sect = data.get("in_sect")
        role = data.get("role")
        if in_sect is None:
            continue
        label = planet.capitalize()
        if role == "malefic":
            if in_sect:
                lines.append(f"- {label}: in-sect malefic — difficulties are structured and purposeful")
            else:
                lines.append(f"- **{label}: out-of-sect malefic** — most destabilizing planet; erratic, harder to channel constructively")
        elif role == "benefic":
            if in_sect:
                lines.append(f"- {label}: in-sect benefic — gifts flow naturally and accessibly")
            else:
                lines.append(f"- {label}: out-of-sect benefic — blessings present but require conscious cultivation")
    return "\n".join(lines)


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


def _format_lunar_phase(lunar_phase: dict) -> str:
    if not lunar_phase:
        return "Lunar phase unavailable."
    return f"- {lunar_phase['phase']} ({lunar_phase['angle']}° Moon ahead of Sun) — {lunar_phase['description']}"


def _format_part_of_fortune(pof: dict | None) -> str:
    if not pof:
        return "Part of Fortune unavailable."
    dignity = f" [{pof['dignity']}]" if pof.get("dignity") else ""
    chart_type = pof.get("chart_type", "").capitalize()
    return f"- {pof['sign']} {pof['position']}°{dignity} ({chart_type} chart formula)"


def _format_asteroids(chart: dict) -> str:
    meta = {
        "ceres":  ("Ceres",  "nurturing style, loss and return cycles, relationship with sustenance and the body"),
        "pallas": ("Pallas", "pattern recognition, strategic wisdom, creative intelligence, justice orientation"),
        "juno":   ("Juno",   "partnership needs, commitment style, what is sought and given in long-term bonds"),
        "vesta":  ("Vesta",  "sacred focus, devotion, what the person is willing to sacrifice for, inner flame"),
    }
    lines = ["## Major Asteroids"]
    for key, (label, meaning) in meta.items():
        d = chart.get(key)
        if not d:
            lines.append(f"- {label}: unavailable")
            continue
        retro = " (retrograde)" if d.get("retrograde") else ""
        house = f", House {d['house']}" if d.get("house") else ""
        lines.append(f"- {label}: {d['sign']} {d['position']}°{retro}{house} — {meaning}")
    return "\n".join(lines)


def _format_arabic_parts(parts: dict) -> str:
    if not parts:
        return "Arabic Parts unavailable."
    lines = []
    meta = {
        "spirit":   ("Part of Spirit (Daimon)", "intentional soul direction, conscious life purpose, what the self wills toward"),
        "eros":     ("Part of Eros",            "desire, attraction, aesthetic longing, what the soul finds beautiful and pursues"),
        "marriage": ("Part of Marriage",         "relationship style, timing, and the qualities sought in partnership"),
    }
    for key, (label, meaning) in meta.items():
        p = parts.get(key)
        if not p:
            continue
        dignity = f" [{p['dignity']}]" if p.get("dignity") else ""
        ct = f" ({p['chart_type']} chart formula)" if p.get("chart_type") else ""
        lines.append(f"- {label}: {p['sign']} {p['position']}°{dignity}{ct} — {meaning}")
    return "\n".join(lines) if lines else "Arabic Parts unavailable."


def _format_antiscia(connections: list[dict]) -> str:
    if not connections:
        return "No antiscia or contra-antiscia connections within 1.5° orb."
    lines = []
    for c in connections:
        p1 = c["planet1"].replace("_", " ").title()
        p2 = c["planet2"].replace("_", " ").title()
        label = "Antiscion" if c["type"] == "antiscia" else "Contra-antiscion"
        lines.append(f"- {p1} {label} {p2} (orb {c['orb']}°, {c['axis']})")
    return "\n".join(lines)


def _format_stelliums(stelliums: list[dict]) -> str:
    if not stelliums:
        return "No stelliums (3+ planets in same sign or house)."
    lines = []
    for s in stelliums:
        planets = ", ".join(p.replace("_", " ").title() for p in s["planets"])
        lines.append(f"- Stellium in {s['location']}: {planets} ({len(s['planets'])} planets)")
    return "\n".join(lines)


def _format_mutual_receptions(receptions: list[dict]) -> str:
    if not receptions:
        return "No mutual receptions detected."
    lines = []
    for r in receptions:
        p1 = r["planet1"].capitalize()
        p2 = r["planet2"].capitalize()
        lines.append(f"- {p1} (in {r['planet1_sign']}) ↔ {p2} (in {r['planet2_sign']}) — mutual exchange of rulership")
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


_SR_PLANETS = ["sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn", "uranus", "neptune", "pluto"]


def _format_solar_return(sr: dict) -> str:
    if not sr:
        return "Solar return chart unavailable."
    lines = [
        f"(Solar return {sr.get('return_year', '')} — cast at current location, exact moment: {sr.get('return_date', 'unknown')})"
    ]
    asc = sr.get("ascendant")
    mc = sr.get("midheaven")
    moon = sr.get("moon")
    if asc:
        lines.append(f"- SR Ascendant: {asc['sign']} {asc['position']}° — overall theme and self-presentation for the year")
    if mc:
        lines.append(f"- SR Midheaven: {mc['sign']} {mc['position']}° — career and public-facing focus")
    if moon:
        house = f", SR House {moon['house']}" if moon.get("house") else ""
        lines.append(f"- SR Moon: {moon['sign']} {moon['position']}°{house} — emotional tone of the year")
    angular = sr.get("angular_planets") or []
    if angular:
        ang_str = "; ".join(
            f"{a['planet'].capitalize()} conjunct SR {a['angle'].replace('_', ' ').title()} (orb {a['orb']}°)"
            for a in angular
        )
        lines.append(f"- Angular planets (most prominent this year): {ang_str}")
    # Houses with 2+ SR planets = highlighted life areas
    house_map: dict[str, list[str]] = {}
    for planet in _SR_PLANETS:
        p = sr.get(planet)
        if p and p.get("house"):
            house_map.setdefault(str(p["house"]), []).append(planet)
    for house, planets in house_map.items():
        if len(planets) >= 2:
            lines.append(f"- SR House {house} occupied by {', '.join(p.capitalize() for p in planets)} — highlighted area of life this year")
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


def _format_firdaria(firdaria: dict | None, chart: dict | None = None) -> str:
    if not firdaria:
        return "Firdaria unavailable."
    major = (firdaria.get("major_lord") or "unknown").replace("_", " ").title()
    major_end = (firdaria.get("major_period_end") or "")[:10]
    major_rem = firdaria.get("years_remaining_major", "?")
    major_yrs = firdaria.get("major_period_years", "?")

    lines = [f"- Major period: {major} Firdaria ({major_yrs}-year period, ends {major_end}, {major_rem} yrs remaining)"]

    if chart:
        lord_data = chart.get((firdaria.get("major_lord") or "").lower())
        if lord_data:
            retro = " (retrograde)" if lord_data.get("retrograde") else ""
            house = f", House {lord_data['house']}" if lord_data.get("house") else ""
            dignity = f" [{lord_data['dignity']}]" if lord_data.get("dignity") else ""
            lines.append(f"  Natal condition: {major} in {lord_data.get('sign')} {lord_data.get('position')}°{retro}{house}{dignity}")

    sub = firdaria.get("sub_lord")
    if sub:
        sub_label = sub.replace("_", " ").title()
        sub_end = (firdaria.get("sub_period_end") or "")[:10]
        sub_rem = firdaria.get("years_remaining_sub", "?")
        lines.append(f"- Sub-period: {sub_label} sub-lord (ends {sub_end}, {sub_rem} yrs remaining)")
        if chart:
            sub_data = chart.get(sub)
            if sub_data:
                retro = " (retrograde)" if sub_data.get("retrograde") else ""
                house = f", House {sub_data['house']}" if sub_data.get("house") else ""
                dignity = f" [{sub_data['dignity']}]" if sub_data.get("dignity") else ""
                lines.append(f"  Natal condition: {sub_label} in {sub_data.get('sign')} {sub_data.get('position')}°{retro}{house}{dignity}")

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
    lunation = _format_progressed_lunation(prog)
    if lunation:
        lines.append(lunation)
    return "\n".join(lines)


def _format_upcoming_transits(upcoming: list[dict]) -> str:
    if not upcoming:
        return "No major outer-planet transits becoming exact within the next 90 days."
    lines = []
    for t in upcoming:
        tp = t["transiting_planet"].capitalize()
        np_ = t["natal_planet"].replace("_", " ").title()
        exact = t.get("exact_date") or "within window"
        retro = " (Rx)" if t.get("retrograde") else ""
        orb = round(t.get("min_orb", 0), 2)
        lines.append(
            f"- {tp}{retro} {t['aspect']} natal {np_} — exact ~{exact} (min orb {orb}°)"
        )
    return "\n".join(lines)


def _format_eclipse_sensitivity(eclipses: list[dict]) -> str:
    if not eclipses:
        return "No natal planets or angles within 3° of eclipses in the ±6-month window."
    lines = []
    for e in eclipses:
        body = e["body"].replace("_", " ").title()
        etype = e.get("eclipse_type", "eclipse").replace("_", " ")
        lines.append(
            f"- {body} (natal {e.get('body_sign', '?')} {e.get('body_pos', '?')}°) within {e['orb']}° of "
            f"{etype} at {e.get('eclipse_sign', '?')} {e.get('eclipse_pos', '?')}° on {e['eclipse_date']}"
        )
    return "\n".join(lines)


def _format_progressed_lunation(prog: dict) -> str:
    pl = prog.get("progressed_lunation")
    if not pl:
        return ""
    return (
        f"- Progressed Lunar Phase: **{pl['phase']}** "
        f"(Prog Moon {pl['angle']}° ahead of Prog Sun) — {pl['description']}\n"
        f"  → Years to next Progressed New Moon: ~{pl['years_to_next_new_moon']}"
    )


def _compute_convergences(chart: dict, state: "AstrologerState") -> list[str]:
    """Detect the same planet activated across multiple timing systems."""
    convergences = []

    profection = chart.get("profection") or {}
    firdaria = chart.get("firdaria") or {}
    vedic = chart.get("vedic") or {}
    dasha = (vedic.get("dasha") or {}) if vedic else {}
    transits = chart.get("transits") or []
    upcoming = chart.get("upcoming_transits") or []
    solar_arc_aspects = chart.get("solar_arc_aspects") or []
    progressed_aspects = chart.get("progressed_aspects") or []

    prof_lord = (profection.get("lord_of_year") or "").lower()
    fird_major = (firdaria.get("major_lord") or "").lower()
    maha_lord = (dasha.get("mahadasha_lord") or "").lower()

    # Triple convergence across all three systems
    if prof_lord and fird_major and maha_lord and prof_lord == fird_major == maha_lord:
        convergences.append(
            f"TRIPLE CONVERGENCE — {prof_lord.capitalize()} is simultaneously the Annual Profection "
            f"Lord, Firdaria Major Lord, and Vimshottari Mahadasha Lord. All three major timing systems "
            f"across Western and Vedic traditions point to the same planet. "
            f"{prof_lord.capitalize()}'s natal condition and any current transits to it represent the "
            f"single most defining theme of this entire life phase."
        )
    elif fird_major and maha_lord and fird_major == maha_lord:
        convergences.append(
            f"CROSS-TRADITION CONVERGENCE — {fird_major.capitalize()} is both the Firdaria Major Lord "
            f"(Western) and the Vimshottari Mahadasha Lord (Vedic). Both biographical timing systems "
            f"agree: this planet defines the current chapter across traditions."
        )
    if prof_lord and fird_major and prof_lord == fird_major and prof_lord != maha_lord:
        convergences.append(
            f"ANNUAL AMPLIFICATION — {prof_lord.capitalize()} is both the Annual Profection Lord and "
            f"Firdaria Major Lord, doubling its activation for the current year."
        )
    if prof_lord and maha_lord and prof_lord == maha_lord and prof_lord != fird_major:
        convergences.append(
            f"VEDIC-WESTERN ANNUAL SYNC — {prof_lord.capitalize()} is both the Annual Profection Lord "
            f"and Vimshottari Mahadasha Lord — the annual Western timing confirms the Vedic arc."
        )

    # Profection lord currently transited by an outer planet
    outer_planets = {"saturn", "uranus", "neptune", "pluto", "jupiter"}
    if prof_lord:
        for t in transits:
            if (t.get("natal_planet", "").lower() == prof_lord
                    and t.get("transiting_planet", "").lower() in outer_planets):
                tp = t["transiting_planet"].capitalize()
                convergences.append(
                    f"YEAR LORD UNDER TRANSIT — Transiting {tp} is {t['aspect']} natal "
                    f"{prof_lord.capitalize()} (orb {t['orb']}°, the Profection Lord of the Year). "
                    f"This dramatically intensifies the current year's themes."
                )
        for t in upcoming[:1]:
            if (t.get("natal_planet", "").lower() == prof_lord
                    and t.get("transiting_planet", "").lower() in outer_planets):
                tp = t["transiting_planet"].capitalize()
                convergences.append(
                    f"YEAR LORD INCOMING — Transiting {tp} will {t['aspect']} natal "
                    f"{prof_lord.capitalize()} (Profection Lord of the Year) ~{t.get('exact_date', 'soon')}. "
                    f"Most time-sensitive event on the horizon."
                )

    # Solar arc applying to ASC or MC
    for sa in solar_arc_aspects:
        np_ = (sa.get("natal_planet") or "").lower()
        if np_ in ("ascendant", "midheaven") and sa.get("applying"):
            dp = sa["directed_planet"].replace("arc_", "Arc ").replace("_", " ").title()
            orb = float(sa.get("orb", 1))
            timeframe = "months" if orb < 0.5 else "about a year"
            convergences.append(
                f"SOLAR ARC TO ANGLE — {dp} {sa['aspect']} natal {np_.capitalize()} "
                f"(orb {sa['orb']}°, applying). A concrete external milestone arrives within {timeframe} — "
                f"identity shift (ASC) or career turning point (MC)."
            )

    # Multiple outer planets hitting the same natal point
    outer_by_natal: dict[str, list[str]] = {}
    for t in list(transits) + list(upcoming):
        np_ = (t.get("natal_planet") or "").lower()
        tp = (t.get("transiting_planet") or "").lower()
        if tp in {"saturn", "uranus", "neptune", "pluto"}:
            outer_by_natal.setdefault(np_, []).append(tp)
    for np_, outers in outer_by_natal.items():
        unique = list(dict.fromkeys(outers))
        if len(unique) >= 2:
            planet_label = np_.replace("_", " ").title()
            outers_str = " + ".join(p.capitalize() for p in unique)
            convergences.append(
                f"MULTI-OUTER PRESSURE on natal {planet_label} — {outers_str} are simultaneously "
                f"activating this point. Compound transformation of {planet_label}'s natal themes."
            )

    # Exact progressed aspects within 0.5° applying
    for pa in progressed_aspects:
        try:
            orb = float(pa.get("orb", 999))
        except (TypeError, ValueError):
            continue
        if orb <= 0.5 and pa.get("applying"):
            pp = pa["progressed_planet"].replace("_", " ").title()
            np_ = pa["natal_planet"].replace("_", " ").title()
            convergences.append(
                f"EXACT PROGRESSED ASPECT — Progressed {pp} {pa['aspect']} natal {np_} "
                f"(orb {pa['orb']}°, applying). Within 0.5°: crystallizing RIGHT NOW as the most "
                f"immediate psychological development."
            )

    return convergences


def _format_yogas(yogas: list[dict]) -> str:
    if not yogas:
        return "No major Vedic yogas detected in the sidereal chart."
    lines = []
    for y in yogas:
        planets_str = " + ".join(p.replace("_", " ").title() for p in y["planets"])
        lines.append(f"- **{y['name']}** [{y['category']}] — {y['detail']}")
        lines.append(f"  {y['description']}")
    return "\n".join(lines)


def _format_vedic(vedic: dict | None) -> str:
    if not vedic:
        return "Vedic (Jyotish) overlay unavailable."
    ayanamsa = vedic.get("ayanamsa", "?")
    sid = vedic.get("sidereal") or {}
    dasha = vedic.get("dasha") or {}

    lines = [f"(Lahiri ayanamsa: {ayanamsa}° — sidereal positions are tropical minus this value)"]

    key_bodies = [
        ("Sun", "sun"), ("Moon", "moon"), ("Ascendant (Lagna)", "ascendant"),
        ("Mercury", "mercury"), ("Venus", "venus"), ("Mars", "mars"),
        ("Jupiter", "jupiter"), ("Saturn", "saturn"),
    ]
    for label, key in key_bodies:
        d = sid.get(key)
        if not d:
            continue
        nav = f", D9 Navamsha: {d['navamsha']}" if d.get("navamsha") else ""
        if key == "moon" and d.get("nakshatra"):
            nak = d["nakshatra"]
            lines.append(
                f"- Sidereal {label}: {d['sign']} {d['position']}°  |  "
                f"Nakshatra: {nak['name']} (lord: {nak['lord'].capitalize()}, pada {nak['pada']}){nav}"
            )
        else:
            lines.append(f"- Sidereal {label}: {d['sign']} {d['position']}°{nav}")

    if dasha:
        maha = (dasha.get("mahadasha_lord") or "?").capitalize()
        maha_end = (dasha.get("mahadasha_end") or "")[:10]
        maha_rem = dasha.get("years_remaining_mahadasha", "?")
        maha_yrs = dasha.get("mahadasha_years", "?")
        lines.append(
            f"- Vimshottari Mahadasha: {maha} ({maha_yrs}-yr period, ends {maha_end}, {maha_rem} yrs remaining)"
        )
        antar = dasha.get("antardasha_lord")
        if antar:
            antar_label = antar.capitalize()
            antar_end = (dasha.get("antardasha_end") or "")[:10]
            antar_rem = dasha.get("years_remaining_antardasha", "?")
            lines.append(f"- Antardasha (sub-period): {antar_label} (ends {antar_end}, {antar_rem} yrs remaining)")

    yogas = vedic.get("yogas") or []
    if yogas:
        lines.append(f"\n**Vedic Yogas ({len(yogas)} detected):**")
        lines.append(_format_yogas(yogas))

    return "\n".join(lines)


def build_prompt(state: "AstrologerState") -> str:
    chart = state.get("chart_data") or {}
    focus = state.get("report_focus") or "general life reading"
    additional = state.get("additional_info") or ""
    convergences = _compute_convergences(chart, state) if chart else []

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
        anaretic_section = "## Anaretic Degrees (29°)\n" + _format_anaretic_degrees(chart.get("anaretic_degrees") or [])
        fixed_stars_section = "## Fixed Star Conjunctions (1° orb)\n" + _format_fixed_stars(chart.get("fixed_stars") or [])
        ruler_section = "## Chart Ruler\n" + _format_chart_ruler(chart.get("chart_ruler"))
        balance_section = "## Elemental & Modal Balance\n" + _format_balance(chart.get("balance") or {})
        sect_section = "## Planetary Sect\n" + _format_sect(chart.get("sect") or {})
        lunar_phase_section = "## Natal Lunar Phase\n" + _format_lunar_phase(chart.get("lunar_phase") or {})
        pof_section = "## Part of Fortune\n" + _format_part_of_fortune(chart.get("part_of_fortune"))
        asteroids_section = _format_asteroids(chart)
        arabic_section = "## Additional Arabic Parts\n" + _format_arabic_parts(chart.get("arabic_parts") or {})
        antiscia_section = "## Antiscia & Contra-Antiscia (1.5° orb)\n" + _format_antiscia(chart.get("antiscia") or [])
        stelliums_section = "## Stelliums\n" + _format_stelliums(chart.get("stelliums") or [])
        receptions_section = "## Mutual Receptions\n" + _format_mutual_receptions(chart.get("mutual_receptions") or [])
        nodes_section = "## Lunar Nodes\n" + _format_nodes(chart)
        houses_section = "## House Cusps\n" + _format_houses(chart.get("houses") or {})
        aspects_section = "## Natal Aspects\n" + _format_aspects(chart.get("aspects") or [])
        patterns_section = "## Aspect Patterns\n" + _format_aspect_patterns(chart.get("aspect_patterns") or [])
        eclipse_section = "## Eclipse Sensitivity (±6 months, 3° orb)\n" + _format_eclipse_sensitivity(chart.get("eclipse_sensitivity") or [])
        transits_section = "## Current Transits (as of report date)\n" + _format_transits(chart.get("transits") or [])
        upcoming_section = "## Upcoming Transits (next 90 days — outer planets only)\n" + _format_upcoming_transits(chart.get("upcoming_transits") or [])
        progressions_section = "## Secondary Progressions\n" + _format_progressions(chart.get("progressions"))
        prog_aspects_section = "## Progressed Aspects to Natal Chart\n" + _format_progressed_aspects(chart.get("progressed_aspects") or [])
        solar_arcs_section = "## Solar Arc Directions\n" + _format_solar_arcs(chart.get("solar_arcs") or {})
        solar_arc_aspects_section = "## Solar Arc Aspects to Natal Chart\n" + _format_solar_arc_aspects(chart.get("solar_arc_aspects") or [])
        profection_section = "## Annual Profection\n" + _format_profection(chart.get("profection"))
        firdaria_section = "## Firdaria Time Lords\n" + _format_firdaria(chart.get("firdaria"), chart)
        solar_return_section = "## Solar Return Chart\n" + _format_solar_return(chart.get("solar_return") or {})
        vedic_section = "## Vedic (Jyotish) Overlay\n" + _format_vedic(chart.get("vedic"))
        chart_section = "\n\n".join([
            placements, anaretic_section, fixed_stars_section, ruler_section, balance_section, sect_section,
            lunar_phase_section, pof_section, asteroids_section, arabic_section, antiscia_section,
            stelliums_section, receptions_section,
            nodes_section, houses_section,
            aspects_section, patterns_section, eclipse_section, transits_section, upcoming_section,
            progressions_section, prog_aspects_section,
            solar_arcs_section, solar_arc_aspects_section,
            profection_section, firdaria_section, solar_return_section, vedic_section,
        ])
    else:
        chart_section = "## Natal Chart\nChart computation was unavailable. Base interpretations on Sun sign and general astrology."

    additional_section = f"\n**Additional Context from User:** {additional}" if additional else ""

    confidence = state.get("birth_time_confidence") or "exact"
    if confidence in ("approximate", "unknown"):
        rectification_section = f"""

**8. Narrowing Your Birth Time** *(Birth time marked as "{confidence}" — add this section)*
Using the chart data above (Firdaria periods, profection years, and transit dates), give 3–4 specific life-event checkpoints this person can use to confirm their Ascendant. For example: "If [Firdaria lord] ruled a period when a major [house theme] event occurred around [year range], this confirms [Ascendant candidate]." Name the 2 most likely Ascendant signs given a ±{30 if confidence == "approximate" else 90}-minute birth time window around {state.get("birth_time", "the stated time")}. Close with: *"Once confirmed, regenerate this reading with 'exact' confidence for precise house-based interpretations."* Keep the section to 5–7 sentences."""
    else:
        rectification_section = ""

    convergence_block = ""
    if convergences:
        convergence_block = (
            "\n## ⚡ Convergence Intelligence (Pre-Computed — Highest Priority)\n"
            "These findings were detected BEFORE you read the chart. They represent the "
            "loudest signals across multiple timing layers and MUST be addressed explicitly in the report:\n\n"
            + "\n\n".join(f"▶ {c}" for c in convergences)
            + "\n"
        )

    return f"""You are a master Western astrologer writing a personalized reading for {state['full_name']}.

Only use the chart data provided — do NOT invent placements, transits, or aspects not listed.
{convergence_block}
## Person Details
- **Full Name:** {state['full_name']}
- **Date of Birth:** {state['parsed_dob']}
- **Birth Location:** {state['birth_location']}
- **Birth Time:** {state['birth_time']} ({state.get('birth_time_timezone', 'timezone not specified')}) [Confidence: {state.get('birth_time_confidence') or 'exact'}]
- **House System:** {state.get('house_system') or 'Placidus'}
- **Current Location:** {state['current_location']}
- **Report Generated As Of:** {state['parsed_current_datetime']}
- **Report Focus:** {focus}
{additional_section}

{chart_section}

## Reference: Interpretation Rules
- Dignity: domicile (strongest) > exaltation > neutral > detriment > fall (most challenged)
- Aspects: applying = currently intensifying; separating = past peak, more ingrained
- Aspect patterns (Grand Trine, T-Square, Yod, Grand Cross) are structural life themes — more important than individual aspects
- Mutual receptions: treat both planets as cooperative allies, not isolated placements
- Stelliums: overwhelmingly concentrated energy — lead with the stellium before individual planets in that area
- Lunar phase: the person's fundamental life rhythm and approach to beginnings/endings
- Part of Fortune: the sign/area of natural ease and abundance
- Part of Spirit: the intentional counterpart to Fortune — where Fortune shows what flows naturally, Spirit shows what the soul deliberately wills; important when discussing life purpose or spiritual direction
- Part of Eros: the sign of longing and aesthetic desire; what the person finds irresistibly beautiful or pursues with passion; relevant in questions of creativity, romance, and calling
- Part of Marriage: the sign/area describing relationship style and what is sought in partnership; integrate with the 7th house and Venus for a complete relationship picture
- Antiscia: two planets in antiscion (summing to 180°) operate as a hidden conjunction — they support and reflect each other across the solstice axis, often appearing as an inexplicable sympathy or talent that standard aspects don't explain. Contra-antiscia (summing to 360°) behave like a hidden opposition — tension and awareness between the two planets. Antiscia connections involving the Sun, Moon, or chart ruler are most significant; name them in the Life Direction section if they involve the Nodes, or in the Overview if they link a luminary to a malefic or benefic.
- Chiron: long-term wound and healing gift; where it falls shows where serving others becomes possible
- Ceres: the nurturing axis — sign shows HOW the person gives and receives care; house shows WHERE; retrograde = early deprivation that becomes a fierce gift for nurturing others; Ceres-Moon or Ceres-Venus aspects intensify emotional caretaking
- Pallas: strategic and creative intelligence; sign shows the flavor of wisdom; house shows the arena; aspects to Mercury or Jupiter amplify pattern-recognition gifts; Pallas strong in the chart often indicates a counselor, strategist, or artist
- Juno: long-term partnership archetype — NOT just marriage; sign shows the quality sought in equals; house shows where equality or imbalance plays out; hard Juno aspects (square, opposition) to personal planets often correlate with relationship patterns worth naming honestly
- Vesta: the sacred flame and focused devotion — what the person is willing to sacrifice other things for; retrograde Vesta = a more internalized, private devotion; Vesta conjunct the Ascendant or Midheaven = a life devoted to a calling; integrate with the 6th and 12th houses for service and retreat themes
- Progressed Sun/Moon: the current psychological chapter and emotional climate
- Progressed sign change within ±2 years: a threshold event — name the approximate year
- Solar arc aspects within 1°: concrete external turning points (applying = within ~1 year); distinct from the more interior story of progressions
- Profection lord of the year: the single most important planet for the current 12-month period
- Priority hierarchy: outer-planet transits/arcs to natal ASC/MC/Sun/Moon > outer to personal planets > inner planet transits
- Upcoming transits (90-day window): these are the most actionable timing data — exact dates let you advise on specific windows. Mention the 2–3 most significant upcoming transits in Section 6 (Practical Guidance) with their approximate dates. A retrograde transiting planet (Rx) will often make the aspect 2–3 times; note this multi-pass pattern when present.
- Birth time confidence: when "approximate" or "unknown", treat Ascendant, house cusps, and house-based interpretations as possibilities rather than certainties; note the uncertainty explicitly and weight sign-based interpretations (unaffected by birth time) more heavily
- Solar return chart: the SR Ascendant and any angular planets are the dominant themes for the 12-month period from the return date; integrate the SR with the profection for a complete annual picture
- Anaretic degree (29°): a planet or angle at 29° carries life-level urgency — a chronic drive to resolve unfinished business in that sign's themes before moving on; if the chart ruler, a luminary, or the Ascendant is anaretic, this urgency colors the entire chart and should be named in the overview
- Planetary sect: day charts (Sun in houses 7–12) favor Sun, Jupiter, Saturn; night charts favor Moon, Venus, Mars. Out-of-sect malefics (Saturn in a night chart, Mars in a day chart) are the most destabilizing planets — their difficulties are less predictable and harder to channel; name this explicitly. Out-of-sect benefics give gifts but require intentional effort to access. In-sect malefics are still difficult but more structured and purposeful.
- Firdaria: the major lord's natal condition (sign, house, dignity, retrograde status) determines the biographical chapter's quality and difficulty. The sub-lord adds a texture layer within the major period. If the Firdaria major lord = profection lord of the year, that planet is doubly activated and should be flagged as the single most important planet right now. A retrograde or debilitated Firdaria lord = a challenging multi-year chapter requiring inner work.
- Vedic overlay: sidereal positions (Lahiri ayanamsa, ~24°) show where planets fall in the Jyotish zodiac — use these to add depth when the tropical and sidereal agree, or to note where the two systems diverge; the Moon's nakshatra is the most significant Vedic datum (governs Vimshottari timing and instinctive nature); the Navamsha (D9) shows soul-level qualities and marriage/dharma themes. Use Vedic data as a cross-system confirmation — note resonances, do not create contradictions with the Western reading.
- Vimshottari Dasha: the Mahadasha (major period, 6–20 years) sets the biographical backdrop; the Antardasha (sub-period, months to years) is the current texture within it. If the Mahadasha lord is the same as the Firdaria major lord, this is a profound convergence across both traditions — name it explicitly as the chart's single most dominant current theme. If the Dasha lord is also the profection lord of the year, all three timing systems point to the same planet — this is exceptional and must be flagged.
- Vedic Yogas: Pancha Mahapurusha yogas (Ruchaka/Bhadra/Hamsa/Malavya/Shasha) are among the most powerful signatures in Jyotish — a planet in its own sign or exaltation in an angular house (Kendra) creates exceptional talent in that planet's domain; integrate this with the Western chart's dominant planets and aspect patterns. Gajakesari Yoga (Jupiter in Kendra from Moon) is one of the most auspicious and common yogas — name it as a source of resilience and wisdom. Raj Yogas (Kendra-Trikona lord links) indicate potential for authority and worldly success; Parivartana Raj Yoga (sign exchange) is particularly potent. Neecha Bhanga Raj Yoga (cancelled debilitation) is a life-transforming signature — the early struggle described by the debilitation becomes the very source of exceptional strength. Dhana Yogas indicate financial capacity. Multiple yogas in the same chart compound each other. Name any yogas in Section 1 (Overview) if they involve the Sun, Moon, or Ascendant lord, or in Section 5 (Key Themes) if they involve other planets.
- Eclipse sensitivity: when a natal planet or angle is within 3° of a recent or upcoming eclipse, that planet/angle is eclipsed — its themes are both activated and destabilized for 6–12 months around the eclipse. A solar eclipse conjunct a natal planet = a reset and new chapter in that planet's domain; a lunar eclipse = an emotional culmination or release. Eclipse contacts to the ASC, MC, Sun, or Moon are life-level events. If multiple natal points are eclipsed simultaneously, the chart is in a period of accelerated change.
- Progressed lunation cycle: the angle of the Progressed Moon ahead of the Progressed Sun reveals the psychological phase the person is living in. New Moon phase = a beginning, planting seeds with little visibility; Crescent = effort and resistance; First Quarter = crisis of action; Gibbous = refinement and preparation; Full Moon = culmination, revelation, visibility; Disseminating = sharing and teaching; Last Quarter = crisis of consciousness, questioning structures; Balsamic = release, completion, preparing for a new cycle. The "years to next Progressed New Moon" is a countdown to the next major psychological reset — if under 3 years, the current cycle is ending and new seeds are forming.
- Fixed stars: only exact conjunctions (1° orb) matter — no other aspects. The 4 Royal Stars (Aldebaran, Regulus, Antares, Fomalhaut) conjunct a luminary or angle are life-defining signatures; Algol conjunct any personal planet or the Ascendant is the chart's most intense pressure point and must be named. Spica, Sirius, Vega near the Sun/Moon/Ascendant indicate distinctive gifts. Weave fixed stars into interpretation naturally — do not list them mechanically.

## Synthesis Protocol — Complete Mentally Before Writing
1. READ THE CONVERGENCE INTELLIGENCE BLOCK FIRST. These pre-computed findings are the chart's loudest signals — build the reading around them.
2. Check Eclipse Sensitivity: any eclipsed natal planet or angle is in an accelerated change period — weave this into sections 3 and 4.
3. Note the Progressed Lunation phase and years-to-next-New-Moon — this sets the psychological chapter and determines whether the person is in a building, culminating, or releasing season of life.
4. Scan all remaining predictive layers and identify any 2–3 additional themes not already captured by the convergences.
5. Rank urgency: convergence-flagged planets (highest) → eclipsed points → applying transit/arc within 0.5° (days–weeks) → within 1° (months) → within 3° (season) → progressions (years).

## Report Instructions
Write in warm, direct, personal language — speak TO this person, not ABOUT them. Every paragraph must name at least one specific planet, sign, degree, or house. Do not list placements — interpret them. Do not use hedging phrases like "might suggest" or "could indicate" — make clear statements grounded in the data.

Write these 7 sections:

**1. Personal Overview**
Open with the natal lunar phase as their fundamental life archetype. Then read Sun + Moon + Ascendant as a unified trio — what does this combination create? Note the chart ruler's sign/house and dignity: it colours the entire chart. If a fixed star conjuncts the Sun, Moon, Ascendant, or chart ruler, name it here as a life-defining quality. If any anaretic (29°) planets or angles exist, name the urgency theme. Name the out-of-sect malefic (if any) as a recurring source of friction. If a stellium dominates, give it prominence. Close with elemental/modal balance as an overall temperament portrait.

**2. Life Direction & Karmic Themes**
North Node (sign + house) = the unfamiliar direction this soul is stretching toward. South Node = ingrained gifts that become a comfort-zone trap. Place any aspect patterns here as structural life challenges or gifts — explain what the configuration *does* to this person's life trajectory, not just what the pattern is. Integrate Chiron's wound/gift.

**3. Current Life Phase**
Progressed Sun sign/house = the psychological chapter; what is being developed and released. Progressed Moon = the emotional climate in force for ~2.5 years. Name any progressed sign change within ±2 years and the approximate year it perfects. Highlight applying progressed aspects within 0.5° as what is crystallizing right now.

**4. Current Cosmic Climate**
Open with the three time lord layers together: the Firdaria major/sub period (Western biographical arc — years to decades), the Vimshottari Mahadasha/Antardasha (Vedic biographical arc — cross-system confirmation), and the profection year (annual focus). State what each lord is doing natally. If the Firdaria lord and Vimshottari Mahadasha lord are the same planet, say so explicitly — this is the chart's most dominant current theme across both traditions. Then present transits in priority order (outer planets to angles/luminaries first). For each significant transit, name: natal planet hit, house it rules, what area of life is activated, and approximate duration. Distinguish solar arc events ("a milestone arriving") from transiting weather ("a seasonal pressure"). If 3+ layers converge on one theme, say so directly.

**5. Key Life Themes** (exactly 3–4 themes)
Each theme must be supported by at least 2 independent chart factors. Draw from aspect patterns, natal dignity extremes, stelliums, mutual receptions, nodal axis, anaretic degrees, sect status, and fixed star conjunctions. A Royal Star on a luminary or angle, or Algol on a personal planet, is almost always a standalone life theme. The out-of-sect malefic, if present, almost always generates a permanent life theme. Name tensions honestly — if the chart shows a creative gift in friction with a structuring challenge, say what that dynamic produces and how to work with it.

**6. Practical Guidance**
3–4 specific, actionable items. Each must be tied to a specific applying transit, solar arc, or progressed aspect and include an approximate timeframe. Where the profection lord is involved, connect it explicitly: "Since [planet] rules your year and is currently [condition], this is the moment to..."

**7. Favorable Timing**
Name 2–3 specific windows with approximate timing. For each: what it is good for and why (cite the activating aspect). If the progressed Moon changes signs within 6 months, name the transition as a fresh emotional chapter and what it opens up.
{rectification_section}"""


def _build_followup_messages(
    state: "AstrologerState", chat_history: list[dict], question: str
) -> list[dict]:
    """Build the messages list for a follow-up question (shared by sync and stream variants)."""
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
        chart_summary = (
            f"{placements}"
            f"\n\nAnaretic Degrees (29°):\n{_format_anaretic_degrees(chart.get('anaretic_degrees') or [])}"
            f"\n\nFixed Star Conjunctions:\n{_format_fixed_stars(chart.get('fixed_stars') or [])}"
            f"\n\nPlanetary Sect:\n{_format_sect(chart.get('sect') or {})}"
            f"\n\nChart Ruler:\n{_format_chart_ruler(chart.get('chart_ruler'))}"
            f"\n\nLunar Phase:\n{_format_lunar_phase(chart.get('lunar_phase') or {})}"
            f"\n\nPart of Fortune:\n{_format_part_of_fortune(chart.get('part_of_fortune'))}"
            f"\n\nArabic Parts:\n{_format_arabic_parts(chart.get('arabic_parts') or {})}"
            f"\n\nAntiscia:\n{_format_antiscia(chart.get('antiscia') or [])}"
            f"\n\nStelliums:\n{_format_stelliums(chart.get('stelliums') or [])}"
            f"\n\nMutual Receptions:\n{_format_mutual_receptions(chart.get('mutual_receptions') or [])}"
            f"\n\nLunar Nodes:\n{_format_nodes(chart)}"
            f"\n\nNatal Aspects:\n{_format_aspects(chart.get('aspects') or [])}"
            f"\n\nAspect Patterns:\n{_format_aspect_patterns(chart.get('aspect_patterns') or [])}"
            f"\n\nCurrent Transits:\n{_format_transits(chart.get('transits') or [])}"
            f"\n\nUpcoming Transits (90 days):\n{_format_upcoming_transits(chart.get('upcoming_transits') or [])}"
            f"\n\nSecondary Progressions:\n{_format_progressions(chart.get('progressions'))}"
            f"\n\nProgressed Aspects to Natal:\n{_format_progressed_aspects(chart.get('progressed_aspects') or [])}"
            f"\n\nSolar Arc Directions:\n{_format_solar_arcs(chart.get('solar_arcs') or {})}"
            f"\n\nSolar Arc Aspects to Natal:\n{_format_solar_arc_aspects(chart.get('solar_arc_aspects') or [])}"
            f"\n\nAnnual Profection:\n{_format_profection(chart.get('profection'))}"
            f"\n\nFirdaria Time Lords:\n{_format_firdaria(chart.get('firdaria'), chart)}"
            f"\n\nSolar Return Chart:\n{_format_solar_return(chart.get('solar_return') or {})}"
            f"\n\nVedic (Jyotish) Overlay:\n{_format_vedic(chart.get('vedic'))}"
        )
    else:
        chart_summary = "Natal chart data unavailable."

    system = (
        f"You are a master Western astrologer. You have already provided a full reading for "
        f"{state['full_name']} (born {state['parsed_dob']} in {state['birth_location']}, "
        f"birth time {state['birth_time']} {state.get('birth_time_timezone', '')}).\n\n"
        f"Their chart data:\n{chart_summary}\n\n"
        "Answer follow-up questions by reasoning from the chart data above. Rules:\n"
        "- Every answer must cite at least one specific planet, degree, sign, or house from the chart\n"
        "- Applying transits and solar arcs are the most time-sensitive — lead with these when discussing timing\n"
        "- When multiple techniques point to the same theme, name the convergence\n"
        "- Do NOT invent placements, aspects, or transits not listed in the chart data above\n"
        "- Speak directly to the person: warm, concise, and actionable"
    )
    return [
        {"role": "system", "content": system},
        {"role": "assistant", "content": state["final_report"]},
        *chat_history,
        {"role": "user", "content": question},
    ]


def answer_followup(state: "AstrologerState", chat_history: list[dict], question: str) -> str:
    client = openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    messages = _build_followup_messages(state, chat_history, question)
    response = client.chat.completions.create(
        model="gpt-4o", max_tokens=1024, temperature=0.7, messages=messages
    )
    return response.choices[0].message.content


def answer_followup_stream(state: "AstrologerState", chat_history: list[dict], question: str):
    """Streaming variant — yields text chunks for use with st.write_stream()."""
    client = openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    messages = _build_followup_messages(state, chat_history, question)
    with client.chat.completions.create(
        model="gpt-4o", max_tokens=1024, temperature=0.7, stream=True, messages=messages
    ) as stream:
        for chunk in stream:
            content = chunk.choices[0].delta.content
            if content:
                yield content


def _fmt_syn_planet(label: str, chart: dict, key: str) -> str:
    d = chart.get(key)
    if not d:
        return f"- {label}: unavailable"
    retro = " (Rx)" if d.get("retrograde") else ""
    dignity = f" [{d['dignity']}]" if d.get("dignity") else ""
    house = f", H{d['house']}" if d.get("house") else ""
    return f"- {label}: {d['sign']} {d['position']}°{retro}{dignity}{house}"


def _format_cross_aspects(aspects: list[dict], name_a: str, name_b: str) -> str:
    if not aspects:
        return "No major inter-chart aspects within 6° orb."
    lines = []
    for a in aspects[:30]:  # cap at 30 for prompt length
        pa = a["planet_a"].replace("_", " ").title()
        pb = a["planet_b"].replace("_", " ").title()
        direction = "applying" if a.get("applying") else "separating"
        lines.append(f"- {name_a}'s {pa} {a['aspect']} {name_b}'s {pb} (orb {a['orb']}°, {direction})")
    return "\n".join(lines)


def _format_house_overlays(overlays: list[dict], guest_name: str, host_name: str) -> str:
    if not overlays:
        return "House overlay data unavailable."
    lines = []
    key_planets = {"sun", "moon", "venus", "mars", "ascendant", "mercury", "jupiter", "saturn"}
    for o in overlays:
        if o["planet"] not in key_planets:
            continue
        p = o["planet"].replace("_", " ").title()
        lines.append(f"- {guest_name}'s {p} ({o['sign']}) falls in {host_name}'s House {o['house_in_partner']}")
    return "\n".join(lines)


def _format_composite(composite: dict, aspects: list[dict]) -> str:
    if not composite:
        return "Composite chart unavailable."
    lines = ["(Midpoint composite — the relationship as its own entity)"]
    for key, label in [
        ("sun", "Composite Sun"), ("moon", "Composite Moon"),
        ("ascendant", "Composite Ascendant"), ("venus", "Composite Venus"),
        ("mars", "Composite Mars"), ("saturn", "Composite Saturn"),
        ("midheaven", "Composite Midheaven"),
    ]:
        d = composite.get(key)
        if d:
            dignity = f" [{d['dignity']}]" if d.get("dignity") else ""
            lines.append(f"- {label}: {d['sign']} {d['position']}°{dignity}")
    # Top composite aspects
    if aspects:
        lines.append("\nComposite aspects (top 8):")
        for a in aspects[:8]:
            p1 = a["planet1"].replace("_", " ").title()
            p2 = a["planet2"].replace("_", " ").title()
            lines.append(f"- {p1} {a['aspect']} {p2} (orb {a['orb']}°)")
    return "\n".join(lines)


def _compute_synastry_convergences(
    name_a: str, chart_a: dict,
    name_b: str, chart_b: dict,
    synastry: dict,
) -> list[str]:
    """Pre-compute the most significant synastry patterns for prompt injection."""
    convergences = []
    cross_aspects = synastry.get("cross_aspects") or []
    overlays_b_in_a = synastry.get("house_overlays_b_in_a") or []
    overlays_a_in_b = synastry.get("house_overlays_a_in_b") or []
    composite = synastry.get("composite") or {}

    # Bucket aspects by sorted planet-pair key
    pairs: dict[tuple, list[dict]] = {}
    for a in cross_aspects:
        pa = (a.get("planet_a") or "").lower()
        pb = (a.get("planet_b") or "").lower()
        if not pa or not pb:
            continue
        key = tuple(sorted([pa, pb]))
        pairs.setdefault(key, []).append(a)

    # Mutual luminaries: A's Sun→B's Moon AND A's Moon→B's Sun
    sun_moon_aspects = pairs.get(("moon", "sun"), [])
    if len(sun_moon_aspects) >= 2:
        descs = []
        for a in sun_moon_aspects:
            pa = (a.get("planet_a") or "").title()
            pb = (a.get("planet_b") or "").title()
            owner_a = name_a if a.get("planet_a", "").lower() == "sun" else name_b
            owner_b = name_b if a.get("planet_b", "").lower() == "moon" else name_a
            direction = "applying" if a.get("applying") else "separating"
            descs.append(f"{name_a}'s {pa} {a['aspect']} {name_b}'s {pb} (orb {a['orb']}°, {direction})")
        convergences.append(
            f"MUTUAL LUMINARIES — Both Sun-Moon inter-aspects exist: "
            + " AND ".join(descs)
            + f". The deepest compatibility bond: each person's identity nourishes the other's emotional world. "
            f"This connection has a natural rhythm of give-and-receive that sustains long-term bonds."
        )
    elif sun_moon_aspects:
        a = sun_moon_aspects[0]
        pa = (a.get("planet_a") or "").title()
        pb = (a.get("planet_b") or "").title()
        direction = "applying" if a.get("applying") else "separating"
        convergences.append(
            f"SUN-MOON INTER-ASPECT — {name_a}'s {pa} {a['aspect']} {name_b}'s {pb} "
            f"(orb {a['orb']}°, {direction}). The most fundamental compatibility signature: "
            f"one person's core identity and the other's emotional nature are directly linked."
        )

    # Double whammies (non-luminary pairs appearing multiple times)
    for pair, aspects in pairs.items():
        if pair == ("moon", "sun"):
            continue  # handled above
        if len(aspects) >= 2:
            p1, p2 = pair
            descs = []
            for a in aspects[:3]:
                direction = "applying" if a.get("applying") else "separating"
                descs.append(
                    f"{name_a}'s {(a.get('planet_a') or '').title()} "
                    f"{a['aspect']} {name_b}'s {(a.get('planet_b') or '').title()} "
                    f"(orb {a['orb']}°, {direction})"
                )
            convergences.append(
                f"DOUBLE WHAMMY — {p1.title()}-{p2.title()} connected in {len(aspects)} aspects: "
                + " AND ".join(descs)
                + f". This planet-pair is the central axis of the connection — its themes are unavoidable and defining."
            )

    # Saturn cross-aspects to luminaries (hard aspects only)
    saturn_contacts = []
    hard_aspects = {"square", "opposition", "conjunction"}
    for a in cross_aspects:
        pa = (a.get("planet_a") or "").lower()
        pb = (a.get("planet_b") or "").lower()
        asp = (a.get("aspect") or "").lower()
        if asp not in hard_aspects:
            continue
        if pa == "saturn" and pb in ("sun", "moon"):
            direction = "applying" if a.get("applying") else "separating"
            saturn_contacts.append(
                f"{name_a}'s Saturn {a['aspect']} {name_b}'s {pb.title()} (orb {a['orb']}°, {direction})"
            )
        elif pb == "saturn" and pa in ("sun", "moon"):
            direction = "applying" if a.get("applying") else "separating"
            saturn_contacts.append(
                f"{name_b}'s Saturn {a['aspect']} {name_a}'s {pa.title()} (orb {a['orb']}°, {direction})"
            )
    if saturn_contacts:
        convergences.append(
            f"SATURN-LUMINARY CONTACT — {'; '.join(saturn_contacts)}. "
            f"The relationship's primary structural dynamic: reality-testing, discipline, and long-term commitment. "
            f"Can feel restricting early; becomes deeply stabilizing when worked with consciously."
        )

    # Angular planet overlays (guest planet in host's houses 1, 4, 7, 10)
    angular_houses = {1, 4, 7, 10}
    angular_overlays = []
    for o in overlays_b_in_a:
        try:
            if int(o.get("house_in_partner", 0)) in angular_houses:
                p = o["planet"].replace("_", " ").title()
                angular_overlays.append(f"{name_b}'s {p} in {name_a}'s House {o['house_in_partner']}")
        except (TypeError, ValueError):
            pass
    for o in overlays_a_in_b:
        try:
            if int(o.get("house_in_partner", 0)) in angular_houses:
                p = o["planet"].replace("_", " ").title()
                angular_overlays.append(f"{name_a}'s {p} in {name_b}'s House {o['house_in_partner']}")
        except (TypeError, ValueError):
            pass
    if len(angular_overlays) >= 3:
        convergences.append(
            f"ANGULAR SATURATION — {len(angular_overlays)} planets fall in angular houses (1/4/7/10): "
            + "; ".join(angular_overlays[:5])
            + ". Angular overlays create visceral, structural activation — these people fundamentally reshape each other's life."
        )
    elif angular_overlays:
        for ov in angular_overlays[:2]:
            convergences.append(f"ANGULAR OVERLAY — {ov}: a planet on the other's angle creates deep, fated-feeling activation of that life area.")

    # Composite planets in angular houses (1, 4, 7, 10)
    composite_angular = []
    for planet in ["sun", "moon", "venus", "mars", "jupiter", "saturn"]:
        p = composite.get(planet)
        try:
            if p and int(p.get("house", 0)) in angular_houses:
                composite_angular.append(f"Composite {planet.title()} in House {p['house']}")
        except (TypeError, ValueError):
            pass
    if composite_angular:
        convergences.append(
            f"COMPOSITE ANGULAR PLANETS — " + "; ".join(composite_angular)
            + ". Planets in the composite chart's angular houses are the relationship's most visible and defining qualities."
        )

    return convergences


def build_synastry_prompt(
    name_a: str, dob_a: str, loc_a: str, chart_a: dict,
    name_b: str, dob_b: str, loc_b: str, chart_b: dict,
    synastry: dict,
) -> str:
    key_placements = ["sun", "moon", "ascendant", "midheaven", "venus", "mars", "mercury", "jupiter", "saturn",
                      "chiron", "ceres", "juno", "vesta", "pallas"]

    section_a = "\n".join([
        f"## {name_a}'s Chart (Person A) — born {dob_a}, {loc_a}",
        *[_fmt_syn_planet(k.capitalize(), chart_a, k) for k in key_placements],
    ])
    section_b = "\n".join([
        f"## {name_b}'s Chart (Person B) — born {dob_b}, {loc_b}",
        *[_fmt_syn_planet(k.capitalize(), chart_b, k) for k in key_placements],
    ])
    cross_section = (
        f"## Inter-Chart Aspects (A ↔ B, 6° orb)\n"
        + _format_cross_aspects(synastry.get("cross_aspects") or [], name_a, name_b)
    )
    overlay_ba = (
        f"## House Overlays — {name_b}'s planets in {name_a}'s houses\n"
        + _format_house_overlays(synastry.get("house_overlays_b_in_a") or [], name_b, name_a)
    )
    overlay_ab = (
        f"## House Overlays — {name_a}'s planets in {name_b}'s houses\n"
        + _format_house_overlays(synastry.get("house_overlays_a_in_b") or [], name_a, name_b)
    )
    comp_section = (
        "## Composite Chart\n"
        + _format_composite(synastry.get("composite") or {}, synastry.get("composite_aspects") or [])
    )

    syn_convergences = _compute_synastry_convergences(name_a, chart_a, name_b, chart_b, synastry)
    syn_convergence_block = ""
    if syn_convergences:
        syn_convergence_block = (
            "\n## ⚡ Synastry Convergence Intelligence (Pre-Computed — Highest Priority)\n"
            "These patterns were detected before reading the data. Address each explicitly in the report:\n\n"
            + "\n\n".join(f"▶ {c}" for c in syn_convergences)
            + "\n"
        )

    return f"""You are a master relationship astrologer writing a synastry compatibility reading for {name_a} and {name_b}.

Use only the chart data provided. Do NOT invent aspects, placements, or positions not listed below.
{syn_convergence_block}
{section_a}

{section_b}

{cross_section}

{overlay_ba}

{overlay_ab}

{comp_section}

## Reference: Synastry Interpretation Rules
- Sun-Moon inter-aspects are the most fundamental compatibility signature — they show whether the two life forces naturally support each other
- Venus-Mars inter-aspects describe physical attraction and desire; Venus-Venus shows aesthetic harmony; Moon-Moon shows instinctive emotional resonance
- Saturn cross-aspects (Saturn conjunct/square/opposite a personal planet) show where one person disciplines or restricts the other — challenging but stabilizing if handled consciously
- Outer planet cross-aspects (Uranus, Neptune, Pluto to personal planets) are generational and often feel fated or overwhelming — name what they activate without catastrophizing
- House overlays: where the guest planet falls is the area of the host's life most activated by the relationship. B's Sun in A's 7th = the relationship feels like a partnership archetype for A; B's Moon in A's 4th = emotional domesticity; B's Venus in A's 5th = romance and play
- Composite chart = the relationship's own natal chart. Composite Sun and Moon show the relationship's identity and emotional core; composite Saturn shows where it needs discipline and structure; composite Venus shows its pleasures; challenging composite aspects describe the relationship's own growth edges
- Rank aspects by significance: Sun/Moon/ASC inter-aspects first, Venus-Mars second, Mercury communication third, Saturn structural fourth, outer planets last
- Be honest about tensions — a hard Saturn square is a real challenge, not a blessing in disguise; frame it constructively but truthfully

## Report Instructions
Speak to both people together ("you two", "between you", "in this connection"). Every paragraph must cite at least one specific planet, sign, degree, or house from the data. Do not list aspects mechanically — weave them into interpretive statements.

Write these 6 sections:

**1. The Connection at a Glance**
2–3 sentences summarizing the dominant quality of this synastry. What is the single most striking aspect or pattern? What archetype best describes this connection?

**2. How You Experience Each Other**
Use house overlays. Where do each person's key planets (Sun, Moon, Venus) land in the other's chart? What areas of life does each person illuminate or activate for the other?

**3. Attraction, Chemistry & Emotional Resonance**
Lead with Sun-Moon, Moon-Moon, and Venus-Mars inter-aspects. What draws these two together instinctively? What does emotional attunement look like between them?

**4. Communication, Growth & Long-Term Compatibility**
Mercury aspects for communication style match. Jupiter aspects for where they inspire each other. Saturn cross-aspects for the relationship's structure, stability, and growth edges — name any Saturn tensions honestly.

**5. The Relationship as Its Own Entity**
Read the composite chart: composite Sun + Moon sign/house as the relationship's identity and emotional tone. Any composite aspect patterns or strongly dignified/debilitated composite planets as defining qualities of the bond.

**6. Strengths & Growth Edges**
2–3 concrete strengths supported by the data. 1–2 honest growth edges (challenges this connection will need to navigate consciously). End with a grounding statement about what makes this connection meaningful, whatever its form.
"""


_SYNASTRY_SYSTEM = (
    "You are a master relationship astrologer who reads synastry with psychological depth and compassion. "
    "You balance honesty about challenges with genuine recognition of gifts. You never catastrophize "
    "difficult aspects, and you never oversell easy ones. Every statement is grounded in specific "
    "chart data. You speak warmly and directly to the people, not about them."
)


def generate_synastry_report(
    name_a: str, dob_a: str, loc_a: str, chart_a: dict,
    name_b: str, dob_b: str, loc_b: str, chart_b: dict,
    synastry: dict,
) -> str:
    client = openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    prompt = build_synastry_prompt(name_a, dob_a, loc_a, chart_a, name_b, dob_b, loc_b, chart_b, synastry)
    response = client.chat.completions.create(
        model="gpt-4o",
        max_tokens=3000,
        temperature=0.7,
        messages=[
            {"role": "system", "content": _SYNASTRY_SYSTEM},
            {"role": "user", "content": prompt},
        ],
    )
    return response.choices[0].message.content


def generate_synastry_report_stream(
    name_a: str, dob_a: str, loc_a: str, chart_a: dict,
    name_b: str, dob_b: str, loc_b: str, chart_b: dict,
    synastry: dict,
):
    """Streaming variant — yields text chunks for use with st.write_stream()."""
    client = openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    prompt = build_synastry_prompt(name_a, dob_a, loc_a, chart_a, name_b, dob_b, loc_b, chart_b, synastry)
    with client.chat.completions.create(
        model="gpt-4o",
        max_tokens=3000,
        temperature=0.7,
        stream=True,
        messages=[
            {"role": "system", "content": _SYNASTRY_SYSTEM},
            {"role": "user", "content": prompt},
        ],
    ) as stream:
        for chunk in stream:
            content = chunk.choices[0].delta.content
            if content:
                yield content


def answer_synastry_followup_stream(
    name_a: str, dob_a: str, chart_a: dict,
    name_b: str, dob_b: str, chart_b: dict,
    synastry: dict, synastry_report: str,
    chat_history: list[dict], question: str,
):
    """Streaming follow-up for synastry questions."""
    client = openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    cross = _format_cross_aspects(synastry.get("cross_aspects") or [], name_a, name_b)
    comp = _format_composite(synastry.get("composite") or {}, synastry.get("composite_aspects") or [])
    system = (
        f"You are a master relationship astrologer. You have already written a synastry reading for "
        f"{name_a} (born {dob_a}) and {name_b} (born {dob_b}).\n\n"
        f"Key inter-chart aspects:\n{cross}\n\n"
        f"Composite chart:\n{comp}\n\n"
        "Answer follow-up questions by reasoning from the chart data above. "
        "Cite specific planets, signs, and houses. Be warm, direct, and grounded in the data. "
        "Do NOT invent aspects or placements not listed above."
    )
    messages = [
        {"role": "system", "content": system},
        {"role": "assistant", "content": synastry_report},
        *chat_history,
        {"role": "user", "content": question},
    ]
    with client.chat.completions.create(
        model="gpt-4o", max_tokens=1024, temperature=0.7, stream=True, messages=messages
    ) as stream:
        for chunk in stream:
            content = chunk.choices[0].delta.content
            if content:
                yield content


_REPORT_SYSTEM = (
    "You are a master astrologer fluent in both Western and Vedic (Jyotish) traditions. "
    "You synthesize natal, transit, progression, solar arc, Hellenistic, and Vedic techniques "
    "into coherent, personally grounded readings. You think in themes first — identify dominant "
    "patterns across all layers, then show how each technique confirms them. When the Firdaria "
    "major lord and Vimshottari Mahadasha lord are the same planet, you name this cross-tradition "
    "convergence explicitly. You never make vague generalizations. Every statement is anchored to "
    "specific planets, degrees, and houses. You speak directly and warmly to the person, as if "
    "sitting across from them."
)


def generate_report(state: "AstrologerState") -> str:
    client = openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    response = client.chat.completions.create(
        model="gpt-4o",
        max_tokens=4096,
        temperature=0.7,
        messages=[
            {"role": "system", "content": _REPORT_SYSTEM},
            {"role": "user", "content": build_prompt(state)},
        ],
    )
    return response.choices[0].message.content


def generate_report_stream(state: "AstrologerState"):
    """Streaming variant — yields text chunks for st.write_stream()."""
    client = openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    with client.chat.completions.create(
        model="gpt-4o",
        max_tokens=4096,
        temperature=0.7,
        stream=True,
        messages=[
            {"role": "system", "content": _REPORT_SYSTEM},
            {"role": "user", "content": build_prompt(state)},
        ],
    ) as stream:
        for chunk in stream:
            content = chunk.choices[0].delta.content
            if content:
                yield content
