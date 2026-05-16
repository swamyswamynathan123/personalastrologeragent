from __future__ import annotations
from typing import Optional
from kerykeion import AstrologicalSubject

_PLANETS = ["sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn", "uranus", "neptune", "pluto"]

# (aspect name, exact angle, max orb)
_MAJOR_ASPECTS = [
    ("Conjunction", 0, 8),
    ("Sextile", 60, 6),
    ("Square", 90, 8),
    ("Trine", 120, 8),
    ("Opposition", 180, 8),
]

# Transits use a tighter orb so only active aspects are shown
_TRANSIT_ORB = 3.0


def _safe_planet(subject: AstrologicalSubject, attr: str) -> Optional[dict]:
    planet = getattr(subject, attr, None)
    if planet is None:
        return None
    return {
        "sign": getattr(planet, "sign", None),
        "position": round(getattr(planet, "position", 0.0), 2),
        "abs_pos": round(getattr(planet, "abs_pos", 0.0), 2),
        "house": getattr(planet, "house", None),
        "retrograde": getattr(planet, "retrograde", False),
    }


def _angular_diff(pos1: float, pos2: float) -> float:
    diff = abs(pos1 - pos2) % 360
    return min(diff, 360 - diff)


def _find_aspect(pos1: float, pos2: float, max_orb: float = 8.0) -> Optional[tuple[str, float]]:
    diff = _angular_diff(pos1, pos2)
    for name, angle, orb in _MAJOR_ASPECTS:
        actual_orb = abs(diff - angle)
        if actual_orb <= min(orb, max_orb):
            return name, round(actual_orb, 2)
    return None


def compute_aspects(chart: dict) -> list[dict]:
    """Compute natal aspects between all planet pairs (including Ascendant and Midheaven)."""
    bodies: dict[str, float] = {}
    for planet in _PLANETS:
        data = chart.get(planet)
        if data and data.get("abs_pos") is not None:
            bodies[planet] = data["abs_pos"]
    for angle_point in ("ascendant", "midheaven"):
        data = chart.get(angle_point)
        if data and data.get("abs_pos") is not None:
            bodies[angle_point] = data["abs_pos"]

    aspects = []
    body_list = list(bodies.items())
    for i, (p1, pos1) in enumerate(body_list):
        for p2, pos2 in body_list[i + 1:]:
            result = _find_aspect(pos1, pos2)
            if result:
                aspect_name, orb = result
                aspects.append({"planet1": p1, "planet2": p2, "aspect": aspect_name, "orb": orb})
    return aspects


def compute_transits(
    natal_chart: dict,
    year: int,
    month: int,
    day: int,
    hour: int,
    minute: int,
    city: str,
    nation: str,
    tz_str: str,
) -> list[dict]:
    """Compute aspects between today's transiting planets and the natal chart."""
    subject = AstrologicalSubject(
        name="Transit",
        year=year,
        month=month,
        day=day,
        hour=hour,
        minute=minute,
        city=city,
        nation=nation,
        tz_str=tz_str,
        online=True,
    )

    transit_positions: dict[str, float] = {}
    for planet in _PLANETS:
        data = _safe_planet(subject, planet)
        if data and data.get("abs_pos") is not None:
            transit_positions[planet] = data["abs_pos"]

    transits = []
    for t_planet, t_pos in transit_positions.items():
        for n_planet in _PLANETS:
            n_data = natal_chart.get(n_planet)
            if not n_data or n_data.get("abs_pos") is None:
                continue
            result = _find_aspect(t_pos, n_data["abs_pos"], max_orb=_TRANSIT_ORB)
            if result:
                aspect_name, orb = result
                transits.append({
                    "transiting_planet": t_planet,
                    "natal_planet": n_planet,
                    "aspect": aspect_name,
                    "orb": orb,
                })
    return transits


def compute_chart(
    full_name: str,
    birth_year: int,
    birth_month: int,
    birth_day: int,
    birth_hour: int,
    birth_minute: int,
    city: str,
    nation: str,
    tz_str: str,
) -> dict:
    """Return a plain dict of natal chart placements using kerykeion."""
    subject = AstrologicalSubject(
        name=full_name,
        year=birth_year,
        month=birth_month,
        day=birth_day,
        hour=birth_hour,
        minute=birth_minute,
        city=city,
        nation=nation,
        tz_str=tz_str,
        online=True,
    )

    chart = {planet: _safe_planet(subject, planet) for planet in _PLANETS}

    # Ascendant and Midheaven — include abs_pos so they can be used in aspects
    first = getattr(subject, "first_house", None)
    tenth = getattr(subject, "tenth_house", None)

    chart["ascendant"] = {
        "sign": getattr(first, "sign", None),
        "position": round(getattr(first, "position", 0.0), 2),
        "abs_pos": round(getattr(first, "abs_pos", 0.0), 2),
    } if first else None

    chart["midheaven"] = {
        "sign": getattr(tenth, "sign", None),
        "position": round(getattr(tenth, "position", 0.0), 2),
        "abs_pos": round(getattr(tenth, "abs_pos", 0.0), 2),
    } if tenth else None

    return chart
