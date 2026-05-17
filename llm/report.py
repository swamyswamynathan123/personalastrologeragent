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


def _format_retrograde_stations(stations: list[dict]) -> str:
    if not stations:
        return "No outer planet stations within 3° of a natal point in the ±180-day window."
    lines = []
    for s in stations:
        planet = s["planet"].capitalize()
        stype = s.get("station_type", "station")
        date = s.get("date", "unknown")
        sign = s.get("sign", "?")
        pos = s.get("position", "?")
        days = s.get("days_from_now", 0)
        past = s.get("past", False)
        try:
            timing = f"{abs(int(days))} days ago" if past else f"in {int(days)} days"
        except (TypeError, ValueError):
            timing = "timing unknown"
        contacts = s.get("natal_contacts") or []
        if contacts:
            contact_strs = [
                f"within {c['orb']}° of natal {c['body'].replace('_', ' ').title()}"
                for c in contacts
            ]
            lines.append(
                f"- {planet} stations {stype} at {sign} {pos}° on {date} ({timing}) — {'; '.join(contact_strs)}"
            )
        else:
            lines.append(f"- {planet} stations {stype} at {sign} {pos}° on {date} ({timing})")
    return "\n".join(lines)


def _format_transit_to_progressed(aspects: list[dict]) -> str:
    if not aspects:
        return "No outer-planet transits to progressed positions within 3° orb."
    lines = []
    for a in aspects:
        tp = a["transiting_planet"].capitalize()
        pp = a["progressed_planet"].replace("_", " ").title()
        retro = " (Rx)" if a.get("retrograde") else ""
        direction = "applying" if a.get("applying") else "separating"
        lines.append(
            f"- Transiting {tp}{retro} {a['aspect']} progressed {pp} (orb {a['orb']}°, {direction})"
        )
    return "\n".join(lines)


def _format_primary_directions(directions: list[dict]) -> str:
    if not directions:
        return "No primary directions within 1° orb at this age (Naibod rate, 1° ARMC ≈ 1 year)."
    lines = []
    for d in directions:
        dp = d["directed_point"]
        np_ = d["natal_point"].replace("_", " ").title()
        sign = d.get("directed_sign", "?")
        pos = d.get("directed_pos", "?")
        lines.append(
            f"- {dp} ({sign} {pos}°) {d['aspect']} natal {np_} (orb {d['orb']}°)"
        )
    return "\n".join(lines)


def _format_lunar_return(lr: dict) -> str:
    if not lr:
        return "Lunar return chart unavailable."
    lines = [
        f"(Next lunar return: {lr.get('return_date', '?')} at {lr.get('return_time', '?')} — "
        f"Moon returns to natal degree; cast at current location)"
    ]
    asc = lr.get("ascendant")
    mc = lr.get("midheaven")
    moon = lr.get("moon")
    if asc:
        lines.append(f"- LR Ascendant: {asc['sign']} {asc['position']}° — the month's energy filter and self-presentation")
    if mc:
        lines.append(f"- LR Midheaven: {mc['sign']} {mc['position']}° — the month's career/public focus")
    if moon:
        house = f", LR House {moon['house']}" if moon.get("house") else ""
        natal_h = f" (natal House {moon['natal_house']})" if moon.get("natal_house") else ""
        lines.append(f"- LR Moon: {moon['sign']} {moon['position']}°{house}{natal_h} — emotional center of the month")
    angular = lr.get("angular_planets") or []
    if angular:
        ang_str = "; ".join(
            f"{a['planet'].capitalize()} conjunct LR {a['angle'].replace('_', ' ').title()} (orb {a['orb']}°)"
            for a in angular
        )
        lines.append(f"- Angular planets (dominant this month): {ang_str}")
    stellia = lr.get("stellia") or {}
    for house_str, planets in stellia.items():
        theme = _HOUSE_THEMES.get(int(house_str), f"House {house_str}")
        lines.append(
            f"- LR House {house_str} ({theme}) occupied by {', '.join(planets)} — concentrated monthly focus"
        )
    return "\n".join(lines)


def _format_transit_passes(passes: list[dict]) -> str:
    if not passes:
        return "No outer-planet transits within 0.5° orb over the next 12 months."
    lines = []
    for p in passes:
        tp = p["transiting_planet"].capitalize()
        np_ = p["natal_planet"].replace("_", " ").title()
        pass_list = p.get("passes") or []
        if not pass_list:
            continue
        if p.get("multi_pass"):
            pass_strs = []
            for ps in pass_list:
                retro = " (Rx)" if ps.get("retrograde") else " (Direct)"
                pass_strs.append(f"{ps['date']}{retro} orb {ps['orb']}°")
            lines.append(
                f"- {tp} {p['aspect']} natal {np_} — **{len(pass_list)} passes**: {' → '.join(pass_strs)}"
            )
        else:
            ps = pass_list[0]
            retro = " (Rx)" if ps.get("retrograde") else ""
            lines.append(
                f"- {tp}{retro} {p['aspect']} natal {np_} — exact ~{ps['date']} (orb {ps['orb']}°)"
            )
    return "\n".join(lines) if lines else "No outer-planet transits within 0.5° orb over the next 12 months."


def _format_almuten_figuris(almuten: dict | None) -> str:
    if not almuten:
        return "Almuten Figuris (Chart Ruler by Dignity) unavailable."
    planet = almuten.get("planet", "?").capitalize()
    score = almuten.get("score", "?")
    sign = almuten.get("sign", "?")
    house = almuten.get("house")
    dignity = almuten.get("dignity", "")
    runner_up = (almuten.get("runner_up") or "").capitalize()
    runner_score = almuten.get("runner_up_score", "?")
    retro = " (Rx)" if almuten.get("retrograde") else ""
    house_str = f", House {house}" if house else ""
    dignity_str = f" — {dignity}" if dignity else ""
    runner_str = f" (runner-up: {runner_up} at {runner_score} pts)" if runner_up else ""
    all_scores = almuten.get("all_scores") or {}
    breakdown_str = ""
    if all_scores:
        scored = sorted(all_scores.items(), key=lambda x: -x[1])[:4]
        parts = ", ".join(f"{p.capitalize()} {v}pts" for p, v in scored if v > 0)
        if parts:
            breakdown_str = f"\n  Top scorers: {parts}"
    return (
        f"- **{planet}**{retro} in {sign}{house_str}{dignity_str} — "
        f"scores {score} dignity points as Chart Master{runner_str}{breakdown_str}"
    )


def _format_house_rulerships(chart: dict) -> str:
    """Compact ruler-per-house table plus cross-house links."""
    houses = chart.get("houses") or {}
    if not houses:
        return "House rulership summary unavailable."

    lines = ["(Ruler = planet whose sign is on that house cusp; its natal condition governs that life area)"]

    ruler_to_houses: dict[str, list[int]] = {}
    cross_links: list[str] = []

    for num in range(1, 13):
        h = houses.get(str(num))
        if not h or not h.get("sign"):
            continue
        ruler = h.get("ruler") or {}
        planet = ruler.get("planet", "")
        ruler_house = ruler.get("house")
        ruler_sign = ruler.get("sign", "?")
        retro = " Rx" if ruler.get("retrograde") else ""
        dignity = f" [{ruler['dignity']}]" if ruler.get("dignity") else ""
        theme = _HOUSE_THEMES.get(num, "")
        house_str = f", H{ruler_house}" if ruler_house else ""
        lines.append(
            f"- H{num} ({theme}): {h['sign']} → {planet.capitalize()}{retro}"
            f" in {ruler_sign}{dignity}{house_str}"
        )
        if planet:
            ruler_to_houses.setdefault(planet, []).append(num)
        if ruler_house and ruler_house != num:
            try:
                rh = int(ruler_house)
                a_theme = _HOUSE_THEMES.get(num, f"H{num}")
                b_theme = _HOUSE_THEMES.get(rh, f"H{rh}")
                cross_links.append(
                    f"  H{num} ruler ({planet.capitalize()}) sits in H{rh}"
                    f" → {a_theme} ↔ {b_theme} are interlinked for this person"
                )
            except (TypeError, ValueError):
                pass

    # Flag planets ruling two houses (mutual house themes)
    for planet, ruled in ruler_to_houses.items():
        if len(ruled) >= 2:
            themes = " + ".join(_HOUSE_THEMES.get(h, f"H{h}") for h in ruled)
            lines.append(
                f"  {planet.capitalize()} rules H{' & H'.join(str(h) for h in ruled)}"
                f" — {themes} are governed by the same planet; its activations affect both areas"
            )

    if cross_links:
        lines.append("\nCross-house links (ruler of A sits in B = those life areas interact):")
        lines.extend(cross_links[:10])

    return "\n".join(lines)


def _format_dignity_hierarchy(chart: dict) -> str:
    """Rank the seven traditional planets by dignity for prediction weighting."""
    _PLANETS_CLASSIC = ["sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn"]
    strongest, weakest = [], []
    for p in _PLANETS_CLASSIC:
        d = chart.get(p)
        if not d:
            continue
        dignity = d.get("dignity", "")
        name = p.capitalize()
        sign = d.get("sign", "?")
        house = d.get("house")
        house_str = f", H{house}" if house else ""
        retro = " Rx" if d.get("retrograde") else ""
        label = f"{name} [{dignity}] in {sign}{house_str}{retro}"
        if dignity in ("domicile", "exaltation"):
            strongest.append(label)
        elif dignity in ("detriment", "fall"):
            weakest.append(label)

    lines = []
    if strongest:
        lines.append(
            "Most dignified — predictions involving these planets flow constructively:\n  "
            + "; ".join(strongest)
        )
    if weakest:
        lines.append(
            "Most challenged — their transits/periods carry friction; do NOT describe as straightforwardly positive:\n  "
            + "; ".join(weakest)
        )
    if not lines:
        lines.append(
            "No planets in domicile, exaltation, detriment, or fall — "
            "peregrine dignity throughout; tone of predictions is neutral to mixed."
        )
    return "\n".join(lines)


def _format_dispositor_tree(tree: dict | None) -> str:
    if not tree:
        return "Dispositor tree unavailable."
    lines = []
    chains = tree.get("chains") or {}
    final = tree.get("final_dispositors") or []
    single = tree.get("single_final_dispositor")
    mutual = tree.get("mutual_reception_cycles") or []

    if single:
        planet = single.capitalize()
        chain_info = chains.get(single.lower()) or []
        dependents = [p.capitalize() for p in chain_info if p.lower() != single.lower()]
        dep_str = f" (disposits: {', '.join(dependents)})" if dependents else ""
        lines.append(
            f"- **Sole Final Dispositor: {planet}**{dep_str} — all planets ultimately trace their "
            f"sign rulership to {planet}. This planet's natal condition colors the entire chart."
        )
    elif final:
        finals_str = " + ".join(p.capitalize() for p in final)
        lines.append(f"- Final dispositors: **{finals_str}** — the chart's authority is split between these planets.")

    if mutual:
        for cycle in mutual:
            cycle_str = " ↔ ".join(p.capitalize() for p in cycle)
            lines.append(f"- Mutual reception cycle: {cycle_str} — these planets exchange rulership power.")

    return "\n".join(lines) if lines else "No single final dispositor; chart power is distributed."


def _format_parallel_aspects(aspects: list[dict], declinations: dict) -> str:
    if not aspects:
        return "No parallel or contra-parallel aspects within 1° orb."
    lines = []
    for a in aspects:
        pa = a["planet_a"].replace("_", " ").title()
        pb = a["planet_b"].replace("_", " ").title()
        kind = a["type"].replace("-", "-")
        dec_a = a["dec_a"]
        dec_b = a["dec_b"]
        hem_a = "N" if dec_a >= 0 else "S"
        hem_b = "N" if dec_b >= 0 else "S"
        lines.append(
            f"- {pa} {kind} {pb} (orb {a['orb']}°) — "
            f"dec {abs(dec_a)}°{hem_a} / {abs(dec_b)}°{hem_b}"
        )
    return "\n".join(lines)


def _format_monthly_profection(profection: dict | None) -> str:
    if not profection:
        return ""
    monthly_house = profection.get("monthly_house")
    monthly_sign = profection.get("monthly_house_sign")
    monthly_lord = (profection.get("monthly_lord") or "").capitalize()
    monthly_lord_sign = profection.get("monthly_lord_sign")
    monthly_lord_house = profection.get("monthly_lord_house")
    months_elapsed = profection.get("months_elapsed", 0)
    if not monthly_house:
        return ""
    lord_str = ""
    if monthly_lord:
        lord_detail = f" in {monthly_lord_sign}" if monthly_lord_sign else ""
        lord_house = f", House {monthly_lord_house}" if monthly_lord_house else ""
        lord_str = f"; monthly lord: **{monthly_lord}**{lord_detail}{lord_house}"
    return (
        f"- Monthly profection (month {months_elapsed + 1} of year): "
        f"**House {monthly_house}** ({monthly_sign or '?'}){lord_str}"
    )


def _format_prenatal_syzygy(syzygy: dict | None) -> str:
    if not syzygy:
        return "Prenatal lunation (syzygy) unavailable."
    kind = "New Moon" if syzygy.get("type") == "new_moon" else "Full Moon"
    eclipse_note = ""
    if syzygy.get("was_eclipse"):
        label = syzygy.get("eclipse_label", "eclipse").replace("_", " ").title()
        eclipse_note = f" ⚡ **This was a {label}** — the syzygy degree carries eclipse-level intensity."
    return (
        f"- Prenatal {kind}: **{syzygy.get('sign', '?')} {syzygy.get('position', '?')}°** "
        f"(abs {syzygy.get('abs_pos', '?')}°) — {syzygy.get('date', '?')} {syzygy.get('time', '')}"
        f"{eclipse_note}\n"
        f"  Transits and directions within 3° of this degree resonate chart-wide."
    )


def _format_minor_aspects(aspects: list[dict]) -> str:
    if not aspects:
        return "No minor aspects within orb."
    quintile_family = {"Quintile", "Biquintile"}
    friction_family = {"Semisquare", "Sesquiquadrate"}
    lines = []
    for a in aspects:
        p1 = a["planet1"].replace("_", " ").title()
        p2 = a["planet2"].replace("_", " ").title()
        asp = a["aspect"]
        orb = a["orb"]
        applying = a.get("applying")
        app_str = " (applying)" if applying else " (separating)" if applying is False else ""
        # Category tag for the LLM
        if asp in quintile_family:
            tag = " [creative/talent]"
        elif asp in friction_family:
            tag = " [friction/irritant]"
        elif asp == "Quincunx":
            tag = " [adjustment/redirection]"
        elif asp == "Semisextile":
            tag = " [subtle resource]"
        else:
            tag = ""
        lines.append(f"- {p1} {asp} {p2} (orb {orb}°){app_str}{tag}")
    return "\n".join(lines)


def _format_parans(parans: list[dict]) -> str:
    if not parans:
        return "No natal parans within 1.5° orb."
    lines = []
    for p in parans:
        pa = p["planet_a"].capitalize()
        pb = p["planet_b"].capitalize()
        aa = p["angle_a"]
        ab = p["angle_b"]
        orb = p["orb"]
        lines.append(
            f"- {pa} {aa} / {pb} {ab} (orb {orb}°) — "
            f"these planets are woven together at the angular level"
        )
    return "\n".join(lines)


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

    # House-level convergence: multiple independent techniques targeting the same house
    house_activations: dict[int, list[str]] = {}

    prof_house = profection.get("profected_house")
    if prof_house:
        try:
            house_activations.setdefault(int(prof_house), []).append("annual profection")
        except (TypeError, ValueError):
            pass

    prof_lord_house = profection.get("lord_house")
    if prof_lord_house and prof_lord:
        try:
            house_activations.setdefault(int(prof_lord_house), []).append(
                f"{prof_lord.capitalize()} (year lord) resides here"
            )
        except (TypeError, ValueError):
            pass

    if fird_major:
        fird_data = chart.get(fird_major) or {}
        fird_house = fird_data.get("house")
        if fird_house:
            try:
                house_activations.setdefault(int(fird_house), []).append(
                    f"{fird_major.capitalize()} (Firdaria lord) resides here"
                )
            except (TypeError, ValueError):
                pass

    solar_return = chart.get("solar_return") or {}
    sr_house_map: dict[str, list[str]] = {}
    for planet in _SR_PLANETS:
        p = solar_return.get(planet)
        if p and p.get("house"):
            sr_house_map.setdefault(str(p["house"]), []).append(planet)
    for house_str, sr_planets in sr_house_map.items():
        if len(sr_planets) >= 2:
            try:
                label = ", ".join(p.capitalize() for p in sr_planets)
                house_activations.setdefault(int(house_str), []).append(
                    f"solar return stellium ({label})"
                )
            except (TypeError, ValueError):
                pass

    for t in transits:
        np_key = (t.get("natal_planet") or "").lower()
        tp_key = (t.get("transiting_planet") or "").lower()
        if tp_key in outer_planets and np_key:
            np_data = chart.get(np_key) or {}
            np_house = np_data.get("house")
            if np_house:
                try:
                    house_activations.setdefault(int(np_house), []).append(
                        f"transiting {tp_key.capitalize()} hits natal {np_key.capitalize()} here"
                    )
                except (TypeError, ValueError):
                    pass

    for house_num, activators in house_activations.items():
        unique = list(dict.fromkeys(activators))
        theme = _HOUSE_THEMES.get(house_num, f"House {house_num}")
        if len(unique) >= 3:
            convergences.append(
                f"HOUSE CONVERGENCE — House {house_num} ({theme}) is activated by {len(unique)} "
                f"independent techniques simultaneously: {'; '.join(unique)}. "
                f"This house's life themes are the single defining arena right now."
            )
        elif len(unique) == 2:
            convergences.append(
                f"HOUSE EMPHASIS — House {house_num} ({theme}) is highlighted by 2 independent "
                f"timing layers: {' + '.join(unique)}. This life area merits focused attention."
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
        rulerships_section = "## House Rulerships & Cross-House Links\n" + _format_house_rulerships(chart)
        dignity_section = "## Dignity Hierarchy (Prediction Weighting)\n" + _format_dignity_hierarchy(chart)
        houses_section = "## House Cusps\n" + _format_houses(chart.get("houses") or {})
        aspects_section = "## Natal Aspects\n" + _format_aspects(chart.get("aspects") or [])
        patterns_section = "## Aspect Patterns\n" + _format_aspect_patterns(chart.get("aspect_patterns") or [])
        eclipse_section = "## Eclipse Sensitivity (±6 months, 3° orb)\n" + _format_eclipse_sensitivity(chart.get("eclipse_sensitivity") or [])
        retrograde_stations_section = "## Retrograde Stations (±180 days, 3° orb of natal)\n" + _format_retrograde_stations(chart.get("retrograde_stations") or [])
        transits_section = "## Current Transits (as of report date)\n" + _format_transits(chart.get("transits") or [])
        upcoming_section = "## Upcoming Transits (next 90 days — outer planets only)\n" + _format_upcoming_transits(chart.get("upcoming_transits") or [])
        transit_passes_section = "## Transit Passes — Full 12-Month Pattern (0.5° exact orb, outer planets)\n" + _format_transit_passes(chart.get("transit_passes") or [])
        primary_directions_section = "## Primary Directions (Naibod arc, 1° orb)\n" + _format_primary_directions(chart.get("primary_directions") or [])
        lunar_return_section = "## Lunar Return (next ~27-day cycle)\n" + _format_lunar_return(chart.get("lunar_return") or {})
        progressions_section = "## Secondary Progressions\n" + _format_progressions(chart.get("progressions"))
        prog_aspects_section = "## Progressed Aspects to Natal Chart\n" + _format_progressed_aspects(chart.get("progressed_aspects") or [])
        transit_to_progressed_section = "## Outer Planet Transits to Progressed Positions\n" + _format_transit_to_progressed(chart.get("transit_to_progressed") or [])
        solar_arcs_section = "## Solar Arc Directions\n" + _format_solar_arcs(chart.get("solar_arcs") or {})
        solar_arc_aspects_section = "## Solar Arc Aspects to Natal Chart\n" + _format_solar_arc_aspects(chart.get("solar_arc_aspects") or [])
        firdaria_section = "## Firdaria Time Lords\n" + _format_firdaria(chart.get("firdaria"), chart)
        solar_return_section = "## Solar Return Chart\n" + _format_solar_return(chart.get("solar_return") or {})
        vedic_section = "## Vedic (Jyotish) Overlay\n" + _format_vedic(chart.get("vedic"))
        almuten_section = "## Almuten Figuris (Chart Master by Classical Dignities)\n" + _format_almuten_figuris(chart.get("almuten_figuris"))
        dispositor_section = "## Dispositor Tree (Sign Rulership Chain)\n" + _format_dispositor_tree(chart.get("dispositor_tree"))
        parallels_section = "## Parallel & Contra-Parallel Aspects (declination, 1° orb)\n" + _format_parallel_aspects(chart.get("parallel_aspects") or [], chart.get("declinations") or {})
        syzygy_section = "## Prenatal Lunation (Syzygy Degree)\n" + _format_prenatal_syzygy(chart.get("prenatal_syzygy"))
        minor_aspects_section = "## Minor Aspects (semisquare 45°, sesquiquadrate 135°, quintile 72°, biquintile 144°, semisextile 30°, quincunx 150°)\n" + _format_minor_aspects(chart.get("minor_aspects") or [])
        parans_section = "## Natal Parans (angular simultaneity, 1.5° orb)\n" + _format_parans(chart.get("parans") or [])
        monthly_prof_line = _format_monthly_profection(chart.get("profection"))
        if monthly_prof_line:
            profection_section = "## Annual Profection\n" + _format_profection(chart.get("profection")) + "\n" + monthly_prof_line
        else:
            profection_section = "## Annual Profection\n" + _format_profection(chart.get("profection"))
        chart_section = "\n\n".join([
            placements, anaretic_section, fixed_stars_section, ruler_section, balance_section, sect_section,
            lunar_phase_section, pof_section, asteroids_section, arabic_section, antiscia_section,
            stelliums_section, receptions_section,
            nodes_section, rulerships_section, dignity_section, houses_section,
            aspects_section, patterns_section, eclipse_section, retrograde_stations_section,
            transits_section, upcoming_section, transit_passes_section,
            progressions_section, prog_aspects_section, transit_to_progressed_section,
            solar_arcs_section, solar_arc_aspects_section, primary_directions_section,
            profection_section, firdaria_section, solar_return_section, lunar_return_section, vedic_section,
            almuten_section, dispositor_section, parallels_section, syzygy_section,
            minor_aspects_section, parans_section,
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
- Dignity: domicile (strongest) > exaltation > neutral > detriment > fall (most challenged). Apply this asymmetrically in predictions: dignified planets deliver their significations reliably and constructively; debilitated planets deliver them with friction, delay, internal conflict, or through the lesson of struggling with that planet's themes. A Jupiter in detriment does NOT give easy abundance — it gives the understanding of abundance through scarcity. Never soften or omit the difficulty of a debilitated planet.
- Aspects: applying = currently intensifying; separating = past peak, more ingrained
- Aspect patterns (Grand Trine, T-Square, Yod, Grand Cross) are structural life themes — more important than individual aspects. Treat them as the chart's load-bearing architecture: individual aspects are furniture; patterns are the walls. A T-Square is a chronic pressure system that drives achievement through tension. A Grand Trine is a gift that can become complacency without challenge. A Yod is a fated redirection point — the apex planet must integrate two incompatible energies. Name the pattern's life dynamic before discussing individual planets within it.
- House rulership chain: for any life-area prediction, trace — (1) the relevant house, (2) its ruling planet from the Rulerships table, (3) that ruler's dignity and natal house, (4) any current activations of that ruler. This chain is the mechanism of prediction. Cross-house links (ruler of H-A sitting in H-B) mean those life areas are structurally entangled for this person — what happens in one echoes in the other.
- System boundary — Western vs. Vedic: Western tropical chart governs psychology, personality, and Western timing (transits, progressions, solar arc, profection, Firdaria). Vedic sidereal chart governs karmic biography and Vimshottari Dasha timing. Do NOT mix them within the same interpretation sentence. Correct: "Tropically, Venus in Libra shows aesthetic grace [Western]. Sidereal Venus in Virgo suggests a more exacting, service-oriented approach to relationships [Vedic overlay]." When the two systems agree on a theme, name the agreement as a confirmation. When they diverge, name both readings separately and let the person hold both.
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
- Primary directions (Naibod arc): the classical Ptolemaic timing method — 1° of ARMC advance per year of life (Naibod rate: 0.9856472°/year). Directed Ascendant or Midheaven aspecting a natal planet marks a biographical turning point: identity redefinition (directed ASC), career/authority shift (directed MC), or the natal planet's themes crystallizing externally. A directed planet reaching the natal ASC or MC brings that planet's energy into the foreground of life. Conjunction and opposition are strongest; squares also significant. Within 0.5° = the event is imminent or unfolding now; between 0.5°–1.0° = within about 6 months. Always prioritize directions to/from natal luminaries and angles. If a primary direction coincides with a current transit or solar arc, the biographical significance is doubled.
- Lunar return: monthly precision layer — the LR Ascendant filters the month's energy; any angular planets in the LR chart (within 5° of LR ASC or MC) dominate that month. LR Moon's house shows where emotional focus is concentrated. Use the lunar return to pinpoint WHEN within a year a transit or arc most concretely manifests — if a transit is active AND the LR Moon is in the same house as the transit's natal point, that month is the peak. Mention specific LR timing in Section 6 (Practical Guidance).
- Transit passes (multi-pass pattern): when an outer planet retrogrades while aspecting a natal point, the aspect recurs 2–3 times over several months. First direct pass = theme enters awareness; retrograde pass = deepest internal processing (often most intense); final direct pass = integration and externalization. Give all dates when multi-pass is present. Name each pass's quality in Section 6.
- Retrograde stations: a planet stationing (changing direction) within 3° of a natal point is not a brief transit — it will hold contact for weeks or months, making its activation far more potent than a standard transit pass. A direct station = the planet's themes are culminating and externalizing; a retrograde station = the themes are being internalized, reviewed, or reconsidered. An outer planet (especially Saturn or Pluto) stationing on a natal angle (ASC/MC) or luminary is a major biographical turning point. Name any station within 30 days (past or future) in Section 4.
- Transit-to-progressed: outer planets transiting progressed planetary positions represent a distinct third timing layer. The progressed chart reflects the evolved psychological self, so transits to progressed positions activate themes of the person's current chapter, not just their natal baseline. The progressed Moon is especially sensitive: outer planet aspects to the progressed Moon correlate with emotional turning points that complement but differ from the natal Moon transits. If an outer planet hits the same point in both the natal and progressed chart, the activation is doubled — name this explicitly.
- Progressed lunation cycle: the angle of the Progressed Moon ahead of the Progressed Sun reveals the psychological phase the person is living in. New Moon phase = a beginning, planting seeds with little visibility; Crescent = effort and resistance; First Quarter = crisis of action; Gibbous = refinement and preparation; Full Moon = culmination, revelation, visibility; Disseminating = sharing and teaching; Last Quarter = crisis of consciousness, questioning structures; Balsamic = release, completion, preparing for a new cycle. The "years to next Progressed New Moon" is a countdown to the next major psychological reset — if under 3 years, the current cycle is ending and new seeds are forming.
- Fixed stars: only exact conjunctions (1° orb) matter — no other aspects. The 4 Royal Stars (Aldebaran, Regulus, Antares, Fomalhaut) conjunct a luminary or angle are life-defining signatures; Algol conjunct any personal planet or the Ascendant is the chart's most intense pressure point and must be named. Spica, Sirius, Vega near the Sun/Moon/Ascendant indicate distinctive gifts. Weave fixed stars into interpretation naturally — do not list them mechanically.

- Minor aspects: the quintile (72°) and biquintile (144°) reveal creative gifts, talents, and inspired intelligence — they operate differently from the major aspects (which describe personality structures) and instead show where the person can access an almost effortless creative flow or extraordinary facility. A quintile or biquintile to the Sun, Moon, or chart ruler is one of the most reliable indicators of a distinctive gift; to Mercury, it shows unusual cognitive facility; to Venus, aesthetic genius; to Mars, athletic or technical brilliance. Semisquares (45°) and sesquiquadrates (135°) are chronic low-grade friction points — the people or situations described by those planets persistently irritate and push, but that pressure often produces results the person couldn't achieve through harmony alone. The quincunx (150°) demands constant adjustment — the two planets share neither element nor modality and must perpetually relearn how to cooperate; it correlates with health adjustments, career pivots, and relationship patterns requiring ongoing recalibration. The semisextile (30°) is a subtle background resource — use sparingly and only when the planets involved are significant elsewhere. Do not list minor aspects mechanically; integrate them where they add meaning to existing chart themes, especially quintiles/biquintiles to luminaries or angles.
- Parans (angular simultaneity): a paran forms when two planets simultaneously occupy two different angles (Rising, Setting, MC, IC) at the birth location — they were literally on the horizon and meridian together at the same moment. Unlike ecliptic conjunctions, parans operate regardless of sign or aspect; they bind planets in a permanent relationship at the experiential level of lived life, not the psychological level of aspect patterns. In traditional and Hellenistic practice, paran contacts are among the most powerful chart indicators: they show themes that manifest concretely and repeatedly in outer circumstances. Sun/Moon in paran with a malefic (Saturn, Mars) creates a persistent biographical theme of challenge in the domain of that malefic. Sun/Moon in paran with a benefic creates consistent good fortune in that domain. Parans between two outer planets (Saturn/Uranus/Neptune/Pluto) describe the generational themes the person embodies in their personal life. A paran between a light (Sun/Moon) and any outer planet is a life-defining signature — name it in Section 1 (Overview) if tight (under 0.5°), or in Section 5 (Key Themes) if wider. Do not force parans into every chart; mention only those within 1° orb involving luminaries, angles, or outer planets, and integrate naturally into the reading.

- Parallel and contra-parallel declinations: operate like hidden conjunctions and oppositions respectively, active across sign boundaries and often more exact than ecliptic aspects. A parallel (same declination, both north or both south within 1°) functions like a conjunction — the two planets blend and reinforce each other, even if they are in incompatible signs. A contra-parallel (equal but opposite declinations, within 1°) functions like an opposition — awareness, tension, and projection between the two planets. Parallels and contra-parallels involving the Sun, Moon, ASC ruler, or chart ruler are the most significant; they often explain chart dynamics that ecliptic aspects alone do not account for. Weave them naturally into interpretation where they add meaning: a Sun-Saturn contra-parallel operating alongside a Saturn square Sun in the ecliptic creates a double pressure that goes beyond what either aspect alone conveys. Do not list them mechanically — mention only those that reinforce or complicate existing chart themes. Note that parallels cut across sign boundaries: Venus parallel Jupiter means these two benefics cooperate even if they share no ecliptic aspect.
- Monthly profection: within the annual profection year, each calendar month from the last birthday activates the next house in sequence. The monthly profected house pinpoints which life arena comes into temporary focus for that 30-day period. The monthly profection lord (ruler of the monthly house) becomes a temporary co-ruler of the month alongside the annual lord. If the monthly lord is also currently transited, under a solar arc, or the same as the annual profection lord, that month becomes especially activated. Use the monthly profection in Section 6 (Practical Guidance) to give the most specific monthly advice: "In [month], House [N] is activated, making it the optimal time for [life area]..."
- Prenatal syzygy (prenatal lunation): the last New Moon or Full Moon before birth establishes the most sensitive degree in the entire natal chart. Planets or angles at this degree (within 3°) carry an intensity that does not show in the standard natal placements — this point is pre-charged before life begins. Any eclipse, transit, solar arc, or primary direction over the prenatal syzygy degree resonates chart-wide, not just in one life area. If a current transit or direction is within 3° of the prenatal syzygy degree, name it in the Current Climate section as a chart-wide amplifier. A natal planet within 1° of the prenatal syzygy degree is one of the most potent placements in the chart — that planet carries the full weight of the prenatal lunar phase and should be mentioned in the Personal Overview.

- Almuten Figuris (Chart Master): the planet accumulating the most essential dignity points at the five power positions (Sun, Moon, ASC, Part of Fortune, Part of Spirit). Unlike the chart ruler (derived from the ASC sign alone), the Almuten is determined by a comprehensive dignity calculation across multiple chart positions — it is the planet that most fundamentally governs the whole person's life direction. When the Almuten and the chart ruler are the same planet, that planet's themes are exceptionally dominant. When they differ, note that the Almuten Figuris operates as the "silent chart ruler" — its natal condition, house, and dignity set a background tone that modifies even the chart ruler's expression. If the Almuten is retrograde or in detriment/fall, the native's core vitality or life direction operates through friction and inner recalibration. Integrate the Almuten in the Personal Overview when its planet differs from the chart ruler, and in Life Direction when the Almuten shares a theme with the nodal axis.
- Dispositor tree: every planet's sign ruler traces back through a rulership chain to a final dispositor (a planet in its own sign). A chart with a single final dispositor concentrates the entire chart's authority in one planet — all other planets ultimately serve it; its natal condition (sign, house, dignity, aspects) sets the quality of the entire life narrative, even more than individual placements would suggest. When the final dispositor is also the chart ruler or Almuten Figuris, its centrality is tripled. A chart without a single final dispositor (multiple final dispositors or a mutual reception loop) indicates a more distributed power structure: no single planet lords over all others, and the native must consciously integrate competing centres of authority. Mutual reception cycles (two planets in each other's signs) represent a closed loop of cooperative power that operates somewhat independently of the rest of the chart — name them as an area of self-reinforcing talent or recurring dynamic. Integrate the dispositor tree in Section 1 (Overview) when a single final dispositor exists, and in Section 5 (Key Themes) when mutual reception cycles or distributed authority creates a notable pattern.

## Synthesis Protocol — Complete Mentally Before Writing
0. CHECK ASPECT PATTERNS FIRST. If a Grand Cross, T-Square, Grand Trine, Yod, Grand Sextile, or Mystic Rectangle is present, it is the STRUCTURAL SPINE of the reading. Every section must connect back to it. Do not bury it in Section 2 — it shapes every other interpretation.
1. READ THE CONVERGENCE INTELLIGENCE BLOCK FIRST. These pre-computed findings are the chart's loudest signals — build the reading around them.
2. READ THE DIGNITY HIERARCHY. Before making any prediction, check whether the planet involved is dignified or debilitated. A debilitated planet's period or transit brings the described events with friction, delay, and inner resistance — never describe it as straightforwardly positive. A dignified planet's activations are more reliable and constructive.
3. USE THE HOUSE RULERSHIP TABLE for every house-based prediction. The prediction chain: (a) identify the house for the life area, (b) find its ruler from the Rulerships table, (c) check the ruler's dignity and natal house, (d) check if the ruler is currently transited, directed, or under a Firdaria/Dasha period. A house-based prediction without tracing this chain is incomplete.
4. Check Primary Directions: any directed angle or planet within 1° of a natal point is a biographical turning point unfolding NOW. This is the highest-precision classical indicator — prioritize it in Section 4.
5. Check Eclipse Sensitivity: any eclipsed natal planet or angle is in an accelerated change period — weave this into sections 3 and 4.
6. Note the Progressed Lunation phase and years-to-next-New-Moon — this sets the psychological chapter and determines whether the person is in a building, culminating, or releasing season of life.
7. Check Transit Passes for multi-pass patterns: identify all 3 exact dates and note which pass is underway. Check the Lunar Return to pinpoint the peak month within the transit window.
8. Scan all remaining predictive layers and identify any 2–3 additional themes not already captured above.
9. Rank urgency: primary direction within 0.5° (now) → convergence-flagged planets → eclipsed points → applying transit/arc within 0.5° (days–weeks) → within 1° (months) → within 3° (season) → progressions (years).

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
        convergences = _compute_convergences(chart, state)
        convergence_block = ""
        if convergences:
            convergence_block = (
                "\n⚡ CONVERGENCE SIGNALS (highest priority — pre-computed cross-system agreements):\n"
                + "\n".join(f"▶ {c}" for c in convergences)
                + "\n"
            )

        prof = chart.get("profection") or {}
        monthly_prof_line = _format_monthly_profection(prof)
        profection_text = _format_profection(prof)
        if monthly_prof_line:
            profection_text += "\n" + monthly_prof_line

        placements = "\n".join([
            _format_planet("Sun", chart.get("sun")),
            _format_planet("Moon", chart.get("moon")),
            _format_planet("Mercury", chart.get("mercury")),
            _format_planet("Venus", chart.get("venus")),
            _format_planet("Mars", chart.get("mars")),
            _format_planet("Jupiter", chart.get("jupiter")),
            _format_planet("Saturn", chart.get("saturn")),
            _format_planet("Uranus", chart.get("uranus")),
            _format_planet("Neptune", chart.get("neptune")),
            _format_planet("Pluto", chart.get("pluto")),
            _format_planet("Chiron", chart.get("chiron")),
            f"- Ascendant: {chart['ascendant']['sign']} {chart['ascendant']['position']}°" if chart.get("ascendant") else "- Ascendant: unavailable",
            f"- Midheaven: {chart['midheaven']['sign']} {chart['midheaven']['position']}°" if chart.get("midheaven") else "- Midheaven: unavailable",
        ])

        chart_summary = (
            f"{convergence_block}"
            f"Natal Placements:\n{placements}"
            f"\n\nHouse Rulerships & Cross-House Links:\n{_format_house_rulerships(chart)}"
            f"\n\nDignity Hierarchy:\n{_format_dignity_hierarchy(chart)}"
            f"\n\nHouse Cusps:\n{_format_houses(chart.get('houses') or {})}"
            f"\n\nChart Ruler:\n{_format_chart_ruler(chart.get('chart_ruler'))}"
            f"\n\nPlanetary Sect:\n{_format_sect(chart.get('sect') or {})}"
            f"\n\nLunar Phase:\n{_format_lunar_phase(chart.get('lunar_phase') or {})}"
            f"\n\nNatal Aspects:\n{_format_aspects(chart.get('aspects') or [])}"
            f"\n\nMinor Aspects:\n{_format_minor_aspects(chart.get('minor_aspects') or [])}"
            f"\n\nAspect Patterns:\n{_format_aspect_patterns(chart.get('aspect_patterns') or [])}"
            f"\n\nMutual Receptions:\n{_format_mutual_receptions(chart.get('mutual_receptions') or [])}"
            f"\n\nParallel & Contra-Parallel Aspects:\n{_format_parallel_aspects(chart.get('parallel_aspects') or [], chart.get('declinations') or {})}"
            f"\n\nLunar Nodes:\n{_format_nodes(chart)}"
            f"\n\nFixed Star Conjunctions:\n{_format_fixed_stars(chart.get('fixed_stars') or [])}"
            f"\n\nAnaretic Degrees (29°):\n{_format_anaretic_degrees(chart.get('anaretic_degrees') or [])}"
            f"\n\nStelliums:\n{_format_stelliums(chart.get('stelliums') or [])}"
            f"\n\nPart of Fortune:\n{_format_part_of_fortune(chart.get('part_of_fortune'))}"
            f"\n\nAntiscia:\n{_format_antiscia(chart.get('antiscia') or [])}"
            f"\n\nCurrent Transits:\n{_format_transits(chart.get('transits') or [])}"
            f"\n\nUpcoming Transits (90 days):\n{_format_upcoming_transits(chart.get('upcoming_transits') or [])}"
            f"\n\nTransit Passes — Full 12-Month Pattern:\n{_format_transit_passes(chart.get('transit_passes') or [])}"
            f"\n\nEclipse Sensitivity:\n{_format_eclipse_sensitivity(chart.get('eclipse_sensitivity') or [])}"
            f"\n\nRetrograde Stations:\n{_format_retrograde_stations(chart.get('retrograde_stations') or [])}"
            f"\n\nSecondary Progressions:\n{_format_progressions(chart.get('progressions'))}"
            f"\n\nProgressed Aspects to Natal:\n{_format_progressed_aspects(chart.get('progressed_aspects') or [])}"
            f"\n\nOuter Planets Transiting Progressed Positions:\n{_format_transit_to_progressed(chart.get('transit_to_progressed') or [])}"
            f"\n\nSolar Arc Directions:\n{_format_solar_arcs(chart.get('solar_arcs') or {})}"
            f"\n\nSolar Arc Aspects to Natal:\n{_format_solar_arc_aspects(chart.get('solar_arc_aspects') or [])}"
            f"\n\nPrimary Directions (Naibod arc):\n{_format_primary_directions(chart.get('primary_directions') or [])}"
            f"\n\nAnnual + Monthly Profection:\n{profection_text}"
            f"\n\nFirdaria Time Lords:\n{_format_firdaria(chart.get('firdaria'), chart)}"
            f"\n\nSolar Return Chart:\n{_format_solar_return(chart.get('solar_return') or {})}"
            f"\n\nLunar Return (next ~27-day cycle):\n{_format_lunar_return(chart.get('lunar_return') or {})}"
            f"\n\nAlmuten Figuris:\n{_format_almuten_figuris(chart.get('almuten_figuris'))}"
            f"\n\nDispositor Tree:\n{_format_dispositor_tree(chart.get('dispositor_tree'))}"
            f"\n\nPrenatal Syzygy Degree:\n{_format_prenatal_syzygy(chart.get('prenatal_syzygy'))}"
            f"\n\nNatal Parans:\n{_format_parans(chart.get('parans') or [])}"
            f"\n\nVedic (Jyotish) Overlay:\n{_format_vedic(chart.get('vedic'))}"
        )
    else:
        chart_summary = "Natal chart data unavailable."

    system = (
        f"You are a master Western astrologer. You already provided a full reading for "
        f"{state['full_name']} (born {state['parsed_dob']} in {state['birth_location']}, "
        f"birth time {state['birth_time']} {state.get('birth_time_timezone', '')}, "
        f"current location {state.get('current_location', '')}).\n\n"
        f"COMPLETE CHART DATA (use this to answer every question with specificity):\n{chart_summary}\n\n"
        "Rules for follow-up answers:\n"
        "- ALWAYS cite specific planets, degrees, signs, houses, and dates from the chart data above\n"
        "- NEVER say chart data is unavailable — it is all provided above\n"
        "- NEVER say you cannot display visual content, show charts, or render images — you are not "
        "being asked to display anything; interpret the astrological data in text\n"
        "- NEVER say you are a text-based AI or reference any limitations around visuals\n"
        "- If the user asks about 'the chart' or 'what the chart shows', interpret the placements "
        "and aspects — answer as an astrologer reading a chart, not as a software system\n"
        "- Lead with the most time-sensitive data: applying transits, primary directions within 1°, "
        "solar arcs within 1°, and convergence signals\n"
        "- For timing questions, check transit passes for multi-pass patterns, primary directions, "
        "monthly profection, and lunar return for the peak month\n"
        "- For career/10th house questions: check MC sign, 10th house ruler, transits/arcs to MC, "
        "profection house, Firdaria lord, and solar return angles\n"
        "- When multiple techniques point to the same theme, name that convergence explicitly\n"
        "- Do NOT invent placements, aspects, or transits not listed above\n"
        "- Be direct, warm, and specific — 3–5 focused paragraphs maximum"
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
    """Blocking three-pass synastry report: draft → structural review → factual grounding."""
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
    draft = response.choices[0].message.content or ""
    reviewed = _review_synastry_report(draft, name_a, chart_a, name_b, chart_b, synastry)
    return _ground_synastry_report(reviewed, name_a, chart_a, name_b, chart_b, synastry)


def generate_synastry_report_stream(
    name_a: str, dob_a: str, loc_a: str, chart_a: dict,
    name_b: str, dob_b: str, loc_b: str, chart_b: dict,
    synastry: dict,
):
    """Three-pass synastry pipeline: draft → structural review → factual grounding → stream."""
    client = openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    prompt = build_synastry_prompt(name_a, dob_a, loc_a, chart_a, name_b, dob_b, loc_b, chart_b, synastry)

    # Pass 1: generate draft
    draft_resp = client.chat.completions.create(
        model="gpt-4o",
        max_tokens=3000,
        temperature=0.7,
        messages=[
            {"role": "system", "content": _SYNASTRY_SYSTEM},
            {"role": "user", "content": prompt},
        ],
    )
    draft = draft_resp.choices[0].message.content or ""

    # Pass 2: structural review (convergences, dignity, Saturn framing, overlays)
    reviewed = _review_synastry_report(draft, name_a, chart_a, name_b, chart_b, synastry)

    # Pass 3: factual grounding (placement, cross-aspects, composite, house numbers)
    final = _ground_synastry_report(reviewed, name_a, chart_a, name_b, chart_b, synastry)

    # Stream the final verified text line by line
    for line in final.split("\n"):
        yield line + "\n"


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
        "Do NOT invent aspects or placements not listed above. "
        "NEVER say you cannot display visual content or reference any AI limitations around visuals — "
        "interpret the astrological data in text as a skilled astrologer would."
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

_REVIEW_SYSTEM = (
    "You are a senior astrology editor. Your only job is to correct specific technical errors "
    "in a natal chart reading. Be conservative — fix only genuine errors, never rewrite for style. "
    "Preserve all headings, structure, section order, and approximate length."
)


def _build_review_prompt(draft: str, state: "AstrologerState") -> str:
    chart = state.get("chart_data") or {}
    dignity_ctx = _format_dignity_hierarchy(chart) if chart else "Not available."
    pattern_ctx = _format_aspect_patterns(chart.get("aspect_patterns") or []) if chart else "Not available."
    rulership_ctx = _format_house_rulerships(chart) if chart else "Not available."
    return f"""Review the natal chart reading below and fix ONLY these four specific errors if present:

1. **DIGNITY ERROR** — A debilitated planet's Firdaria period, Mahadasha, or major transit is described as straightforwardly positive/constructive without naming the friction, challenge, or required effort. (Use the Dignity Hierarchy below to identify debilitated planets.)

2. **SYSTEM MIXING** — A sentence blends Western tropical and Vedic sidereal interpretations in the same claim without clearly labeling which tradition is speaking (e.g., "your Venus in Scorpio [tropical] shows X while sidereal Venus in Libra shows Y" is correct; "Venus in Scorpio/Libra shows X" is not).

3. **PATTERN SPINE MISSING** — If a major aspect pattern (Grand Cross, T-Square, Yod, Grand Trine, Mystic Rectangle) exists in the chart, the reading must reference it as a structural theme in Section 1 or Section 2. If it appears only as a passing mention elsewhere, bring it forward.

4. **UNSUPPORTED HOUSE CLAIM** — A specific life-area prediction (career, relationships, finances, health) makes no mention of the relevant house ruler's natal condition (sign, dignity, or house placement).

## Reference: Dignity Hierarchy
{dignity_ctx}

## Reference: Aspect Patterns
{pattern_ctx}

## Reference: House Rulerships
{rulership_ctx}

## Reading to Review and Correct
{draft}

Output the COMPLETE corrected reading. Make only the minimum edits required to fix genuine errors. If no errors are found, reproduce the reading exactly."""


def _review_report(draft: str, state: "AstrologerState") -> str:
    """Self-review pass — returns corrected report text."""
    client = openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    response = client.chat.completions.create(
        model="gpt-4o",
        max_tokens=4096,
        temperature=0.3,
        messages=[
            {"role": "system", "content": _REVIEW_SYSTEM},
            {"role": "user", "content": _build_review_prompt(draft, state)},
        ],
    )
    return response.choices[0].message.content or draft


# ---------------------------------------------------------------------------
# Pass 3: Factual grounding
# ---------------------------------------------------------------------------

_GROUNDING_SYSTEM = (
    "You are a fact-checker for astrological chart readings. "
    "Your only job is to verify that specific factual claims in the reading match the "
    "ground-truth chart data provided. Be precise and conservative — only remove or correct "
    "claims that directly contradict the data. Never rewrite for style or completeness. "
    "Preserve all headings, structure, and interpretive content."
)


def _build_fact_sheet(chart: dict) -> str:
    """Compact ground-truth reference extracted from raw chart data."""
    lines: list[str] = ["## Ground-Truth Chart Facts"]

    # Natal placements
    lines.append("\n### Natal Placements")
    for p in ["sun", "moon", "mercury", "venus", "mars", "jupiter",
              "saturn", "uranus", "neptune", "pluto", "chiron"]:
        d = chart.get(p)
        if d:
            retro = " Rx" if d.get("retrograde") else ""
            house = f", H{d['house']}" if d.get("house") else ""
            dignity = f" [{d['dignity']}]" if d.get("dignity") else ""
            lines.append(f"- {p.capitalize()}: {d['sign']} {d['position']}°{retro}{house}{dignity}")
    asc = chart.get("ascendant")
    if asc:
        lines.append(f"- Ascendant: {asc['sign']} {asc['position']}°")
    mc = chart.get("midheaven")
    if mc:
        lines.append(f"- Midheaven: {mc['sign']} {mc['position']}°")

    # Timing lords
    lines.append("\n### Active Timing Lords")
    prof = chart.get("profection") or {}
    if prof:
        lines.append(
            f"- Annual Profection: House {prof.get('profected_house')}, "
            f"Lord of Year: {(prof.get('lord_of_year') or '?').capitalize()}"
        )
    fird = chart.get("firdaria") or {}
    if fird:
        lines.append(
            f"- Firdaria Major: {(fird.get('major_lord') or '?').capitalize()}, "
            f"ends {(fird.get('major_period_end') or '')[:10]}"
        )
        if fird.get("sub_lord"):
            lines.append(
                f"- Firdaria Sub: {fird['sub_lord'].capitalize()}, "
                f"ends {(fird.get('sub_period_end') or '')[:10]}"
            )
    vedic = chart.get("vedic") or {}
    dasha = (vedic.get("dasha") or {}) if vedic else {}
    if dasha:
        lines.append(
            f"- Mahadasha: {(dasha.get('mahadasha_lord') or '?').capitalize()}, "
            f"ends {(dasha.get('mahadasha_end') or '')[:10]}"
        )
        if dasha.get("antardasha_lord"):
            lines.append(
                f"- Antardasha: {dasha['antardasha_lord'].capitalize()}, "
                f"ends {(dasha.get('antardasha_end') or '')[:10]}"
            )

    # Transit passes — most specific timing source
    passes = chart.get("transit_passes") or []
    if passes:
        lines.append("\n### Transit Passes (exact dates, outer planets)")
        for p in passes[:20]:
            tp = p["transiting_planet"].capitalize()
            np_ = p["natal_planet"].replace("_", " ").title()
            for ps in (p.get("passes") or [])[:3]:
                retro = " Rx" if ps.get("retrograde") else ""
                lines.append(
                    f"- {tp}{retro} {p['aspect']} {np_}: {ps['date']} (orb {ps['orb']}°)"
                )

    # Upcoming transits (90-day window)
    upcoming = chart.get("upcoming_transits") or []
    if upcoming:
        lines.append("\n### Upcoming Transits (next 90 days)")
        for t in upcoming[:15]:
            tp = t["transiting_planet"].capitalize()
            np_ = t["natal_planet"].replace("_", " ").title()
            lines.append(
                f"- {tp} {t['aspect']} {np_}: ~{t.get('exact_date', 'unknown')} "
                f"(min orb {round(t.get('min_orb', 0), 2)}°)"
            )

    # Solar arc aspects
    sa = chart.get("solar_arc_aspects") or []
    if sa:
        lines.append("\n### Solar Arc Aspects (within 1°)")
        for a in sa:
            dp = a["directed_planet"].replace("arc_", "Arc ").replace("_", " ").title()
            np_ = a["natal_planet"].replace("_", " ").title()
            direction = "applying" if a.get("applying") else "separating"
            lines.append(f"- {dp} {a['aspect']} natal {np_}: orb {a['orb']}°, {direction}")

    # Progressed aspects
    prog = chart.get("progressed_aspects") or []
    if prog:
        lines.append("\n### Progressed Aspects (within 1°)")
        for a in prog[:10]:
            pp = a["progressed_planet"].replace("_", " ").title()
            np_ = a["natal_planet"].replace("_", " ").title()
            direction = "applying" if a.get("applying") else "separating"
            lines.append(f"- Progressed {pp} {a['aspect']} natal {np_}: orb {a['orb']}°, {direction}")

    # Primary directions
    pds = chart.get("primary_directions") or []
    if pds:
        lines.append("\n### Primary Directions (within 1°)")
        for d in pds[:8]:
            np_ = d["natal_point"].replace("_", " ").title()
            lines.append(f"- {d['directed_point']} {d['aspect']} natal {np_}: orb {d['orb']}°")

    # Aspect patterns
    patterns = chart.get("aspect_patterns") or []
    if patterns:
        lines.append("\n### Natal Aspect Patterns")
        for p in patterns:
            planets_str = ", ".join(pl.replace("_", " ").title() for pl in p["planets"])
            lines.append(f"- {p['type']}: {planets_str}")

    # Eclipse sensitivity
    eclipses = chart.get("eclipse_sensitivity") or []
    if eclipses:
        lines.append("\n### Eclipse Sensitivity")
        for e in eclipses[:8]:
            body = e["body"].replace("_", " ").title()
            lines.append(
                f"- {body} within {e['orb']}° of "
                f"{e.get('eclipse_type', 'eclipse').replace('_', ' ')} on {e['eclipse_date']}"
            )

    # Retrograde stations
    stations = chart.get("retrograde_stations") or []
    if stations:
        lines.append("\n### Retrograde Stations (within 3° of natal)")
        for s in stations[:8]:
            lines.append(
                f"- {s['planet'].capitalize()} stations {s.get('station_type', '?')} "
                f"on {s.get('date', '?')} at {s.get('sign', '?')} {s.get('position', '?')}°"
            )

    return "\n".join(lines)


def _build_grounding_prompt(report: str, state: "AstrologerState") -> str:
    chart = state.get("chart_data") or {}
    fact_sheet = _build_fact_sheet(chart) if chart else "No chart data available."
    return f"""Verify the natal chart reading below against the ground-truth chart data.

{fact_sheet}

## Reading to Verify
{report}

## Verification Instructions

Check ONLY these four types of factual errors:

1. **DATE MISMATCH** — The report names a specific month or date for a transit, solar arc, or primary direction event that does not appear in the Transit Passes, Upcoming Transits, Solar Arc Aspects, or Primary Directions data above. Correct the date using the actual data, or remove the unsupported sentence.

2. **PLACEMENT ERROR** — The report states a planet is in a sign or house that contradicts the Natal Placements data above.

3. **TIMING LORD ERROR** — The report names a Firdaria major/sub lord, Mahadasha/Antardasha lord, or Profection lord of the year that contradicts the Active Timing Lords data above.

4. **INVENTED ASPECT** — The report describes an applying or exact aspect (e.g., "Saturn is squaring your natal Moon") that does not appear in the Transit Passes, Solar Arc Aspects, or Progressed Aspects data above.

Make only the minimum edits required to fix genuine errors. Do not rewrite for style, completeness, or interpretation. If no factual errors are found, reproduce the reading exactly."""


def _ground_report(report: str, state: "AstrologerState") -> str:
    """Factual grounding pass — cross-references report claims against raw chart data."""
    chart = state.get("chart_data") or {}
    if not chart:
        return report  # nothing to ground against
    client = openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    response = client.chat.completions.create(
        model="gpt-4o",
        max_tokens=4096,
        temperature=0,
        messages=[
            {"role": "system", "content": _GROUNDING_SYSTEM},
            {"role": "user", "content": _build_grounding_prompt(report, state)},
        ],
    )
    return response.choices[0].message.content or report


def generate_report(state: "AstrologerState") -> str:
    """Blocking three-pass report: draft → structural review → factual grounding."""
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
    draft = response.choices[0].message.content or ""
    reviewed = _review_report(draft, state)
    return _ground_report(reviewed, state)


def generate_report_stream(state: "AstrologerState"):
    """Three-pass pipeline: draft → structural review → factual grounding → stream."""
    client = openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"])

    # Pass 1: generate draft
    draft_resp = client.chat.completions.create(
        model="gpt-4o",
        max_tokens=4096,
        temperature=0.7,
        messages=[
            {"role": "system", "content": _REPORT_SYSTEM},
            {"role": "user", "content": build_prompt(state)},
        ],
    )
    draft = draft_resp.choices[0].message.content or ""

    # Pass 2: structural self-review
    reviewed = _review_report(draft, state)

    # Pass 3: factual grounding against raw chart data
    final = _ground_report(reviewed, state)

    # Stream the final verified text line by line
    for line in final.split("\n"):
        yield line + "\n"


# ===========================================================================
# Synastry three-pass pipeline helpers
# ===========================================================================

_SYNASTRY_REVIEW_SYSTEM = (
    "You are a senior relationship astrology editor. Your only job is to correct specific technical "
    "errors in a synastry reading. Be conservative — fix only genuine errors, never rewrite for style. "
    "Preserve all headings, structure, section order, and approximate length."
)


def _build_synastry_review_prompt(
    draft: str,
    name_a: str, chart_a: dict,
    name_b: str, chart_b: dict,
    synastry: dict,
) -> str:
    convergences = _compute_synastry_convergences(name_a, chart_a, name_b, chart_b, synastry)
    convergence_list = "\n".join(f"- {c}" for c in convergences) if convergences else "None detected."

    composite = synastry.get("composite") or {}
    dignity_lines = []
    for key in ["sun", "moon", "venus", "mars", "saturn", "mercury", "jupiter"]:
        d = composite.get(key)
        if d and d.get("dignity") in ("detriment", "fall"):
            dignity_lines.append(
                f"- Composite {key.capitalize()}: {d['sign']} [{d['dignity']}]"
            )
    composite_dignity = "\n".join(dignity_lines) if dignity_lines else "None."

    saturn_contacts = []
    for a in (synastry.get("cross_aspects") or []):
        if "saturn" in (a.get("planet_a", "") + a.get("planet_b", "")):
            if a.get("aspect") in ("conjunction", "square", "opposition"):
                pa = a["planet_a"].replace("_", " ").title()
                pb = a["planet_b"].replace("_", " ").title()
                saturn_contacts.append(
                    f"- {name_a}'s {pa} {a['aspect']} {name_b}'s {pb} (orb {a['orb']}°)"
                )
    saturn_list = "\n".join(saturn_contacts) if saturn_contacts else "None."

    return f"""Review the synastry reading below and fix ONLY these four specific errors if present:

1. **CONVERGENCE NOT ADDRESSED** — One of the pre-computed synastry convergences below was not explicitly addressed in the reading. Integrate a clear interpretation of any unaddressed convergence into the most relevant section.

2. **COMPOSITE DIGNITY ERROR** — A composite planet in detriment or fall is described as constructive or positive without naming the challenge it creates for the relationship. (See Composite Debilitated Planets below.)

3. **SATURN FRAMING ERROR** — A challenging Saturn cross-aspect (conjunction, square, or opposition) is described as purely positive or entirely omitted. Saturn contacts must be named honestly — acknowledge both the stabilizing AND the restricting/challenging dimension.

4. **HOUSE OVERLAY UNSUPPORTED CLAIM** — A statement about what this relationship brings to a specific area of one person's life (career, home, finances, spirituality, etc.) makes no reference to the house overlay data. Either cite the relevant overlay or remove the unsupported life-area claim.

## Reference: Pre-Computed Convergences (all must be addressed)
{convergence_list}

## Reference: Composite Debilitated Planets
{composite_dignity}

## Reference: Challenging Saturn Cross-Aspects
{saturn_list}

## Reading to Review and Correct
{draft}

Output the COMPLETE corrected reading. Make only the minimum edits required to fix genuine errors. If no errors are found, reproduce the reading exactly."""


def _review_synastry_report(
    draft: str,
    name_a: str, chart_a: dict,
    name_b: str, chart_b: dict,
    synastry: dict,
) -> str:
    client = openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    response = client.chat.completions.create(
        model="gpt-4o",
        max_tokens=3500,
        temperature=0.3,
        messages=[
            {"role": "system", "content": _SYNASTRY_REVIEW_SYSTEM},
            {"role": "user", "content": _build_synastry_review_prompt(
                draft, name_a, chart_a, name_b, chart_b, synastry
            )},
        ],
    )
    return response.choices[0].message.content or draft


def _build_synastry_fact_sheet(
    name_a: str, chart_a: dict,
    name_b: str, chart_b: dict,
    synastry: dict,
) -> str:
    """Compact ground-truth reference for synastry factual grounding."""
    lines: list[str] = ["## Ground-Truth Synastry Facts"]

    key = ["sun", "moon", "ascendant", "venus", "mars", "mercury", "jupiter", "saturn"]
    lines.append(f"\n### {name_a}'s Key Placements")
    for p in key:
        d = chart_a.get(p)
        if d:
            retro = " Rx" if d.get("retrograde") else ""
            house = f", H{d['house']}" if d.get("house") else ""
            lines.append(f"- {p.capitalize()}: {d['sign']} {d.get('position', '?')}°{retro}{house}")

    lines.append(f"\n### {name_b}'s Key Placements")
    for p in key:
        d = chart_b.get(p)
        if d:
            retro = " Rx" if d.get("retrograde") else ""
            house = f", H{d['house']}" if d.get("house") else ""
            lines.append(f"- {p.capitalize()}: {d['sign']} {d.get('position', '?')}°{retro}{house}")

    cross = synastry.get("cross_aspects") or []
    if cross:
        lines.append("\n### Inter-Chart Aspects")
        for a in cross[:25]:
            pa = a["planet_a"].replace("_", " ").title()
            pb = a["planet_b"].replace("_", " ").title()
            lines.append(f"- {name_a}'s {pa} {a['aspect']} {name_b}'s {pb} (orb {a['orb']}°)")

    overlays_ba = synastry.get("house_overlays_b_in_a") or []
    if overlays_ba:
        lines.append(f"\n### {name_b}'s Planets in {name_a}'s Houses")
        for o in overlays_ba[:10]:
            lines.append(
                f"- {name_b}'s {o['planet'].capitalize()} ({o['sign']}) in {name_a}'s House {o['house_in_partner']}"
            )

    overlays_ab = synastry.get("house_overlays_a_in_b") or []
    if overlays_ab:
        lines.append(f"\n### {name_a}'s Planets in {name_b}'s Houses")
        for o in overlays_ab[:10]:
            lines.append(
                f"- {name_a}'s {o['planet'].capitalize()} ({o['sign']}) in {name_b}'s House {o['house_in_partner']}"
            )

    composite = synastry.get("composite") or {}
    if composite:
        lines.append("\n### Composite Chart Placements")
        for p in ["sun", "moon", "ascendant", "midheaven", "venus", "mars", "saturn"]:
            d = composite.get(p)
            if d:
                house = f", H{d['house']}" if d.get("house") else ""
                lines.append(f"- Composite {p.capitalize()}: {d['sign']} {d.get('position', '?')}°{house}")

    return "\n".join(lines)


def _build_synastry_grounding_prompt(
    report: str,
    name_a: str, chart_a: dict,
    name_b: str, chart_b: dict,
    synastry: dict,
) -> str:
    fact_sheet = _build_synastry_fact_sheet(name_a, chart_a, name_b, chart_b, synastry)
    return f"""Verify the synastry reading below against the ground-truth chart data.

{fact_sheet}

## Reading to Verify
{report}

## Verification Instructions

Check ONLY these four types of factual errors:

1. **PLACEMENT ERROR** — The report states a planet is in a sign or house for either person that contradicts the Key Placements data above.

2. **INVENTED CROSS-ASPECT** — The report describes an inter-chart aspect (e.g., "{name_a}'s Venus trines {name_b}'s Moon") that does not appear in the Inter-Chart Aspects data above.

3. **COMPOSITE ERROR** — The report states a composite planet is in a sign or house that contradicts the Composite Chart Placements data above.

4. **HOUSE NUMBER ERROR** — The report names a specific house number for a planet overlay (e.g., "{name_b}'s Sun falls in {name_a}'s 7th house") that contradicts the House Overlays data above.

Make only the minimum edits required to fix genuine errors. Do not rewrite for style, completeness, or interpretation. If no factual errors are found, reproduce the reading exactly."""


def _ground_synastry_report(
    report: str,
    name_a: str, chart_a: dict,
    name_b: str, chart_b: dict,
    synastry: dict,
) -> str:
    """Factual grounding pass for synastry — skipped if chart data is absent."""
    if not synastry:
        return report
    client = openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    response = client.chat.completions.create(
        model="gpt-4o",
        max_tokens=3500,
        temperature=0,
        messages=[
            {"role": "system", "content": _GROUNDING_SYSTEM},
            {"role": "user", "content": _build_synastry_grounding_prompt(
                report, name_a, chart_a, name_b, chart_b, synastry
            )},
        ],
    )
    return response.choices[0].message.content or report
