from __future__ import annotations
from typing import Optional
from kerykeion import AstrologicalSubject


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

    chart = {
        "sun": _safe_planet(subject, "sun"),
        "moon": _safe_planet(subject, "moon"),
        "mercury": _safe_planet(subject, "mercury"),
        "venus": _safe_planet(subject, "venus"),
        "mars": _safe_planet(subject, "mars"),
        "jupiter": _safe_planet(subject, "jupiter"),
        "saturn": _safe_planet(subject, "saturn"),
        "uranus": _safe_planet(subject, "uranus"),
        "neptune": _safe_planet(subject, "neptune"),
        "pluto": _safe_planet(subject, "pluto"),
    }

    # Ascendant and Midheaven via house cusps
    first = getattr(subject, "first_house", None)
    tenth = getattr(subject, "tenth_house", None)

    chart["ascendant"] = {
        "sign": getattr(first, "sign", None),
        "position": round(getattr(first, "position", 0.0), 2),
    } if first else None

    chart["midheaven"] = {
        "sign": getattr(tenth, "sign", None),
        "position": round(getattr(tenth, "position", 0.0), 2),
    } if tenth else None

    return chart
