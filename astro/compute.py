from __future__ import annotations
from typing import Optional
from kerykeion import AstrologicalSubject

_PLANETS = ["sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn", "uranus", "neptune", "pluto"]

_MAJOR_ASPECTS = [
    ("Conjunction", 0, 8),
    ("Sextile", 60, 6),
    ("Square", 90, 8),
    ("Trine", 120, 8),
    ("Opposition", 180, 8),
]

_TRANSIT_ORB = 3.0

# Average daily motion in degrees (direct). Retrograde flag flips the sign.
_PLANET_SPEEDS = {
    "moon": 13.2, "mercury": 1.38, "venus": 1.2, "sun": 0.985,
    "mars": 0.524, "jupiter": 0.083, "saturn": 0.034,
    "uranus": 0.012, "neptune": 0.006, "pluto": 0.004,
    "north_node": 0.053,  # mean node moves mostly retrograde; retrograde flag handles direction
    "ascendant": 0.0, "midheaven": 0.0,
}

_SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]

_HOUSE_ATTRS = [
    "first_house", "second_house", "third_house", "fourth_house",
    "fifth_house", "sixth_house", "seventh_house", "eighth_house",
    "ninth_house", "tenth_house", "eleventh_house", "twelfth_house",
]


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


def _safe_house(subject: AstrologicalSubject, attr: str) -> Optional[dict]:
    house = getattr(subject, attr, None)
    if house is None:
        return None
    return {
        "sign": getattr(house, "sign", None),
        "position": round(getattr(house, "position", 0.0), 2),
    }


def _sign_from_abs_pos(abs_pos: float) -> tuple[str, float]:
    idx = int(abs_pos / 30) % 12
    return _SIGNS[idx], round(abs_pos % 30, 2)


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


def _is_applying(
    p1_name: str, p1_abs: float, p1_retro: bool,
    p2_name: str, p2_abs: float, p2_retro: bool,
    aspect_angle: float,
) -> bool:
    """True if the two bodies are moving toward the exact aspect angle."""
    s1 = _PLANET_SPEEDS.get(p1_name, 0) * (-1 if p1_retro else 1)
    s2 = _PLANET_SPEEDS.get(p2_name, 0) * (-1 if p2_retro else 1)
    rel = s1 - s2  # net motion of p1 relative to p2 per day

    # Signed gap: how far ahead p1 is of p2, in [-180, 180]
    gap = (p1_abs - p2_abs) % 360
    if gap > 180:
        gap -= 360

    # Nearest exact aspect position
    if aspect_angle == 0:
        exact = 0.0
    elif aspect_angle == 180:
        exact = 180.0 if gap >= 0 else -180.0
    else:
        exact = aspect_angle if abs(gap - aspect_angle) <= abs(gap + aspect_angle) else -aspect_angle

    deviation = gap - exact  # how far the current gap is from exact
    if rel == 0 or deviation == 0:
        return False
    # Applying when deviation and rel have opposite signs (gap moving toward exact)
    return (deviation > 0) != (rel > 0)


def compute_aspects(chart: dict) -> list[dict]:
    """Compute natal aspects between all planet pairs, Ascendant, Midheaven, and North Node."""
    bodies: dict[str, tuple[float, bool]] = {}
    for planet in _PLANETS:
        data = chart.get(planet)
        if data and data.get("abs_pos") is not None:
            bodies[planet] = (data["abs_pos"], data.get("retrograde", False))
    for key in ("ascendant", "midheaven"):
        data = chart.get(key)
        if data and data.get("abs_pos") is not None:
            bodies[key] = (data["abs_pos"], False)
    nn = chart.get("north_node")
    if nn and nn.get("abs_pos") is not None:
        bodies["north_node"] = (nn["abs_pos"], nn.get("retrograde", False))

    aspects = []
    body_list = list(bodies.items())
    for i, (p1, (pos1, retro1)) in enumerate(body_list):
        for p2, (pos2, retro2) in body_list[i + 1:]:
            result = _find_aspect(pos1, pos2)
            if result:
                aspect_name, orb = result
                exact_angle = next(a for n, a, _ in _MAJOR_ASPECTS if n == aspect_name)
                applying = _is_applying(p1, pos1, retro1, p2, pos2, retro2, exact_angle)
                aspects.append({
                    "planet1": p1, "planet2": p2,
                    "aspect": aspect_name, "orb": orb, "applying": applying,
                })
    return aspects


def compute_transits(
    natal_chart: dict,
    year: int, month: int, day: int, hour: int, minute: int,
    city: str, nation: str, tz_str: str,
) -> list[dict]:
    """Compute aspects between today's transiting planets and the natal chart."""
    subject = AstrologicalSubject(
        name="Transit",
        year=year, month=month, day=day, hour=hour, minute=minute,
        city=city, nation=nation, tz_str=tz_str, online=True,
    )

    transit_positions: dict[str, tuple[float, bool]] = {}
    for planet in _PLANETS:
        data = _safe_planet(subject, planet)
        if data and data.get("abs_pos") is not None:
            transit_positions[planet] = (data["abs_pos"], data.get("retrograde", False))

    transits = []
    for t_planet, (t_pos, t_retro) in transit_positions.items():
        for n_planet in _PLANETS:
            n_data = natal_chart.get(n_planet)
            if not n_data or n_data.get("abs_pos") is None:
                continue
            result = _find_aspect(t_pos, n_data["abs_pos"], max_orb=_TRANSIT_ORB)
            if result:
                aspect_name, orb = result
                exact_angle = next(a for n, a, _ in _MAJOR_ASPECTS if n == aspect_name)
                applying = _is_applying(
                    t_planet, t_pos, t_retro,
                    n_planet, n_data["abs_pos"], n_data.get("retrograde", False),
                    exact_angle,
                )
                transits.append({
                    "transiting_planet": t_planet, "natal_planet": n_planet,
                    "aspect": aspect_name, "orb": orb, "applying": applying,
                })
    return transits


def compute_chart(
    full_name: str,
    birth_year: int, birth_month: int, birth_day: int,
    birth_hour: int, birth_minute: int,
    city: str, nation: str, tz_str: str,
) -> dict:
    """Return a plain dict of natal chart placements using kerykeion."""
    subject = AstrologicalSubject(
        name=full_name,
        year=birth_year, month=birth_month, day=birth_day,
        hour=birth_hour, minute=birth_minute,
        city=city, nation=nation, tz_str=tz_str, online=True,
    )

    chart = {planet: _safe_planet(subject, planet) for planet in _PLANETS}

    # Ascendant and Midheaven (include abs_pos for aspect computation)
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

    # North Node (mean node) and computed South Node
    north_node = _safe_planet(subject, "mean_node")
    chart["north_node"] = north_node
    if north_node and north_node.get("abs_pos") is not None:
        s_abs = (north_node["abs_pos"] + 180) % 360
        s_sign, s_pos = _sign_from_abs_pos(s_abs)
        chart["south_node"] = {"sign": s_sign, "position": s_pos, "abs_pos": round(s_abs, 2)}
    else:
        chart["south_node"] = None

    # All 12 house cusps
    chart["houses"] = {}
    for i, attr in enumerate(_HOUSE_ATTRS, 1):
        chart["houses"][str(i)] = _safe_house(subject, attr)

    return chart
