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

_PLANET_SPEEDS = {
    "moon": 13.2, "mercury": 1.38, "venus": 1.2, "sun": 0.985,
    "mars": 0.524, "jupiter": 0.083, "saturn": 0.034,
    "uranus": 0.012, "neptune": 0.006, "pluto": 0.004,
    "chiron": 0.02, "north_node": 0.053,
    "ascendant": 0.0, "midheaven": 0.0,
}

_PROGRESSED_ORB = 1.0  # 1° = ~1 year for the progressed Sun

_SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]

_HOUSE_ATTRS = [
    "first_house", "second_house", "third_house", "fourth_house",
    "fifth_house", "sixth_house", "seventh_house", "eighth_house",
    "ninth_house", "tenth_house", "eleventh_house", "twelfth_house",
]

# Essential dignities: domicile checked first (strongest), then exaltation, detriment, fall.
# Outer planets use modern rulerships for domicile/detriment; exaltation/fall omitted where debated.
_DIGNITIES: dict[str, dict[str, list[str]]] = {
    "sun":     {"domicile": ["Leo"],                    "exaltation": ["Aries"],     "detriment": ["Aquarius"],             "fall": ["Libra"]},
    "moon":    {"domicile": ["Cancer"],                 "exaltation": ["Taurus"],    "detriment": ["Capricorn"],            "fall": ["Scorpio"]},
    "mercury": {"domicile": ["Gemini", "Virgo"],        "exaltation": [],            "detriment": ["Sagittarius", "Pisces"],"fall": []},
    "venus":   {"domicile": ["Taurus", "Libra"],        "exaltation": ["Pisces"],    "detriment": ["Aries", "Scorpio"],     "fall": ["Virgo"]},
    "mars":    {"domicile": ["Aries", "Scorpio"],       "exaltation": ["Capricorn"], "detriment": ["Libra", "Taurus"],      "fall": ["Cancer"]},
    "jupiter": {"domicile": ["Sagittarius", "Pisces"],  "exaltation": ["Cancer"],    "detriment": ["Gemini", "Virgo"],      "fall": ["Capricorn"]},
    "saturn":  {"domicile": ["Capricorn", "Aquarius"],  "exaltation": ["Libra"],     "detriment": ["Cancer", "Leo"],        "fall": ["Aries"]},
    "uranus":  {"domicile": ["Aquarius"],               "exaltation": [],            "detriment": ["Leo"],                  "fall": []},
    "neptune": {"domicile": ["Pisces"],                 "exaltation": [],            "detriment": ["Virgo"],                "fall": []},
    "pluto":   {"domicile": ["Scorpio"],                "exaltation": [],            "detriment": ["Taurus"],               "fall": []},
}

# Modern sign rulers (used for chart ruler and house ruler lookups)
_SIGN_RULER: dict[str, str] = {
    "Aries": "mars", "Taurus": "venus", "Gemini": "mercury", "Cancer": "moon",
    "Leo": "sun", "Virgo": "mercury", "Libra": "venus", "Scorpio": "pluto",
    "Sagittarius": "jupiter", "Capricorn": "saturn", "Aquarius": "uranus", "Pisces": "neptune",
}

_SIGN_ELEMENT: dict[str, str] = {
    "Aries": "Fire", "Leo": "Fire", "Sagittarius": "Fire",
    "Taurus": "Earth", "Virgo": "Earth", "Capricorn": "Earth",
    "Gemini": "Air", "Libra": "Air", "Aquarius": "Air",
    "Cancer": "Water", "Scorpio": "Water", "Pisces": "Water",
}

_SIGN_MODALITY: dict[str, str] = {
    "Aries": "Cardinal", "Cancer": "Cardinal", "Libra": "Cardinal", "Capricorn": "Cardinal",
    "Taurus": "Fixed", "Leo": "Fixed", "Scorpio": "Fixed", "Aquarius": "Fixed",
    "Gemini": "Mutable", "Virgo": "Mutable", "Sagittarius": "Mutable", "Pisces": "Mutable",
}

# Maps kerykeion house-name strings to integers (handles both string and int house values)
_HOUSE_NUMBER: dict[str, int] = {
    "First_House": 1, "Second_House": 2, "Third_House": 3, "Fourth_House": 4,
    "Fifth_House": 5, "Sixth_House": 6, "Seventh_House": 7, "Eighth_House": 8,
    "Ninth_House": 9, "Tenth_House": 10, "Eleventh_House": 11, "Twelfth_House": 12,
}

# Sect: classical day/night planet groupings
_SECT_DIURNAL = {"sun", "jupiter", "saturn"}     # day sect planets
_SECT_NOCTURNAL = {"moon", "venus", "mars"}       # night sect planets
_SECT_MALEFICS = {"saturn", "mars"}
_SECT_BENEFICS = {"jupiter", "venus"}

# Fixed stars: (name, J2000 tropical longitude°, nature, interpretation)
# Orb: 1.0° conjunction to any natal body or angle
_FIXED_STARS: list[tuple[str, float, str, str]] = [
    ("Algol",       56.17, "malefic",
     "the most feared star; Medusa's eye — compulsive, dangerous power; themes of violence, obsession, or loss that must be consciously transformed"),
    ("Alcyone",     60.00, "mixed",
     "Pleiades — grief and weeping, but also far-sighted ambition and connection to collective memory and vision"),
    ("Aldebaran",   69.78, "benefic",
     "Royal Star (Watcher of the East) — honor, success, intelligence; greatness sustained only through integrity"),
    ("Rigel",       76.83, "benefic",
     "rise through persistent effort and technical mastery; practical ambition that earns its rewards"),
    ("Betelgeuse",  88.75, "benefic",
     "great success, bold achievement, expansive fortune; a star of rapid rise and commanding presence"),
    ("Sirius",     104.08, "benefic",
     "the brightest star — fierce ambition, fame, renown; burns intensely and can illuminate or consume"),
    ("Pollux",     113.22, "mixed",
     "bold warrior energy — audacious and courageous; victory is possible but ruthlessness must be guarded against"),
    ("Regulus",    149.83, "benefic",
     "Royal Star (Heart of the Lion) — leadership, fame, royalty; success is assured unless revenge is sought, which destroys all gains"),
    ("Spica",      203.83, "benefic",
     "one of the most fortunate stars — artistic gifts, brilliance, grace, and natural abundance"),
    ("Arcturus",   204.23, "benefic",
     "success through independent, pioneering effort; a trailblazer who forges their own path"),
    ("Antares",    249.77, "mixed",
     "Royal Star (Heart of the Scorpion) — fierce ambition, passion, warrior drive; success comes but reckless overreach destroys it"),
    ("Vega",       285.32, "benefic",
     "artistic gifts, idealism, charisma, and visionary leadership; magnetic aesthetic presence"),
    ("Fomalhaut",  333.87, "benefic",
     "Royal Star (Watcher of the South) — otherworldly idealism, spirituality, poetic gifts; highly sensitive and visionary"),
    ("Scheat",     359.37, "malefic",
     "risk of undoing through stubbornness or misfortune; themes of isolation, loss, or self-inflicted downfall"),
]

_LUNAR_PHASES = [
    (0,   45,  "New Moon",      "instinctive, subjective, seed-planting; life driven by pure potential and new beginnings"),
    (45,  90,  "Crescent",      "emerging from the past, striving to establish something new against resistance"),
    (90,  135, "First Quarter", "crisis of action; turning points demand decisive choices and bold moves"),
    (135, 180, "Gibbous",       "refinement and analysis; devoted to improvement, preparation, and perfecting one's craft"),
    (180, 225, "Full Moon",     "illumination and relationship; objectivity, heightened awareness, fulfillment through contrast"),
    (225, 270, "Disseminating", "sharing and teaching; purpose expressed through distributing knowledge and lived experience"),
    (270, 315, "Last Quarter",  "crisis of consciousness; reorientation, questioning old structures, conscious release"),
    (315, 360, "Balsamic",      "completion and transition; prophetic, future-oriented energy clearing the way for a new cycle"),
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


def _get_dignity(planet: str, sign: str) -> Optional[str]:
    d = _DIGNITIES.get(planet)
    if not d:
        return None
    for level in ("domicile", "exaltation", "detriment", "fall"):
        if sign in d[level]:
            return level
    return None


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
    s1 = _PLANET_SPEEDS.get(p1_name, 0) * (-1 if p1_retro else 1)
    s2 = _PLANET_SPEEDS.get(p2_name, 0) * (-1 if p2_retro else 1)
    rel = s1 - s2

    gap = (p1_abs - p2_abs) % 360
    if gap > 180:
        gap -= 360

    if aspect_angle == 0:
        exact = 0.0
    elif aspect_angle == 180:
        exact = 180.0 if gap >= 0 else -180.0
    else:
        exact = aspect_angle if abs(gap - aspect_angle) <= abs(gap + aspect_angle) else -aspect_angle

    deviation = gap - exact
    if rel == 0 or deviation == 0:
        return False
    return (deviation > 0) != (rel > 0)


def compute_balance(chart: dict) -> dict:
    """Count planetary distribution across elements and modalities."""
    elements: dict[str, int] = {"Fire": 0, "Earth": 0, "Air": 0, "Water": 0}
    modalities: dict[str, int] = {"Cardinal": 0, "Fixed": 0, "Mutable": 0}
    for planet in _PLANETS:
        data = chart.get(planet)
        if data and data.get("sign"):
            sign = data["sign"]
            el = _SIGN_ELEMENT.get(sign)
            mod = _SIGN_MODALITY.get(sign)
            if el:
                elements[el] += 1
            if mod:
                modalities[mod] += 1
    return {"elements": elements, "modalities": modalities}


def compute_chart_ruler(chart: dict) -> Optional[dict]:
    """Return data on the planet ruling the Ascendant sign (the chart ruler)."""
    asc = chart.get("ascendant")
    if not asc or not asc.get("sign"):
        return None
    asc_sign = asc["sign"]
    ruler_key = _SIGN_RULER.get(asc_sign)
    if not ruler_key:
        return None
    ruler_data = chart.get(ruler_key)
    if not ruler_data:
        return None
    return {
        "planet": ruler_key,
        "asc_sign": asc_sign,
        "sign": ruler_data.get("sign"),
        "position": ruler_data.get("position"),
        "house": ruler_data.get("house"),
        "retrograde": ruler_data.get("retrograde", False),
        "dignity": ruler_data.get("dignity"),
    }


def compute_house_rulers(chart: dict) -> dict:
    """Return ruling planet data keyed by house number string ('1'–'12')."""
    rulers = {}
    houses = chart.get("houses") or {}
    for num in range(1, 13):
        house_data = houses.get(str(num))
        if not house_data or not house_data.get("sign"):
            rulers[str(num)] = None
            continue
        ruler_key = _SIGN_RULER.get(house_data["sign"])
        if not ruler_key:
            rulers[str(num)] = None
            continue
        planet_data = chart.get(ruler_key)
        if not planet_data:
            rulers[str(num)] = None
            continue
        rulers[str(num)] = {
            "planet": ruler_key,
            "sign": planet_data.get("sign"),
            "position": planet_data.get("position"),
            "house": planet_data.get("house"),
            "retrograde": planet_data.get("retrograde", False),
            "dignity": planet_data.get("dignity"),
        }
    return rulers


def compute_progressions(
    birth_year: int, birth_month: int, birth_day: int,
    birth_hour: int, birth_minute: int,
    current_year: int, current_month: int, current_day: int,
    city: str, nation: str, tz_str: str,
) -> dict:
    """Compute secondary progressions: each year of life = 1 day after birth."""
    from datetime import date, timedelta

    birth_date = date(birth_year, birth_month, birth_day)
    current_date = date(current_year, current_month, current_day)
    age_years = (current_date - birth_date).days / 365.25
    progressed_date = birth_date + timedelta(days=age_years)

    subject = AstrologicalSubject(
        name="Progressed",
        year=progressed_date.year,
        month=progressed_date.month,
        day=progressed_date.day,
        hour=birth_hour,
        minute=birth_minute,
        city=city,
        nation=nation,
        tz_str=tz_str,
        online=True,
    )

    # Only personal planets progress meaningfully; outer planets barely move
    progressed: dict = {"progressed_date": progressed_date.isoformat()}
    for planet in ["sun", "moon", "mercury", "venus", "mars"]:
        data = _safe_planet(subject, planet)
        if data and data.get("sign"):
            dignity = _get_dignity(planet, data["sign"])
            if dignity:
                data["dignity"] = dignity
        progressed[planet] = data

    first = getattr(subject, "first_house", None)
    tenth = getattr(subject, "tenth_house", None)
    progressed["ascendant"] = {
        "sign": getattr(first, "sign", None),
        "position": round(getattr(first, "position", 0.0), 2),
        "abs_pos": round(getattr(first, "abs_pos", 0.0), 2),
    } if first else None
    progressed["midheaven"] = {
        "sign": getattr(tenth, "sign", None),
        "position": round(getattr(tenth, "position", 0.0), 2),
        "abs_pos": round(getattr(tenth, "abs_pos", 0.0), 2),
    } if tenth else None

    return progressed


def compute_progressed_aspects(natal_chart: dict, progressions: dict) -> list[dict]:
    """Compute aspects between progressed planets and natal chart points (1° orb)."""
    # Progressed bodies
    prog_bodies: dict[str, tuple[float, bool]] = {}
    for key in ["sun", "moon", "mercury", "venus", "mars"]:
        data = progressions.get(key)
        if data and data.get("abs_pos") is not None:
            prog_bodies[f"progressed_{key}"] = (data["abs_pos"], data.get("retrograde", False))
    for key in ["ascendant", "midheaven"]:
        data = progressions.get(key)
        if data and data.get("abs_pos") is not None:
            prog_bodies[f"progressed_{key}"] = (data["abs_pos"], False)

    # Natal reference points
    natal_bodies: dict[str, float] = {}
    for planet in _PLANETS:
        data = natal_chart.get(planet)
        if data and data.get("abs_pos") is not None:
            natal_bodies[planet] = data["abs_pos"]
    chiron = natal_chart.get("chiron")
    if chiron and chiron.get("abs_pos") is not None:
        natal_bodies["chiron"] = chiron["abs_pos"]
    for key in ("ascendant", "midheaven"):
        data = natal_chart.get(key)
        if data and data.get("abs_pos") is not None:
            natal_bodies[key] = data["abs_pos"]
    nn = natal_chart.get("north_node")
    if nn and nn.get("abs_pos") is not None:
        natal_bodies["north_node"] = nn["abs_pos"]

    aspects = []
    for prog_name, (prog_pos, prog_retro) in prog_bodies.items():
        for natal_name, natal_pos in natal_bodies.items():
            result = _find_aspect(prog_pos, natal_pos, max_orb=_PROGRESSED_ORB)
            if result:
                aspect_name, orb = result
                exact_angle = next(a for n, a, _ in _MAJOR_ASPECTS if n == aspect_name)
                base_name = prog_name.replace("progressed_", "")
                applying = _is_applying(base_name, prog_pos, prog_retro, natal_name, natal_pos, False, exact_angle)
                aspects.append({
                    "progressed_planet": prog_name,
                    "natal_planet": natal_name,
                    "aspect": aspect_name,
                    "orb": orb,
                    "applying": applying,
                })
    return aspects


def compute_lunar_phase(chart: dict) -> dict:
    """Return the natal lunar phase from the Sun-Moon angular separation."""
    sun = chart.get("sun")
    moon = chart.get("moon")
    if not sun or not moon or sun.get("abs_pos") is None or moon.get("abs_pos") is None:
        return {}
    angle = (moon["abs_pos"] - sun["abs_pos"]) % 360
    for start, end, name, desc in _LUNAR_PHASES:
        if start <= angle < end:
            return {"angle": round(angle, 2), "phase": name, "description": desc}
    return {"angle": round(angle, 2), "phase": "New Moon", "description": _LUNAR_PHASES[0][3]}


def compute_part_of_fortune(chart: dict) -> Optional[dict]:
    """Lot of Fortune: ASC + Moon - Sun (day chart) or ASC + Sun - Moon (night chart)."""
    asc = chart.get("ascendant")
    sun = chart.get("sun")
    moon = chart.get("moon")
    if not asc or not sun or not moon:
        return None
    if asc.get("abs_pos") is None or sun.get("abs_pos") is None or moon.get("abs_pos") is None:
        return None

    raw_house = sun.get("house")
    if isinstance(raw_house, int):
        sun_house_num = raw_house
    else:
        sun_house_num = _HOUSE_NUMBER.get(str(raw_house), 0)
    is_day = sun_house_num >= 7

    if is_day:
        pof_abs = (asc["abs_pos"] + moon["abs_pos"] - sun["abs_pos"]) % 360
    else:
        pof_abs = (asc["abs_pos"] + sun["abs_pos"] - moon["abs_pos"]) % 360

    sign, pos = _sign_from_abs_pos(pof_abs)
    result: dict = {
        "abs_pos": round(pof_abs, 2),
        "sign": sign,
        "position": pos,
        "chart_type": "day" if is_day else "night",
    }
    dignity = _get_dignity("moon", sign)
    if dignity:
        result["dignity"] = dignity
    return result


def compute_stelliums(chart: dict) -> list[dict]:
    """Detect 3+ planets in the same sign or house."""
    from collections import defaultdict
    sign_planets: dict = defaultdict(list)
    house_planets: dict = defaultdict(list)

    for planet in _PLANETS:
        data = chart.get(planet)
        if not data:
            continue
        if data.get("sign"):
            sign_planets[data["sign"]].append(planet)
        raw_house = data.get("house")
        if raw_house is not None:
            if isinstance(raw_house, int):
                house_num = raw_house
            else:
                house_num = _HOUSE_NUMBER.get(str(raw_house), 0)
            if house_num:
                house_planets[house_num].append(planet)

    stelliums = []
    for sign, planets in sign_planets.items():
        if len(planets) >= 3:
            stelliums.append({"type": "sign", "location": sign, "planets": planets})
    for house_num, planets in house_planets.items():
        if len(planets) >= 3:
            stelliums.append({"type": "house", "location": f"House {house_num}", "planets": planets})
    return stelliums


def compute_mutual_receptions(chart: dict) -> list[dict]:
    """Detect pairs of planets in each other's ruling signs."""
    ruler_planets = list(set(_SIGN_RULER.values()))
    receptions = []
    checked: set = set()

    for i, p1 in enumerate(ruler_planets):
        for p2 in ruler_planets[i + 1:]:
            key = frozenset({p1, p2})
            if key in checked:
                continue
            checked.add(key)
            d1 = chart.get(p1)
            d2 = chart.get(p2)
            if not d1 or not d2:
                continue
            if _SIGN_RULER.get(d1.get("sign")) == p2 and _SIGN_RULER.get(d2.get("sign")) == p1:
                receptions.append({
                    "planet1": p1, "planet1_sign": d1["sign"],
                    "planet2": p2, "planet2_sign": d2["sign"],
                })
    return receptions


def compute_anaretic_degrees(chart: dict) -> list[dict]:
    """Flag any planet or angle at 29° of a sign (finishing/urgency energy)."""
    anaretic = []
    for body in list(_PLANETS) + ["chiron", "ascendant", "midheaven", "north_node"]:
        data = chart.get(body)
        if not data:
            continue
        pos = data.get("position")
        if pos is not None and pos >= 29.0:
            anaretic.append({"body": body, "sign": data.get("sign"), "position": pos})
    return anaretic


def compute_sect(chart: dict) -> dict:
    """Determine day/night chart sect and flag each classical planet as in-sect or out-of-sect."""
    sun = chart.get("sun")
    if not sun:
        return {}

    raw_house = sun.get("house")
    sun_house = raw_house if isinstance(raw_house, int) else _HOUSE_NUMBER.get(str(raw_house), 0)
    is_day = sun_house >= 7

    planets_sect: dict[str, dict] = {}
    for planet in _PLANETS:
        if not chart.get(planet):
            continue
        if planet in _SECT_DIURNAL:
            sect = "diurnal"
            in_sect = is_day
        elif planet in _SECT_NOCTURNAL:
            sect = "nocturnal"
            in_sect = not is_day
        elif planet == "mercury":
            # Mercury adapts to the chart sect
            sect = "diurnal" if is_day else "nocturnal"
            in_sect = True
        else:
            # Outer planets (uranus, neptune, pluto) have no classical sect
            planets_sect[planet] = {"sect": None, "in_sect": None, "role": "outer"}
            continue

        if planet in _SECT_MALEFICS:
            role = "malefic"
        elif planet in _SECT_BENEFICS:
            role = "benefic"
        elif planet in ("sun", "moon"):
            role = "luminary"
        else:
            role = "neutral"

        planets_sect[planet] = {"sect": sect, "in_sect": in_sect, "role": role}

    return {"chart_type": "day" if is_day else "night", "planets": planets_sect}


def compute_fixed_star_conjunctions(chart: dict, orb: float = 1.0) -> list[dict]:
    """Return natal planets/angles conjunct significant fixed stars within `orb` degrees."""
    bodies: dict[str, float] = {}
    for planet in _PLANETS:
        d = chart.get(planet)
        if d and d.get("abs_pos") is not None:
            bodies[planet] = d["abs_pos"]
    for key in ("ascendant", "midheaven"):
        d = chart.get(key)
        if d and d.get("abs_pos") is not None:
            bodies[key] = d["abs_pos"]
    chiron = chart.get("chiron")
    if chiron and chiron.get("abs_pos") is not None:
        bodies["chiron"] = chiron["abs_pos"]
    nn = chart.get("north_node")
    if nn and nn.get("abs_pos") is not None:
        bodies["north_node"] = nn["abs_pos"]

    conjunctions = []
    for star_name, star_pos, nature, keywords in _FIXED_STARS:
        for body_name, body_pos in bodies.items():
            actual_orb = _angular_diff(body_pos, star_pos)
            if actual_orb <= orb:
                conjunctions.append({
                    "body": body_name,
                    "star": star_name,
                    "orb": round(actual_orb, 2),
                    "nature": nature,
                    "keywords": keywords,
                })
    conjunctions.sort(key=lambda x: x["orb"])
    return conjunctions


def compute_solar_arcs(natal_chart: dict, progressions: dict) -> dict:
    """Solar arc directions: advance every natal body by the progressed Sun's arc."""
    natal_sun = natal_chart.get("sun")
    prog_sun = progressions.get("sun")
    if not natal_sun or not prog_sun:
        return {}
    natal_sun_pos = natal_sun.get("abs_pos")
    prog_sun_pos = prog_sun.get("abs_pos")
    if natal_sun_pos is None or prog_sun_pos is None:
        return {}

    arc = (prog_sun_pos - natal_sun_pos) % 360
    result: dict = {"arc": round(arc, 3)}

    for body in list(_PLANETS) + ["chiron", "ascendant", "midheaven", "north_node"]:
        natal_data = natal_chart.get(body)
        if not natal_data or natal_data.get("abs_pos") is None:
            continue
        directed_abs = (natal_data["abs_pos"] + arc) % 360
        directed_sign, directed_pos = _sign_from_abs_pos(directed_abs)
        entry: dict = {"abs_pos": round(directed_abs, 2), "sign": directed_sign, "position": directed_pos}
        dignity = _get_dignity(body, directed_sign)
        if dignity:
            entry["dignity"] = dignity
        result[body] = entry

    return result


def compute_solar_arc_aspects(natal_chart: dict, solar_arcs: dict) -> list[dict]:
    """Aspects between solar arc directed positions and natal points (1° orb)."""
    if not solar_arcs:
        return []

    directed: dict[str, float] = {}
    for body in list(_PLANETS) + ["chiron", "ascendant", "midheaven", "north_node"]:
        data = solar_arcs.get(body)
        if data and data.get("abs_pos") is not None:
            directed[f"arc_{body}"] = data["abs_pos"]

    natal: dict[str, float] = {}
    for planet in _PLANETS:
        d = natal_chart.get(planet)
        if d and d.get("abs_pos") is not None:
            natal[planet] = d["abs_pos"]
    chiron = natal_chart.get("chiron")
    if chiron and chiron.get("abs_pos") is not None:
        natal["chiron"] = chiron["abs_pos"]
    for key in ("ascendant", "midheaven"):
        d = natal_chart.get(key)
        if d and d.get("abs_pos") is not None:
            natal[key] = d["abs_pos"]
    nn = natal_chart.get("north_node")
    if nn and nn.get("abs_pos") is not None:
        natal["north_node"] = nn["abs_pos"]

    aspects = []
    for arc_name, arc_pos in directed.items():
        for natal_name, natal_pos in natal.items():
            result = _find_aspect(arc_pos, natal_pos, max_orb=_PROGRESSED_ORB)
            if result:
                aspect_name, orb = result
                exact_angle = next(a for n, a, _ in _MAJOR_ASPECTS if n == aspect_name)
                gap = (arc_pos - natal_pos) % 360
                if gap > 180:
                    gap -= 360
                if exact_angle == 0:
                    exact = 0.0
                elif exact_angle == 180:
                    exact = 180.0 if gap >= 0 else -180.0
                else:
                    exact = exact_angle if abs(gap - exact_angle) <= abs(gap + exact_angle) else -exact_angle
                applying = (gap - exact) < 0
                aspects.append({
                    "directed_planet": arc_name,
                    "natal_planet": natal_name,
                    "aspect": aspect_name,
                    "orb": orb,
                    "applying": applying,
                })
    return aspects


def compute_solar_return(
    natal_chart: dict,
    birth_month: int, birth_day: int,
    current_year: int, current_month: int, current_day: int,
    natal_city: str, natal_nation: str, tz_str: str,
    current_city: str, current_nation: str,
) -> dict:
    """Find the exact solar return moment via binary search, then cast the chart."""
    from datetime import datetime, date, timedelta

    natal_sun = natal_chart.get("sun")
    if not natal_sun or natal_sun.get("abs_pos") is None:
        return {}
    natal_sun_abs = natal_sun["abs_pos"]

    # Choose solar return year: most recently completed (or imminent within 1 day)
    current_date = date(current_year, current_month, current_day)
    try:
        this_bday = date(current_year, birth_month, birth_day)
    except ValueError:
        this_bday = date(current_year, birth_month, min(birth_day, 28))

    sr_center = this_bday if this_bday <= current_date + timedelta(days=1) else (
        date(current_year - 1, birth_month, min(birth_day, 28))
    )

    lo = datetime(sr_center.year, sr_center.month, sr_center.day, 0, 0) - timedelta(days=2)
    hi = lo + timedelta(days=4)

    def sun_pos_at(dt: datetime) -> float:
        try:
            s = AstrologicalSubject(
                "SR_search", dt.year, dt.month, dt.day, dt.hour, dt.minute,
                city=natal_city, nation=natal_nation, tz_str=tz_str, online=True,
            )
            p = _safe_planet(s, "sun")
            return p["abs_pos"] if p and p.get("abs_pos") is not None else -1.0
        except Exception:
            return -1.0

    # Binary search — 10 iterations → ~0.005° precision (~18 min of time)
    result_dt = lo + (hi - lo) / 2
    for _ in range(10):
        mid = lo + (hi - lo) / 2
        pos = sun_pos_at(mid)
        if pos < 0:
            break
        diff = (pos - natal_sun_abs) % 360
        if diff > 180:
            diff -= 360
        if abs(diff) < 0.01:
            result_dt = mid
            break
        if diff > 0:
            hi = mid
        else:
            lo = mid
    else:
        result_dt = lo + (hi - lo) / 2

    # Cast the SR chart at the current location
    try:
        sr_subj = AstrologicalSubject(
            "Solar Return",
            result_dt.year, result_dt.month, result_dt.day,
            result_dt.hour, result_dt.minute,
            city=current_city, nation=current_nation, tz_str="UTC", online=True,
        )
    except Exception:
        return {}

    sr: dict = {"return_date": result_dt.strftime("%Y-%m-%d %H:%M UTC"), "return_year": result_dt.year}

    for planet in _PLANETS:
        sr[planet] = _safe_planet(sr_subj, planet)

    first = getattr(sr_subj, "first_house", None)
    tenth = getattr(sr_subj, "tenth_house", None)
    sr["ascendant"] = {
        "sign": getattr(first, "sign", None),
        "position": round(getattr(first, "position", 0.0), 2),
        "abs_pos": round(getattr(first, "abs_pos", 0.0), 2),
    } if first else None
    sr["midheaven"] = {
        "sign": getattr(tenth, "sign", None),
        "position": round(getattr(tenth, "position", 0.0), 2),
        "abs_pos": round(getattr(tenth, "abs_pos", 0.0), 2),
    } if tenth else None

    sr["houses"] = {}
    for i, attr in enumerate(_HOUSE_ATTRS, 1):
        sr["houses"][str(i)] = _safe_house(sr_subj, attr)

    # Planets within 5° of SR ASC or MC (angular = most prominent for the year)
    angular = []
    for key in ("ascendant", "midheaven"):
        angle = sr.get(key)
        if not angle or angle.get("abs_pos") is None:
            continue
        for planet in _PLANETS:
            p = sr.get(planet)
            if p and p.get("abs_pos") is not None:
                orb = _angular_diff(p["abs_pos"], angle["abs_pos"])
                if orb <= 5.0:
                    angular.append({"planet": planet, "angle": key, "orb": round(orb, 2)})
    sr["angular_planets"] = angular

    return sr


def compute_aspect_patterns(chart: dict, aspects: list[dict]) -> list[dict]:
    """Detect Grand Trine, T-Square, Grand Cross, and Yod configurations."""
    aspect_between: dict[frozenset, str] = {}
    for a in aspects:
        aspect_between[frozenset({a["planet1"], a["planet2"]})] = a["aspect"]

    def has_aspect(p1: str, p2: str, name: str) -> bool:
        return aspect_between.get(frozenset({p1, p2})) == name

    # Collect all body positions (same set as compute_aspects)
    all_pos: dict[str, float] = {}
    for planet in _PLANETS:
        d = chart.get(planet)
        if d and d.get("abs_pos") is not None:
            all_pos[planet] = d["abs_pos"]
    chiron = chart.get("chiron")
    if chiron and chiron.get("abs_pos") is not None:
        all_pos["chiron"] = chiron["abs_pos"]
    for key in ("ascendant", "midheaven"):
        d = chart.get(key)
        if d and d.get("abs_pos") is not None:
            all_pos[key] = d["abs_pos"]
    nn = chart.get("north_node")
    if nn and nn.get("abs_pos") is not None:
        all_pos["north_node"] = nn["abs_pos"]

    def has_quincunx(p1: str, p2: str) -> bool:
        if p1 not in all_pos or p2 not in all_pos:
            return False
        return abs(_angular_diff(all_pos[p1], all_pos[p2]) - 150) <= 3.0

    planets = list(all_pos.keys())
    n = len(planets)
    patterns: list[dict] = []
    seen_gt: set = set()
    seen_ts: set = set()
    seen_gc: set = set()
    seen_yod: set = set()

    # Grand Trine
    for i in range(n):
        for j in range(i + 1, n):
            for k in range(j + 1, n):
                A, B, C = planets[i], planets[j], planets[k]
                if has_aspect(A, B, "Trine") and has_aspect(B, C, "Trine") and has_aspect(A, C, "Trine"):
                    key = frozenset({A, B, C})
                    if key not in seen_gt:
                        seen_gt.add(key)
                        signs = [chart.get(p, {}).get("sign") for p in (A, B, C)]
                        elements = [_SIGN_ELEMENT.get(s) for s in signs if s]
                        element = elements[0] if elements and len(set(elements)) == 1 else None
                        patterns.append({"type": "Grand Trine", "planets": [A, B, C], "element": element, "apex": None})

    # T-Square
    for i in range(n):
        for j in range(i + 1, n):
            A, B = planets[i], planets[j]
            if not has_aspect(A, B, "Opposition"):
                continue
            for C in planets:
                if C in (A, B) or not (has_aspect(A, C, "Square") and has_aspect(B, C, "Square")):
                    continue
                key = frozenset({A, B, C})
                if key not in seen_ts:
                    seen_ts.add(key)
                    patterns.append({"type": "T-Square", "planets": [A, B, C], "element": None, "apex": C})

    # Grand Cross
    for i in range(n):
        for j in range(i + 1, n):
            for k in range(j + 1, n):
                for l in range(k + 1, n):
                    A, B, C, D = planets[i], planets[j], planets[k], planets[l]
                    all_six = [(A, B), (A, C), (A, D), (B, C), (B, D), (C, D)]
                    asp_counts = {"Opposition": 0, "Square": 0}
                    for p1, p2 in all_six:
                        v = aspect_between.get(frozenset({p1, p2}))
                        if v in asp_counts:
                            asp_counts[v] += 1
                    if asp_counts["Opposition"] == 2 and asp_counts["Square"] == 4:
                        key = frozenset({A, B, C, D})
                        if key not in seen_gc:
                            seen_gc.add(key)
                            patterns.append({"type": "Grand Cross", "planets": [A, B, C, D], "element": None, "apex": None})

    # Yod (Finger of God)
    for i in range(n):
        for j in range(i + 1, n):
            A, B = planets[i], planets[j]
            if not has_aspect(A, B, "Sextile"):
                continue
            for C in planets:
                if C in (A, B) or not (has_quincunx(A, C) and has_quincunx(B, C)):
                    continue
                key = frozenset({A, B, C})
                if key not in seen_yod:
                    seen_yod.add(key)
                    patterns.append({"type": "Yod", "planets": [A, B, C], "element": None, "apex": C})

    return patterns


def compute_profection(
    birth_year: int, birth_month: int, birth_day: int,
    current_year: int, current_month: int, current_day: int,
    chart: dict,
) -> dict:
    """Annual profection: each year of life activates the next house in sequence."""
    age = current_year - birth_year
    if (current_month, current_day) < (birth_month, birth_day):
        age -= 1
    profected_house = (age % 12) + 1

    house_data = (chart.get("houses") or {}).get(str(profected_house)) or {}
    house_sign = house_data.get("sign")
    lord = _SIGN_RULER.get(house_sign) if house_sign else None
    lord_data = chart.get(lord) if lord else None

    return {
        "age": age,
        "profected_house": profected_house,
        "house_sign": house_sign,
        "lord_of_year": lord,
        "lord_sign": lord_data.get("sign") if lord_data else None,
        "lord_position": lord_data.get("position") if lord_data else None,
        "lord_house": lord_data.get("house") if lord_data else None,
        "lord_retrograde": lord_data.get("retrograde", False) if lord_data else False,
        "lord_dignity": lord_data.get("dignity") if lord_data else None,
    }


def compute_aspects(chart: dict) -> list[dict]:
    bodies: dict[str, tuple[float, bool]] = {}
    for planet in _PLANETS:
        data = chart.get(planet)
        if data and data.get("abs_pos") is not None:
            bodies[planet] = (data["abs_pos"], data.get("retrograde", False))
    for key in ("ascendant", "midheaven"):
        data = chart.get(key)
        if data and data.get("abs_pos") is not None:
            bodies[key] = (data["abs_pos"], False)
    chiron_data = chart.get("chiron")
    if chiron_data and chiron_data.get("abs_pos") is not None:
        bodies["chiron"] = (chiron_data["abs_pos"], chiron_data.get("retrograde", False))
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
    subject = AstrologicalSubject(
        name=full_name,
        year=birth_year, month=birth_month, day=birth_day,
        hour=birth_hour, minute=birth_minute,
        city=city, nation=nation, tz_str=tz_str, online=True,
    )

    chart = {planet: _safe_planet(subject, planet) for planet in _PLANETS}

    # Ascendant and Midheaven
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

    # Chiron
    chiron = _safe_planet(subject, "chiron")
    if chiron and chiron.get("sign"):
        dignity = _get_dignity("chiron", chiron["sign"])
        if dignity:
            chiron["dignity"] = dignity
    chart["chiron"] = chiron

    # North Node and computed South Node
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

    # Essential dignities — added directly onto each planet dict
    for planet_name in _PLANETS:
        data = chart.get(planet_name)
        if data and data.get("sign"):
            dignity = _get_dignity(planet_name, data["sign"])
            if dignity:
                data["dignity"] = dignity

    # Elemental / modal balance and chart ruler (computed after dignities)
    chart["balance"] = compute_balance(chart)
    chart["chart_ruler"] = compute_chart_ruler(chart)

    # House rulers merged into each house entry
    for num_str, ruler in compute_house_rulers(chart).items():
        if chart["houses"].get(num_str) is not None:
            chart["houses"][num_str]["ruler"] = ruler

    # Natal lunar phase, Part of Fortune, stelliums, mutual receptions
    chart["lunar_phase"] = compute_lunar_phase(chart)
    chart["part_of_fortune"] = compute_part_of_fortune(chart)
    chart["stelliums"] = compute_stelliums(chart)
    chart["mutual_receptions"] = compute_mutual_receptions(chart)

    # Anaretic degrees, planetary sect, fixed star conjunctions
    chart["anaretic_degrees"] = compute_anaretic_degrees(chart)
    chart["sect"] = compute_sect(chart)
    chart["fixed_stars"] = compute_fixed_star_conjunctions(chart)

    return chart
