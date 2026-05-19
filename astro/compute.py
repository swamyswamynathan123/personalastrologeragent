from __future__ import annotations
import logging
from typing import Optional
from kerykeion import AstrologicalSubject

# kerykeion logs ERROR when GeoNames rate-limits; we fall back to Nominatim so these are harmless
logging.getLogger("kerykeion.fetch_geonames").setLevel(logging.CRITICAL)

_PLANETS = ["sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn", "uranus", "neptune", "pluto"]

_MAJOR_ASPECTS = [
    ("Conjunction", 0, 8),
    ("Sextile", 60, 6),
    ("Square", 90, 8),
    ("Trine", 120, 8),
    ("Opposition", 180, 8),
]

_MINOR_ASPECTS = [
    ("Semisquare", 45, 2),
    ("Sesquiquadrate", 135, 2),
    ("Quintile", 72, 2),
    ("Biquintile", 144, 2),
    ("Semisextile", 30, 1.5),
    ("Quincunx", 150, 3),
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

_ASTEROID_IDS = {"ceres": 17, "pallas": 18, "juno": 19, "vesta": 20}

_HOUSE_ORDINALS = [
    "First_House", "Second_House", "Third_House", "Fourth_House",
    "Fifth_House", "Sixth_House", "Seventh_House", "Eighth_House",
    "Ninth_House", "Tenth_House", "Eleventh_House", "Twelfth_House",
]

# kerykeion stores 3-letter sign abbreviations; map them to 0-based indices
_SIGN_ABBREV = {
    "Ari": 0, "Tau": 1, "Gem": 2, "Can": 3, "Leo": 4, "Vir": 5,
    "Lib": 6, "Sco": 7, "Sag": 8, "Cap": 9, "Aqu": 10, "Pis": 11,
}

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

_HOUSE_SYSTEM_CODES: dict[str, str] = {
    "Placidus": "P",
    "Whole Sign": "W",
    "Koch": "K",
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

# Firdaria time lords: major period sequences and durations (in years)
_FIRDARIA_DAY = [
    ("sun",        10), ("venus",       8), ("mercury",    13),
    ("moon",        9), ("saturn",      11), ("jupiter",    12),
    ("mars",        7), ("north_node",   3), ("south_node",  2),
]  # total 75 years
_FIRDARIA_NIGHT = [
    ("moon",        9), ("saturn",      11), ("jupiter",    12),
    ("mars",        7), ("sun",         10), ("venus",       8),
    ("mercury",    13), ("north_node",   3), ("south_node",  2),
]  # total 75 years
# Sub-lord sequences: 7 classical planets in Firdaria order (no nodes)
_FIRDARIA_SUB_DAY   = ["sun",  "venus",   "mercury", "moon", "saturn", "jupiter", "mars"]
_FIRDARIA_SUB_NIGHT = ["moon", "saturn",  "jupiter", "mars", "sun",    "venus",   "mercury"]

# Sect: classical day/night planet groupings
_SECT_DIURNAL = {"sun", "jupiter", "saturn"}     # day sect planets
_SECT_NOCTURNAL = {"moon", "venus", "mars"}       # night sect planets
_SECT_MALEFICS = {"saturn", "mars"}
_SECT_BENEFICS = {"jupiter", "venus"}

# Egyptian terms (bounds) — (start°, end°, planet) per sign; used in Almuten Figuris
_EGYPTIAN_TERMS: dict[str, list[tuple[int, int, str]]] = {
    "Aries":       [(0,6,"jupiter"),(6,12,"venus"),(12,20,"mercury"),(20,25,"mars"),(25,30,"saturn")],
    "Taurus":      [(0,8,"venus"),(8,14,"mercury"),(14,22,"jupiter"),(22,27,"saturn"),(27,30,"mars")],
    "Gemini":      [(0,6,"mercury"),(6,12,"jupiter"),(12,17,"venus"),(17,24,"mars"),(24,30,"saturn")],
    "Cancer":      [(0,7,"mars"),(7,13,"venus"),(13,19,"mercury"),(19,26,"jupiter"),(26,30,"saturn")],
    "Leo":         [(0,6,"jupiter"),(6,11,"venus"),(11,18,"saturn"),(18,24,"mercury"),(24,30,"mars")],
    "Virgo":       [(0,7,"mercury"),(7,17,"venus"),(17,21,"jupiter"),(21,28,"mars"),(28,30,"saturn")],
    "Libra":       [(0,6,"saturn"),(6,14,"mercury"),(14,21,"jupiter"),(21,28,"venus"),(28,30,"mars")],
    "Scorpio":     [(0,7,"mars"),(7,11,"venus"),(11,19,"mercury"),(19,24,"jupiter"),(24,30,"saturn")],
    "Sagittarius": [(0,12,"jupiter"),(12,17,"venus"),(17,21,"mercury"),(21,26,"saturn"),(26,30,"mars")],
    "Capricorn":   [(0,7,"mercury"),(7,14,"jupiter"),(14,22,"venus"),(22,26,"saturn"),(26,30,"mars")],
    "Aquarius":    [(0,7,"mercury"),(7,13,"venus"),(13,20,"jupiter"),(20,25,"mars"),(25,30,"saturn")],
    "Pisces":      [(0,12,"venus"),(12,16,"jupiter"),(16,19,"mercury"),(19,28,"mars"),(28,30,"saturn")],
}

# Faces (decans) — three 10° faces per sign, rulers in Chaldean order from sign ruler
_FACES: dict[str, list[str]] = {
    "Aries":       ["mars","sun","venus"],
    "Taurus":      ["mercury","moon","saturn"],
    "Gemini":      ["jupiter","mars","sun"],
    "Cancer":      ["venus","mercury","moon"],
    "Leo":         ["saturn","jupiter","mars"],
    "Virgo":       ["sun","venus","mercury"],
    "Libra":       ["moon","saturn","jupiter"],
    "Scorpio":     ["mars","sun","venus"],
    "Sagittarius": ["mercury","moon","saturn"],
    "Capricorn":   ["jupiter","mars","sun"],
    "Aquarius":    ["venus","mercury","moon"],
    "Pisces":      ["saturn","jupiter","mars"],
}

# Triplicity rulers (Ptolemaic system, day/night/cooperating)
_TRIPLICITY_RULERS: dict[str, dict[str, str]] = {
    "Fire":  {"day": "sun",    "night": "jupiter", "cooperating": "saturn"},
    "Earth": {"day": "venus",  "night": "moon",    "cooperating": "mars"},
    "Air":   {"day": "saturn", "night": "mercury", "cooperating": "jupiter"},
    "Water": {"day": "venus",  "night": "mars",    "cooperating": "moon"},
}

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

# ── Vedic / Jyotish constants ────────────────────────────────────────────────

_NAKSHATRA_NAMES = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
    "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
    "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishtha",
    "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati",
]

# Vimshottari lord for each nakshatra (cycles through 9 lords × 3 = 27)
_NAKSHATRA_LORDS = ["ketu", "venus", "sun", "moon", "mars", "rahu", "jupiter", "saturn", "mercury"]

# Vimshottari Dasha sequence: (planet, years); total = 120
_VIMSHOTTARI_SEQUENCE = [
    ("ketu", 7), ("venus", 20), ("sun", 6), ("moon", 10), ("mars", 7),
    ("rahu", 18), ("jupiter", 16), ("saturn", 19), ("mercury", 17),
]

# Navamsha (D9) starting sign index by element of the tropical sign
_D9_START: dict[str, int] = {"Fire": 0, "Earth": 9, "Air": 6, "Water": 3}

_NAKSHATRA_SIZE = 360.0 / 27  # 13.3333…°

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


def _house_from_lon(lon: float, houses: dict) -> Optional[str]:
    """Return kerykeion-style house name for an ecliptic longitude, given chart house cusps."""
    cusps = []
    for num_str, h in houses.items():
        if h and h.get("sign") and h.get("position") is not None:
            try:
                sign = h["sign"]
                # handle both abbreviated ("Vir") and full ("Virgo") sign names
                if sign in _SIGN_ABBREV:
                    idx = _SIGN_ABBREV[sign]
                else:
                    idx = _SIGNS.index(sign)
                abs_p = idx * 30.0 + h["position"]
                cusps.append((abs_p, int(num_str)))
            except (ValueError, KeyError):
                pass
    if len(cusps) < 12:
        return None
    cusps.sort()
    lon = lon % 360
    house_num = cusps[-1][1]
    for i in range(len(cusps)):
        curr_abs = cusps[i][0]
        next_abs = cusps[(i + 1) % len(cusps)][0]
        if next_abs > curr_abs:
            if curr_abs <= lon < next_abs:
                house_num = cusps[i][1]
                break
        else:  # crossing 0°
            if lon >= curr_abs or lon < next_abs:
                house_num = cusps[i][1]
                break
    return _HOUSE_ORDINALS[house_num - 1]


def _compute_asteroid_pos(jd: float, body_id: int, houses: dict) -> Optional[dict]:
    """Compute sign/position/house for a minor body via swisseph."""
    try:
        import os
        import swisseph as swe
        import kerykeion as _kery
        swe.set_ephe_path(os.path.join(os.path.dirname(_kery.__file__), "sweph"))
        result = swe.calc_ut(jd, body_id)
        lon, lon_speed = result[0][0], result[0][3]
        sign, pos = _sign_from_abs_pos(lon)
        return {
            "sign": sign,
            "position": pos,
            "abs_pos": round(lon, 2),
            "retrograde": lon_speed < 0,
            "house": _house_from_lon(lon, houses),
        }
    except Exception:
        return None


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


def _find_minor_aspect(pos1: float, pos2: float) -> Optional[tuple[str, float]]:
    diff = _angular_diff(pos1, pos2)
    for name, angle, orb in _MINOR_ASPECTS:
        actual_orb = abs(diff - angle)
        if actual_orb <= orb:
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

    # Progressed lunation phase: angle from prog Sun to prog Moon
    ps = progressed.get("sun")
    pm = progressed.get("moon")
    if ps and pm and ps.get("abs_pos") is not None and pm.get("abs_pos") is not None:
        angle = (pm["abs_pos"] - ps["abs_pos"]) % 360
        if angle < 45:
            phase, desc = "New Moon", "initiation and new beginning — commitments made now carry forward for ~29 years"
        elif angle < 90:
            phase, desc = "Crescent", "building momentum, breaking from conditioning, asserting intent"
        elif angle < 135:
            phase, desc = "First Quarter", "crisis of action, decisive turning point, breaking from the past"
        elif angle < 180:
            phase, desc = "Gibbous", "refinement and adjustment — perfecting skills before culmination"
        elif angle < 225:
            phase, desc = "Full Moon", "culmination, maximum awareness, relationships and polarity illuminated"
        elif angle < 270:
            phase, desc = "Disseminating", "sharing and teaching insights gained at the Full Moon"
        elif angle < 315:
            phase, desc = "Last Quarter", "crisis of consciousness, reorientation, releasing old structures"
        else:
            phase, desc = "Balsamic", "release and completion — the old cycle ending before rebirth"
        degrees_to_new = (360 - angle) % 360
        years_to_new = round(degrees_to_new / 12.0, 1)
        progressed["progressed_lunation"] = {
            "phase": phase,
            "angle": round(angle, 1),
            "description": desc,
            "years_to_next_new_moon": years_to_new,
        }

    return progressed


def compute_eclipse_sensitivity(
    chart: dict,
    current_year: int, current_month: int, current_day: int,
    current_hour: int = 12, current_minute: int = 0,
) -> list[dict]:
    """Return natal planets/angles within 3° of solar or lunar eclipses in a ±6-month window."""
    try:
        import os
        import swisseph as swe
        import kerykeion as _kery
        swe.set_ephe_path(os.path.join(os.path.dirname(_kery.__file__), "sweph"))

        current_jd = swe.julday(current_year, current_month, current_day,
                                current_hour + current_minute / 60.0)
        search_start = current_jd - 183

        eclipses: list[dict] = []

        # Solar eclipses — Sun position = eclipse degree
        jd = search_start
        for _ in range(5):
            try:
                retval, tret = swe.sol_eclipse_when_glob(jd, 0, 0, False)
                if retval < 0 or not tret or tret[0] == 0:
                    break
                ejd = tret[0]
                lon = swe.calc_ut(ejd, swe.SUN)[0][0]
                sign, pos = _sign_from_abs_pos(lon)
                eclipses.append({"type": "solar", "jd": ejd, "abs_pos": round(lon, 2),
                                  "sign": sign, "position": round(pos, 2),
                                  "timing": "past" if ejd < current_jd else "upcoming"})
                jd = ejd + 10
            except Exception:
                break

        # Lunar eclipses — Moon position = eclipse degree
        jd = search_start
        for _ in range(5):
            try:
                retval, tret = swe.lun_eclipse_when_glob(jd, 0, 0, False)
                if retval < 0 or not tret or tret[0] == 0:
                    break
                ejd = tret[0]
                lon = swe.calc_ut(ejd, swe.MOON)[0][0]
                sign, pos = _sign_from_abs_pos(lon)
                eclipses.append({"type": "lunar", "jd": ejd, "abs_pos": round(lon, 2),
                                  "sign": sign, "position": round(pos, 2),
                                  "timing": "past" if ejd < current_jd else "upcoming"})
                jd = ejd + 10
            except Exception:
                break

        # Keep only within ±6 months
        eclipses = [e for e in eclipses if abs(e["jd"] - current_jd) <= 183]

        if not eclipses:
            return []

        # Natal bodies to test
        bodies: dict[str, float] = {}
        for planet in _PLANETS:
            d = chart.get(planet)
            if d and d.get("abs_pos") is not None:
                bodies[planet] = d["abs_pos"]
        for key in ("ascendant", "midheaven", "north_node", "chiron"):
            d = chart.get(key)
            if d and d.get("abs_pos") is not None:
                bodies[key] = d["abs_pos"]

        hits: list[dict] = []
        for eclipse in eclipses:
            yr, mo, dy, _ = swe.revjul(eclipse["jd"])
            eclipse_date_str = f"{int(yr)}-{int(mo):02d}-{int(dy):02d}"
            for body, body_pos in bodies.items():
                diff = abs((body_pos - eclipse["abs_pos"] + 180) % 360 - 180)
                if diff <= 3.0:
                    body_data = chart.get(body) or {}
                    hits.append({
                        "body": body,
                        "body_sign": body_data.get("sign", "?"),
                        "body_pos": body_data.get("position", "?"),
                        "eclipse_type": eclipse["type"],
                        "eclipse_sign": eclipse["sign"],
                        "eclipse_pos": round(eclipse["position"], 2),
                        "eclipse_date": eclipse_date_str,
                        "orb": round(diff, 2),
                        "timing": eclipse["timing"],
                    })

        return sorted(hits, key=lambda x: x["orb"])
    except Exception:
        return []


def compute_retrograde_stations(
    chart: dict,
    current_year: int, current_month: int, current_day: int,
    current_hour: int = 12, current_minute: int = 0,
    window_days: int = 180,
    natal_orb: float = 3.0,
) -> list[dict]:
    """Find outer planet retrograde/direct stations within ±window_days of current date.

    Each station includes natal_contacts: natal planets within natal_orb of the station degree.
    Station degree is often more sensitive than the transit itself — a planet stationing
    at a natal point can hold that contact for weeks.
    """
    try:
        import os
        import swisseph as swe
        import kerykeion as _kery
        swe.set_ephe_path(os.path.join(os.path.dirname(_kery.__file__), "sweph"))

        current_jd = swe.julday(current_year, current_month, current_day,
                                 current_hour + current_minute / 60.0)

        outer_body_ids = {
            "mars": swe.MARS,
            "jupiter": swe.JUPITER,
            "saturn": swe.SATURN,
            "uranus": swe.URANUS,
            "neptune": swe.NEPTUNE,
            "pluto": swe.PLUTO,
        }

        # Build natal abs_pos lookup
        natal_bodies: dict[str, float] = {}
        for planet in _PLANETS:
            d = chart.get(planet)
            if d and d.get("abs_pos") is not None:
                natal_bodies[planet] = float(d["abs_pos"])
        for key in ("ascendant", "midheaven", "north_node"):
            d = chart.get(key)
            if d and d.get("abs_pos") is not None:
                natal_bodies[key] = float(d["abs_pos"])

        stations: list[dict] = []

        for planet_name, body_id in outer_body_ids.items():
            start_jd = current_jd - window_days
            end_jd = current_jd + window_days
            try:
                prev_speed = swe.calc_ut(start_jd, body_id)[0][3]
                prev_jd = start_jd
            except Exception:
                continue

            jd = start_jd + 1.0
            while jd <= end_jd:
                try:
                    speed = swe.calc_ut(jd, body_id)[0][3]
                except Exception:
                    jd += 1.0
                    continue

                if prev_speed * speed < 0:
                    # Speed changed sign — binary search for exact station JD
                    lo, hi = prev_jd, jd
                    for _ in range(30):
                        mid = (lo + hi) / 2
                        try:
                            mid_speed = swe.calc_ut(mid, body_id)[0][3]
                        except Exception:
                            break
                        if mid_speed * speed < 0:
                            lo = mid
                        else:
                            hi = mid

                    station_jd = (lo + hi) / 2
                    try:
                        station_lon = swe.calc_ut(station_jd, body_id)[0][0]
                    except Exception:
                        prev_speed, prev_jd = speed, jd
                        jd += 1.0
                        continue

                    yr, mo, dy, _ = swe.revjul(station_jd)
                    station_date = f"{int(yr)}-{int(mo):02d}-{int(dy):02d}"
                    sign, pos = _sign_from_abs_pos(station_lon)
                    station_type = "Direct" if prev_speed < 0 else "Retrograde"

                    natal_contacts = []
                    for body_name, body_abs in natal_bodies.items():
                        diff = abs((station_lon - body_abs + 180) % 360 - 180)
                        if diff <= natal_orb:
                            natal_contacts.append({"body": body_name, "orb": round(diff, 2)})
                    natal_contacts.sort(key=lambda x: x["orb"])

                    stations.append({
                        "planet": planet_name,
                        "station_type": station_type,
                        "date": station_date,
                        "sign": sign,
                        "position": round(pos, 2),
                        "abs_pos": round(station_lon, 2),
                        "natal_contacts": natal_contacts,
                        "days_from_now": round(station_jd - current_jd),
                        "past": station_jd < current_jd,
                    })

                prev_speed, prev_jd = speed, jd
                jd += 1.0

        return sorted(stations, key=lambda x: x["date"])
    except Exception:
        return []


def compute_transit_to_progressed(
    natal_chart: dict,
    progressions: dict,
    year: int, month: int, day: int, hour: int, minute: int,
    city: str, nation: str, tz_str: str,
    orb: float = 3.0,
) -> list[dict]:
    """Compute outer planet transits aspecting progressed planet positions.

    Distinct from natal transits — these hit the evolved, time-adjusted positions.
    A transit to the progressed Moon (fast-moving) is especially time-sensitive.
    """
    try:
        outer_transit_bodies = ["mars", "jupiter", "saturn", "uranus", "neptune", "pluto"]
        progressed_targets = ["sun", "moon", "mercury", "venus", "mars", "ascendant", "midheaven"]

        transit_subject = AstrologicalSubject(
            name="Transit", year=year, month=month, day=day, hour=hour, minute=minute,
            city=city, nation=nation, tz_str=tz_str, online=True,
        )

        transit_positions: dict[str, dict] = {}
        for body in outer_transit_bodies:
            planet = getattr(transit_subject, body, None)
            if planet is not None and hasattr(planet, "abs_pos"):
                transit_positions[body] = {
                    "abs_pos": float(planet.abs_pos),
                    "retrograde": getattr(planet, "retrograde", False),
                }

        prog_positions: dict[str, float] = {}
        if progressions:
            for body in progressed_targets:
                prog_body = progressions.get(body)
                if prog_body and prog_body.get("abs_pos") is not None:
                    prog_positions[body] = float(prog_body["abs_pos"])

        aspects = []
        for transit_name, transit_data in transit_positions.items():
            t_pos = transit_data["abs_pos"]
            t_retro = transit_data["retrograde"]
            for prog_name, p_pos in prog_positions.items():
                result = _find_aspect(t_pos, p_pos, max_orb=orb)
                if result:
                    aspect_name, actual_orb = result
                    exact_angle = next(a for n, a, _ in _MAJOR_ASPECTS if n == aspect_name)
                    applying = _is_applying(transit_name, t_pos, t_retro, prog_name, p_pos, False, exact_angle)
                    aspects.append({
                        "transiting_planet": transit_name,
                        "progressed_planet": prog_name,
                        "aspect": aspect_name,
                        "orb": actual_orb,
                        "applying": applying,
                        "retrograde": t_retro,
                    })

        return sorted(aspects, key=lambda x: x["orb"])
    except Exception:
        return []


def compute_primary_directions(
    natal_chart: dict,
    birth_year: int, birth_month: int, birth_day: int,
    birth_hour: int, birth_minute: int,
    current_year: int, current_month: int, current_day: int,
    tz_str: str,
    orb: float = 1.0,
) -> list[dict]:
    """Naibod primary directions: directed angles → natal planets, directed planets → natal angles.

    Each degree of ARMC advance ≈ 1 year of life (Naibod rate: 0.9856472°/year).
    The most time-sensitive major-life-event indicator in classical Western astrology.
    """
    try:
        import os
        import swisseph as swe
        import kerykeion as _kery
        import pytz
        from datetime import date, datetime

        swe.set_ephe_path(os.path.join(os.path.dirname(_kery.__file__), "sweph"))

        natal_armc = natal_chart.get("_natal_armc")
        natal_lat = natal_chart.get("_natal_lat")
        if natal_armc is None or natal_lat is None:
            return []

        # Natal JD (convert birth local time to UT)
        tz = pytz.timezone(tz_str or "UTC")
        local_dt = tz.localize(datetime(birth_year, birth_month, birth_day, birth_hour, birth_minute))
        utc_dt = local_dt.astimezone(pytz.UTC)
        natal_jd = swe.julday(utc_dt.year, utc_dt.month, utc_dt.day,
                              utc_dt.hour + utc_dt.minute / 60.0 + utc_dt.second / 3600.0)

        # Obliquity of the ecliptic at birth (linear approximation, accurate to 0.01°)
        T = (natal_jd - 2451545.0) / 36525.0
        eps = 23.439291111 - 0.013004167 * T

        # Age and Naibod arc
        birth_date = date(birth_year, birth_month, birth_day)
        current_date_obj = date(current_year, current_month, current_day)
        age_years = (current_date_obj - birth_date).days / 365.25
        arc = age_years * 0.9856472  # mean daily solar motion in degrees

        # Directed ARMC → directed house cusps
        directed_armc = (natal_armc + arc) % 360
        cusps, ascmc = swe.houses_armc(directed_armc, natal_lat, eps, b'P')
        directed_asc = ascmc[0]
        directed_mc = ascmc[1]

        results: list[dict] = []

        # 1. Directed Ascendant and Midheaven aspecting natal planets/angles
        natal_targets = {k: natal_chart.get(k) for k in (
            "sun", "moon", "mercury", "venus", "mars",
            "jupiter", "saturn", "uranus", "neptune", "pluto",
            "ascendant", "midheaven", "chiron", "north_node",
        )}

        for label, directed_lon in (("Directed Ascendant", directed_asc), ("Directed Midheaven", directed_mc)):
            for body_name, body_data in natal_targets.items():
                if not body_data or body_data.get("abs_pos") is None:
                    continue
                asp = _find_aspect(directed_lon, body_data["abs_pos"], max_orb=orb)
                if asp:
                    aspect_name, aspect_orb = asp
                    sign, pos = _sign_from_abs_pos(directed_lon)
                    results.append({
                        "directed_point": label,
                        "natal_point": body_name,
                        "aspect": aspect_name.lower(),
                        "orb": str(round(aspect_orb, 2)),
                        "directed_sign": sign,
                        "directed_pos": round(pos, 2),
                    })

        # 2. Directed planets aspecting all natal planets and angles (inter-planet directions)
        all_natal_targets: dict[str, float] = {}
        for angle in ("ascendant", "midheaven"):
            d = natal_chart.get(angle)
            if d and d.get("abs_pos") is not None:
                all_natal_targets[angle] = float(d["abs_pos"])
        for np_ in ("sun", "moon", "mercury", "venus", "mars", "jupiter",
                    "saturn", "uranus", "neptune", "pluto", "chiron", "north_node"):
            d = natal_chart.get(np_)
            if d and d.get("abs_pos") is not None:
                all_natal_targets[np_] = float(d["abs_pos"])

        for planet_name in ("sun", "moon", "mercury", "venus", "mars",
                            "jupiter", "saturn", "uranus", "neptune", "pluto"):
            pdata = natal_chart.get(planet_name)
            if not pdata or pdata.get("abs_pos") is None:
                continue
            # Convert natal ecliptic lon to RA, advance by arc, convert back
            eq = swe.cotrans((float(pdata["abs_pos"]), 0.0, 1.0), -eps)
            directed_ra = (eq[0] + arc) % 360
            ecl_back = swe.cotrans((directed_ra, eq[1], 1.0), eps)
            directed_planet_lon = ecl_back[0]

            for target_name, target_lon in all_natal_targets.items():
                if target_name == planet_name:
                    continue  # skip self
                asp = _find_aspect(directed_planet_lon, target_lon, max_orb=orb)
                if asp:
                    aspect_name, aspect_orb = asp
                    sign, pos = _sign_from_abs_pos(directed_planet_lon)
                    results.append({
                        "directed_point": f"Directed {planet_name.capitalize()}",
                        "natal_point": target_name,
                        "aspect": aspect_name.lower(),
                        "orb": str(round(aspect_orb, 2)),
                        "directed_sign": sign,
                        "directed_pos": round(pos, 2),
                    })

        return sorted(results, key=lambda x: float(x["orb"]))
    except Exception:
        return []


def compute_lunar_return(
    natal_chart: dict,
    current_year: int, current_month: int, current_day: int,
    current_hour: int, current_minute: int,
    city: str, nation: str,
) -> dict:
    """Compute the next lunar return chart: when the Moon returns to its natal degree.

    The lunar return recurs every ~27.3 days and provides monthly precision timing.
    Cast at the current location, not the birth location.
    """
    try:
        import os
        import swisseph as swe
        import kerykeion as _kery

        swe.set_ephe_path(os.path.join(os.path.dirname(_kery.__file__), "sweph"))

        natal_moon = natal_chart.get("moon")
        if not natal_moon or natal_moon.get("abs_pos") is None:
            return {}

        natal_moon_lon = float(natal_moon["abs_pos"])
        current_jd = swe.julday(current_year, current_month, current_day,
                                current_hour + current_minute / 60.0)

        # Moon's current longitude — estimate next crossing
        current_moon_lon = swe.calc_ut(current_jd, swe.MOON)[0][0]
        forward_dist = (natal_moon_lon - current_moon_lon) % 360
        approx_jd = current_jd + forward_dist / 13.2

        # Binary search within ±1.5 days of estimate
        lo, hi = approx_jd - 1.5, approx_jd + 1.5
        for _ in range(50):
            mid = (lo + hi) / 2
            mid_lon = swe.calc_ut(mid, swe.MOON)[0][0]
            dist_to_target = (natal_moon_lon - mid_lon) % 360
            if dist_to_target > 180:  # overshot
                hi = mid
            else:  # hasn't reached yet
                lo = mid
        lr_jd = (lo + hi) / 2

        # Convert JD to UTC calendar date/time
        yr, mo, dy, hr_frac = swe.revjul(lr_jd)
        hr_int = int(hr_frac)
        mn_int = int((hr_frac - hr_int) * 60)
        lr_date_str = f"{int(yr)}-{int(mo):02d}-{int(dy):02d}"
        lr_time_str = f"{hr_int:02d}:{mn_int:02d} UTC"

        # Build lunar return chart at current location
        lr_subject = AstrologicalSubject(
            name="Lunar Return",
            year=int(yr), month=int(mo), day=int(dy),
            hour=hr_int, minute=mn_int,
            city=city, nation=nation,
            tz_str="UTC",
            online=True,
        )

        first = getattr(lr_subject, "first_house", None)
        tenth = getattr(lr_subject, "tenth_house", None)

        lr: dict = {
            "return_date": lr_date_str,
            "return_time": lr_time_str,
            "ascendant": {
                "sign": getattr(first, "sign", None),
                "position": round(getattr(first, "position", 0.0), 2),
                "abs_pos": round(getattr(first, "abs_pos", 0.0), 2),
            } if first else None,
            "midheaven": {
                "sign": getattr(tenth, "sign", None),
                "position": round(getattr(tenth, "position", 0.0), 2),
                "abs_pos": round(getattr(tenth, "abs_pos", 0.0), 2),
            } if tenth else None,
        }

        # LR planet positions
        for planet in ("sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn"):
            lr[planet] = _safe_planet(lr_subject, planet)

        # Natal house mapping: which natal house does each LR planet fall in?
        natal_houses = natal_chart.get("houses") or {}
        for planet in ("sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn"):
            p = lr.get(planet)
            if p and p.get("abs_pos") is not None:
                natal_h = _house_from_lon(float(p["abs_pos"]), natal_houses)
                if natal_h:
                    hn = _HOUSE_NUMBER.get(natal_h)
                    if hn is not None:
                        p["natal_house"] = hn

        # Angular planets: within 5° of LR ASC or MC
        asc_abs = float(getattr(first, "abs_pos", 0) or 0) if first else None
        mc_abs = float(getattr(tenth, "abs_pos", 0) or 0) if tenth else None
        angular = []
        for planet in ("sun", "moon", "mercury", "venus", "mars",
                       "jupiter", "saturn", "uranus", "neptune", "pluto"):
            p = lr.get(planet) or _safe_planet(lr_subject, planet)
            if not p or p.get("abs_pos") is None:
                continue
            for angle_name, angle_abs in (("ascendant", asc_abs), ("midheaven", mc_abs)):
                if angle_abs is None:
                    continue
                diff = _angular_diff(float(p["abs_pos"]), angle_abs)
                if diff <= 5.0:
                    angular.append({"planet": planet, "angle": angle_name, "orb": round(diff, 2)})
        lr["angular_planets"] = angular

        # LR house-stellium detection (houses with 2+ planets)
        lr_houses: dict[str, dict] = {}
        for i, attr in enumerate(_HOUSE_ATTRS, 1):
            h = getattr(lr_subject, attr, None)
            if h:
                lr_houses[str(i)] = {
                    "sign": getattr(h, "sign", None),
                    "position": round(getattr(h, "position", 0.0), 2),
                    "abs_pos": round(getattr(h, "abs_pos", 0.0), 2),
                }

        lr_house_map: dict[str, list[str]] = {}
        all_planets = ("sun", "moon", "mercury", "venus", "mars",
                       "jupiter", "saturn", "uranus", "neptune", "pluto")
        for planet in all_planets:
            p = lr.get(planet) or _safe_planet(lr_subject, planet)
            if p and p.get("abs_pos") is not None:
                h = _house_from_lon(float(p["abs_pos"]), lr_houses)
                if h:
                    hn = _HOUSE_NUMBER.get(h)
                    if hn:
                        lr_house_map.setdefault(str(hn), []).append(planet)

        stellia = {}
        for house_str, planets_in in lr_house_map.items():
            if len(planets_in) >= 2:
                stellia[house_str] = [p.capitalize() for p in planets_in]
        if stellia:
            lr["stellia"] = stellia

        return lr
    except Exception:
        return {}


def compute_transit_passes(
    natal_chart: dict,
    current_year: int, current_month: int, current_day: int,
    current_hour: int = 12, current_minute: int = 0,
    window_days: int = 365,
    exact_orb: float = 0.5,
) -> list[dict]:
    """Scan 1 year for all exact transit contacts (outer planets → natal points).

    Returns each transit pair with all exact-contact dates grouped into passes.
    Multi-pass entries (2-3 dates) reveal the full retrograde triple-transit pattern
    with specific dates for each station, allowing precise life-event timing advice.
    """
    try:
        import os
        import swisseph as swe
        import kerykeion as _kery
        from datetime import date as dt_date, timedelta

        swe.set_ephe_path(os.path.join(os.path.dirname(_kery.__file__), "sweph"))

        outer_ids = {
            "saturn": swe.SATURN,
            "uranus": swe.URANUS,
            "neptune": swe.NEPTUNE,
            "pluto": swe.PLUTO,
        }

        # Natal positions to check against
        natal_pos: dict[str, float] = {}
        for body in list(_PLANETS) + ["ascendant", "midheaven", "north_node"]:
            d = natal_chart.get(body)
            if d and d.get("abs_pos") is not None:
                natal_pos[body] = float(d["abs_pos"])

        start_jd = swe.julday(current_year, current_month, current_day,
                              current_hour + current_minute / 60.0)

        # accumulate: key → list of (date_str, orb, retrograde)
        raw: dict[str, list[tuple[str, float, bool]]] = {}

        for planet_name, body_id in outer_ids.items():
            for day_offset in range(window_days + 1):
                jd = start_jd + day_offset
                try:
                    calc = swe.calc_ut(jd, body_id)[0]
                    t_lon = calc[0]
                    t_retro = calc[3] < 0
                except Exception:
                    continue

                yr, mo, dy, _ = swe.revjul(jd)
                date_str = f"{int(yr)}-{int(mo):02d}-{int(dy):02d}"

                for natal_name, n_lon in natal_pos.items():
                    asp = _find_aspect(t_lon, n_lon, max_orb=exact_orb)
                    if asp:
                        aspect_name, orb_val = asp
                        key = f"{planet_name}|{natal_name}|{aspect_name}"
                        raw.setdefault(key, []).append((date_str, round(orb_val, 2), t_retro))

        # Group consecutive days into distinct passes (gap > 14 days = new pass)
        results: list[dict] = []
        for key, contacts in raw.items():
            planet_name, natal_name, aspect_name = key.split("|")

            # Group into passes
            passes_grouped: list[list[tuple[str, float, bool]]] = []
            current_group: list[tuple[str, float, bool]] = [contacts[0]]
            for i in range(1, len(contacts)):
                prev_d = dt_date.fromisoformat(contacts[i - 1][0])
                curr_d = dt_date.fromisoformat(contacts[i][0])
                if (curr_d - prev_d).days <= 14:
                    current_group.append(contacts[i])
                else:
                    passes_grouped.append(current_group)
                    current_group = [contacts[i]]
            passes_grouped.append(current_group)

            # Peak (minimum orb) date for each pass
            pass_summaries = []
            for group in passes_grouped:
                peak = min(group, key=lambda x: x[1])
                pass_summaries.append({
                    "date": peak[0],
                    "orb": peak[1],
                    "retrograde": peak[2],
                })

            results.append({
                "transiting_planet": planet_name,
                "natal_planet": natal_name,
                "aspect": aspect_name,
                "passes": pass_summaries,
                "multi_pass": len(pass_summaries) > 1,
            })

        # Sort: multi-pass first, then by first pass date
        results.sort(key=lambda x: (not x["multi_pass"], x["passes"][0]["date"] if x["passes"] else "9999"))
        return results
    except Exception:
        return []


def compute_declinations(
    birth_year: int, birth_month: int, birth_day: int,
    birth_hour: int, birth_minute: int,
    tz_str: str = "UTC",
) -> dict:
    """Return declination (degrees, + = north / - = south) for each planet and angle."""
    try:
        import os, swisseph as swe, kerykeion as _kery, pytz as _pytz
        from datetime import datetime as _dt

        swe.set_ephe_path(os.path.join(os.path.dirname(_kery.__file__), "sweph"))
        tz = _pytz.timezone(tz_str or "UTC")
        local = tz.localize(_dt(birth_year, birth_month, birth_day, birth_hour, birth_minute))
        utc = local.astimezone(_pytz.UTC)
        jd = swe.julday(utc.year, utc.month, utc.day, utc.hour + utc.minute / 60.0)

        SEFLG_EQUATORIAL = 2048
        body_ids = {
            "sun": swe.SUN, "moon": swe.MOON, "mercury": swe.MERCURY,
            "venus": swe.VENUS, "mars": swe.MARS, "jupiter": swe.JUPITER,
            "saturn": swe.SATURN, "uranus": swe.URANUS, "neptune": swe.NEPTUNE,
            "pluto": swe.PLUTO, "north_node": swe.MEAN_NODE,
        }
        try:
            body_ids["chiron"] = swe.CHIRON
        except AttributeError:
            pass

        declinations: dict = {}
        for name, body_id in body_ids.items():
            try:
                pos = swe.calc_ut(jd, body_id, SEFLG_EQUATORIAL)[0]
                declinations[name] = round(pos[1], 3)
            except Exception:
                pass

        # Angles: ecliptic lon → equatorial via obliquity
        T = (jd - 2451545.0) / 36525.0
        eps = 23.439291111 - 0.013004167 * T
        return {"bodies": declinations, "eps": round(eps, 6), "jd": jd}
    except Exception:
        return {}


def _add_angle_declinations(natal_chart: dict, decl_data: dict) -> dict:
    """Extend declination dict with ASC and MC using their ecliptic abs_pos."""
    bodies = dict(decl_data.get("bodies") or {})
    eps = decl_data.get("eps")
    if eps is None:
        return bodies
    try:
        import swisseph as swe
        for angle_name in ("ascendant", "midheaven"):
            d = natal_chart.get(angle_name)
            if d and d.get("abs_pos") is not None:
                eq = swe.cotrans((float(d["abs_pos"]), 0.0, 1.0), -eps)
                bodies[angle_name] = round(eq[1], 3)
    except Exception:
        pass
    return bodies


def compute_parallel_aspects(natal_chart: dict, decl_data: dict, orb: float = 1.0) -> list[dict]:
    """Find parallel (same declination) and contra-parallel (equal but opposite) aspects."""
    try:
        bodies = _add_angle_declinations(natal_chart, decl_data)
        if not bodies:
            return []

        body_names = list(bodies.keys())
        results = []
        seen: set = set()

        for i, a in enumerate(body_names):
            for b in body_names[i + 1:]:
                key = (a, b)
                if key in seen:
                    continue
                seen.add(key)
                dec_a = bodies[a]
                dec_b = bodies[b]

                # Parallel: same hemisphere, nearly equal magnitude
                diff = abs(dec_a - dec_b)
                if diff <= orb:
                    results.append({
                        "planet_a": a, "planet_b": b,
                        "type": "parallel", "orb": round(diff, 2),
                        "dec_a": round(dec_a, 2), "dec_b": round(dec_b, 2),
                    })

                # Contra-parallel: opposite hemispheres, nearly equal magnitude
                if dec_a * dec_b < 0:  # opposite signs
                    contra = abs(abs(dec_a) - abs(dec_b))
                    if contra <= orb:
                        results.append({
                            "planet_a": a, "planet_b": b,
                            "type": "contra-parallel", "orb": round(contra, 2),
                            "dec_a": round(dec_a, 2), "dec_b": round(dec_b, 2),
                        })

        return sorted(results, key=lambda x: x["orb"])
    except Exception:
        return []


def compute_prenatal_syzygy(
    birth_year: int, birth_month: int, birth_day: int,
    birth_hour: int, birth_minute: int,
    tz_str: str = "UTC",
) -> dict:
    """Find the last New or Full Moon before birth (prenatal lunation / syzygy).

    The prenatal syzygy degree is the most sensitive point in the natal chart
    for Hellenistic timing: transits and directions over it resonate chart-wide.
    """
    try:
        import os, swisseph as swe, kerykeion as _kery, pytz as _pytz
        from datetime import datetime as _dt

        swe.set_ephe_path(os.path.join(os.path.dirname(_kery.__file__), "sweph"))
        tz = _pytz.timezone(tz_str or "UTC")
        local = tz.localize(_dt(birth_year, birth_month, birth_day, birth_hour, birth_minute))
        utc = local.astimezone(_pytz.UTC)
        birth_jd = swe.julday(utc.year, utc.month, utc.day,
                               utc.hour + utc.minute / 60.0)

        def phase_angle(jd: float) -> float:
            sun = swe.calc_ut(jd, swe.SUN)[0][0]
            moon = swe.calc_ut(jd, swe.MOON)[0][0]
            return (moon - sun) % 360

        # Approximate: locate the last NM and FM using mean synodic rate
        birth_a = phase_angle(birth_jd)
        days_since_nm = birth_a * 29.53059 / 360.0
        days_since_fm = ((birth_a - 180) % 360) * 29.53059 / 360.0

        if days_since_nm <= days_since_fm:
            target, approx_jd = 0.0, birth_jd - days_since_nm
        else:
            target, approx_jd = 180.0, birth_jd - days_since_fm

        # Binary search within ±2 days of estimate
        lo, hi = approx_jd - 2.0, min(approx_jd + 2.0, birth_jd - 0.01)
        for _ in range(60):
            mid = (lo + hi) / 2
            mid_a = phase_angle(mid)
            dist = (mid_a - target) % 360
            if dist < 180:  # past target (Moon has moved beyond)
                hi = mid
            else:
                lo = mid
        exact_jd = (lo + hi) / 2

        # Confirm it's before birth
        if exact_jd >= birth_jd:
            exact_jd -= 29.53059

        yr, mo, dy, hr_frac = swe.revjul(exact_jd)
        hr_int = int(hr_frac)
        mn_int = int((hr_frac - hr_int) * 60)

        # Syzygy degree = Sun's longitude (NM: Sun = Moon; FM: Sun is 180° from Moon)
        sun_lon = swe.calc_ut(exact_jd, swe.SUN)[0][0]
        sign_names = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
                      "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
        sign_idx = int(sun_lon / 30) % 12
        sign_pos = round(sun_lon % 30, 2)
        abs_pos = round(sun_lon, 2)

        # Eclipse check: was this syzygy also an eclipse?
        was_eclipse = False
        eclipse_label = None
        try:
            node_lon = swe.calc_ut(exact_jd, swe.MEAN_NODE)[0][0]
            moon_lon_at = swe.calc_ut(exact_jd, swe.MOON)[0][0]
            if target == 0.0:  # New Moon → solar eclipse when Sun within 18.5° of node
                dist = min((sun_lon - node_lon) % 360, (node_lon - sun_lon) % 360)
                was_eclipse = dist <= 18.5
                eclipse_label = "solar eclipse" if was_eclipse else None
            else:  # Full Moon → lunar eclipse when Moon within 12.5° of node
                dist = min((moon_lon_at - node_lon) % 360, (node_lon - moon_lon_at) % 360)
                was_eclipse = dist <= 12.5
                eclipse_label = "lunar eclipse" if was_eclipse else None
        except Exception:
            pass

        result = {
            "type": "new_moon" if target == 0.0 else "full_moon",
            "date": f"{int(yr)}-{int(mo):02d}-{int(dy):02d}",
            "time": f"{hr_int:02d}:{mn_int:02d} UTC",
            "sign": sign_names[sign_idx],
            "position": sign_pos,
            "abs_pos": abs_pos,
            "was_eclipse": was_eclipse,
        }
        if eclipse_label:
            result["eclipse_label"] = eclipse_label
        return result
    except Exception:
        return {}


def compute_minor_aspects(chart: dict) -> list[dict]:
    """Find minor aspects (semisquare, sesquiquadrate, quintile, biquintile, semisextile, quincunx)
    between all natal planets and angles."""
    bodies: dict[str, float] = {}
    for planet in _PLANETS:
        d = chart.get(planet)
        if d and d.get("abs_pos") is not None:
            bodies[planet] = float(d["abs_pos"])
    for key in ("ascendant", "midheaven", "north_node", "chiron"):
        d = chart.get(key)
        if d and d.get("abs_pos") is not None:
            bodies[key] = float(d["abs_pos"])

    results = []
    body_list = list(bodies.items())
    for i, (p1, pos1) in enumerate(body_list):
        for p2, pos2 in body_list[i + 1:]:
            result = _find_minor_aspect(pos1, pos2)
            if result:
                aspect_name, orb = result
                exact_angle = next(a for n, a, _ in _MINOR_ASPECTS if n == aspect_name)
                p1_retro = (chart.get(p1) or {}).get("retrograde", False)
                p2_retro = (chart.get(p2) or {}).get("retrograde", False)
                applying = _is_applying(p1, pos1, p1_retro, p2, pos2, p2_retro, exact_angle)
                results.append({
                    "planet1": p1, "planet2": p2,
                    "aspect": aspect_name, "orb": orb, "applying": applying,
                })
    return results


def compute_parans(
    natal_chart: dict,
    birth_year: int, birth_month: int, birth_day: int,
    birth_hour: int, birth_minute: int,
    tz_str: str = "UTC",
    orb_degrees: float = 1.5,
) -> list[dict]:
    """Compute natal parans: pairs of planets on different angles at the same sidereal time.

    A paran (para-Anastenaria) occurs when two planets simultaneously occupy different angles
    (Rising, Setting, MC, IC) — their energies are woven together at the level of lived experience.
    Computed analytically from equatorial coordinates: planets' angle-crossing LSTs within orb_degrees.
    """
    try:
        import os, swisseph as swe, kerykeion as _kery, pytz as _pytz, math
        from datetime import datetime as _dt

        swe.set_ephe_path(os.path.join(os.path.dirname(_kery.__file__), "sweph"))
        tz = _pytz.timezone(tz_str or "UTC")
        local = tz.localize(_dt(birth_year, birth_month, birth_day, birth_hour, birth_minute))
        utc = local.astimezone(_pytz.UTC)
        jd = swe.julday(utc.year, utc.month, utc.day, utc.hour + utc.minute / 60.0)

        natal_lat = natal_chart.get("_natal_lat")
        if natal_lat is None:
            return []
        lat_rad = math.radians(float(natal_lat))

        SEFLG_EQUATORIAL = 2048
        body_ids = {
            "sun": swe.SUN, "moon": swe.MOON, "mercury": swe.MERCURY,
            "venus": swe.VENUS, "mars": swe.MARS, "jupiter": swe.JUPITER,
            "saturn": swe.SATURN, "uranus": swe.URANUS, "neptune": swe.NEPTUNE,
            "pluto": swe.PLUTO,
        }

        # Equatorial coordinates at birth
        eq_pos: dict[str, dict] = {}
        for name, body_id in body_ids.items():
            try:
                pos = swe.calc_ut(jd, body_id, SEFLG_EQUATORIAL)[0]
                eq_pos[name] = {"ra": pos[0], "dec": pos[1]}
            except Exception:
                pass

        # Angle-crossing LSTs for each planet (degrees of RAMC)
        # MC: LST = RA; IC: LST = RA+180; Rising: LST = RA-H; Setting: LST = RA+H
        # H = arccos(-tan(lat)*tan(dec))
        angle_lsts: dict[str, dict[str, float]] = {}
        for planet, eq in eq_pos.items():
            ra, dec = eq["ra"], eq["dec"]
            lsts: dict[str, float] = {
                "MC": ra % 360,
                "IC": (ra + 180) % 360,
            }
            try:
                cos_H = -math.tan(lat_rad) * math.tan(math.radians(dec))
                if abs(cos_H) <= 1.0:
                    H = math.degrees(math.acos(cos_H))
                    lsts["Rising"] = (ra - H) % 360
                    lsts["Setting"] = (ra + H) % 360
            except (ValueError, ZeroDivisionError):
                pass
            angle_lsts[planet] = lsts

        # Find pairs within orb_degrees
        results = []
        planet_names = list(angle_lsts.keys())
        seen: set = set()
        for i, pa in enumerate(planet_names):
            for pb in planet_names[i + 1:]:
                for angle_a, lst_a in angle_lsts[pa].items():
                    for angle_b, lst_b in angle_lsts[pb].items():
                        if angle_a == angle_b:
                            continue
                        diff = abs(lst_a - lst_b)
                        if diff > 180:
                            diff = 360 - diff
                        if diff <= orb_degrees:
                            key = tuple(sorted([(pa, angle_a), (pb, angle_b)]))
                            if key in seen:
                                continue
                            seen.add(key)
                            results.append({
                                "planet_a": pa, "angle_a": angle_a,
                                "planet_b": pb, "angle_b": angle_b,
                                "orb": round(diff, 2),
                            })

        return sorted(results, key=lambda x: x["orb"])
    except Exception:
        return []


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


_VEDIC_OWN_SIGNS: dict[str, set] = {
    "sun":     {"Leo"},
    "moon":    {"Cancer"},
    "mars":    {"Aries", "Scorpio"},
    "mercury": {"Gemini", "Virgo"},
    "jupiter": {"Sagittarius", "Pisces"},
    "venus":   {"Taurus", "Libra"},
    "saturn":  {"Capricorn", "Aquarius"},
}

_VEDIC_EXALTATION: dict[str, str] = {
    "sun": "Aries", "moon": "Taurus", "mars": "Capricorn",
    "mercury": "Virgo", "jupiter": "Cancer",
    "venus": "Pisces", "saturn": "Libra",
}

_VEDIC_DEBILITATION: dict[str, str] = {
    "sun": "Libra", "moon": "Scorpio", "mars": "Cancer",
    "mercury": "Pisces", "jupiter": "Capricorn",
    "venus": "Virgo", "saturn": "Aries",
}

# Classical (Jyotish) sign rulerships — no outer planets
_VEDIC_SIGN_RULER: dict[str, str] = {
    "Aries": "mars", "Taurus": "venus", "Gemini": "mercury", "Cancer": "moon",
    "Leo": "sun", "Virgo": "mercury", "Libra": "venus", "Scorpio": "mars",
    "Sagittarius": "jupiter", "Capricorn": "saturn", "Aquarius": "saturn", "Pisces": "jupiter",
}

_KENDRA = {1, 4, 7, 10}
_TRIKONA = {1, 5, 9}


def compute_yogas(sidereal: dict) -> list[dict]:
    """Detect major Vedic yogas using whole-sign houses from the sidereal Lagna."""
    lagna = sidereal.get("ascendant")
    if not lagna or lagna.get("sidereal_abs") is None:
        return []

    lagna_sign_idx = int(lagna["sidereal_abs"] / 30) % 12

    def sid_sign(body: str) -> str | None:
        d = sidereal.get(body)
        return d.get("sign") if d else None

    def vedic_house(body: str) -> int | None:
        d = sidereal.get(body)
        if not d or d.get("sidereal_abs") is None:
            return None
        sign_idx = int(d["sidereal_abs"] / 30) % 12
        return ((sign_idx - lagna_sign_idx) % 12) + 1

    def house_sign_lord(house_num: int) -> str:
        sign = _SIGNS[(lagna_sign_idx + house_num - 1) % 12]
        return _VEDIC_SIGN_RULER.get(sign, "")

    yogas: list[dict] = []

    # ── Pancha Mahapurusha Yogas ──────────────────────────────────────────
    _PMP = [
        ("mars",    "Ruchaka Yoga",
         "Mars power yoga — exceptional courage, drive, leadership capacity, and physical vitality; a life defined by bold action and competitive excellence"),
        ("mercury", "Bhadra Yoga",
         "Mercury intellect yoga — extraordinary analytical brilliance, communication mastery, and business acumen; a natural teacher or strategist"),
        ("jupiter", "Hamsa Yoga",
         "Jupiter wisdom yoga — spiritual authority, teaching gifts, ethical stature, and a life that naturally attracts prosperity, respect, and wide influence"),
        ("venus",   "Malavya Yoga",
         "Venus grace yoga — artistic excellence, refined aesthetic sense, magnetic charm, and material comfort through creative gifts"),
        ("saturn",  "Shasha Yoga",
         "Saturn mastery yoga — authority built through sustained discipline, organizational power, and long-term perseverance; a life of earned achievement"),
    ]
    for planet, name, desc in _PMP:
        sign = sid_sign(planet)
        house = vedic_house(planet)
        if not sign or not house:
            continue
        in_own = sign in _VEDIC_OWN_SIGNS.get(planet, set())
        in_exalt = sign == _VEDIC_EXALTATION.get(planet)
        if (in_own or in_exalt) and house in _KENDRA:
            dignity = "own sign" if in_own else "exaltation"
            yogas.append({
                "name": name,
                "planets": [planet],
                "sign": sign,
                "house": house,
                "detail": f"{planet.capitalize()} in {dignity} in House {house} (Kendra)",
                "description": desc,
                "category": "Pancha Mahapurusha",
            })

    # ── Gajakesari Yoga ───────────────────────────────────────────────────
    moon_h = vedic_house("moon")
    jupiter_h = vedic_house("jupiter")
    if moon_h and jupiter_h:
        jup_from_moon = ((jupiter_h - moon_h) % 12) + 1
        if jup_from_moon in _KENDRA:
            moon_deb = sid_sign("moon") == _VEDIC_DEBILITATION.get("moon")
            jup_deb = sid_sign("jupiter") == _VEDIC_DEBILITATION.get("jupiter")
            strength = "weakened (debilitation)" if (moon_deb or jup_deb) else "strong"
            yogas.append({
                "name": "Gajakesari Yoga",
                "planets": ["moon", "jupiter"],
                "sign": f"Moon H{moon_h}, Jupiter H{jupiter_h}",
                "house": moon_h,
                "detail": f"Jupiter in House {jup_from_moon} from Moon ({strength})",
                "description": "Moon-Jupiter Kendra yoga — wisdom, benevolence, natural popularity, and the capacity to inspire others; associated with emotional intelligence and lasting reputation",
                "category": "Lunar",
            })

    # ── Raj Yoga (Kendra-Trikona lord conjunction or exchange) ────────────
    kendra_exclusive = {h: house_sign_lord(h) for h in [4, 7, 10]}   # not Trikona
    trikona_exclusive = {h: house_sign_lord(h) for h in [5, 9]}       # not Kendra
    seen_raj: set = set()

    for kh, kl in kendra_exclusive.items():
        for th, tl in trikona_exclusive.items():
            if not kl or not tl or kl == tl:
                continue
            pair = frozenset({kl, tl})
            if pair in seen_raj:
                continue
            kl_sign = sid_sign(kl)
            tl_sign = sid_sign(tl)
            if not kl_sign or not tl_sign:
                continue
            # Conjunction
            if kl_sign == tl_sign:
                seen_raj.add(pair)
                yogas.append({
                    "name": "Raj Yoga",
                    "planets": [kl, tl],
                    "sign": kl_sign,
                    "house": vedic_house(kl),
                    "detail": f"H{kh} lord ({kl.capitalize()}) + H{th} lord ({tl.capitalize()}) conjunct in {kl_sign}",
                    "description": f"Kendra-Trikona conjunction — lords of action (H{kh}) and fortune (H{th}) unite to create strong potential for success, authority, and achievement of life purpose",
                    "category": "Raj Yoga",
                })
            # Parivartana (exchange)
            elif _VEDIC_SIGN_RULER.get(kl_sign) == tl and _VEDIC_SIGN_RULER.get(tl_sign) == kl:
                seen_raj.add(pair)
                yogas.append({
                    "name": "Raj Yoga (Parivartana)",
                    "planets": [kl, tl],
                    "sign": f"{kl.capitalize()} in {kl_sign} ↔ {tl.capitalize()} in {tl_sign}",
                    "house": vedic_house(kl),
                    "detail": f"H{kh} lord ({kl.capitalize()}) and H{th} lord ({tl.capitalize()}) exchange signs",
                    "description": f"Parivartana Raj Yoga — Houses {kh} and {th} lords exchange signs, creating cooperative power that amplifies both the action principle (Kendra) and the fortune principle (Trikona) simultaneously",
                    "category": "Raj Yoga",
                })

    # ── Neecha Bhanga Raj Yoga (debilitation cancellation) ───────────────
    # Canceller = lord of the debilitation sign, or the planet exalted in that sign
    _NEECHA_BHANGA: dict[str, tuple] = {
        "sun":     ("venus",   "Libra"),
        "moon":    ("mars",    "Scorpio"),
        "mars":    ("moon",    "Cancer"),
        "mercury": ("jupiter", "Pisces"),
        "jupiter": ("saturn",  "Capricorn"),
        "venus":   ("mercury", "Virgo"),
        "saturn":  ("mars",    "Aries"),
    }
    for planet, (canceller, deb_sign) in _NEECHA_BHANGA.items():
        if sid_sign(planet) != deb_sign:
            continue
        c_house = vedic_house(canceller)
        if c_house and c_house in _KENDRA:
            yogas.append({
                "name": "Neecha Bhanga Raj Yoga",
                "planets": [planet, canceller],
                "sign": deb_sign,
                "house": vedic_house(planet),
                "detail": f"{planet.capitalize()} debilitated in {deb_sign}; {canceller.capitalize()} (canceller) in Kendra H{c_house}",
                "description": f"{planet.capitalize()} in {deb_sign} (debilitated), but the debilitation is cancelled by {canceller.capitalize()} in a Kendra — early struggles transform into exceptional resilience and eventual strength in the themes of {deb_sign}",
                "category": "Neecha Bhanga",
            })

    # ── Dhana Yoga (wealth — lords of 2 and 11 linked) ───────────────────
    lord_2 = house_sign_lord(2)
    lord_11 = house_sign_lord(11)
    if lord_2 and lord_11 and lord_2 != lord_11:
        l2_sign = sid_sign(lord_2)
        l11_sign = sid_sign(lord_11)
        l2_house = vedic_house(lord_2)
        l11_house = vedic_house(lord_11)
        if l2_sign and l11_sign:
            # Conjunction
            if l2_sign == l11_sign:
                yogas.append({
                    "name": "Dhana Yoga",
                    "planets": [lord_2, lord_11],
                    "sign": l2_sign,
                    "house": l2_house,
                    "detail": f"H2 lord ({lord_2.capitalize()}) + H11 lord ({lord_11.capitalize()}) conjunct in {l2_sign}",
                    "description": "Wealth yoga — lords of the 2nd (accumulated wealth) and 11th (income, gains) houses unite, indicating strong potential for financial accumulation and material prosperity",
                    "category": "Dhana Yoga",
                })
            # One lord placed in the other's house
            elif l2_house == 11 or l11_house == 2:
                detail = f"H2 lord in H11" if l2_house == 11 else f"H11 lord in H2"
                yogas.append({
                    "name": "Dhana Yoga",
                    "planets": [lord_2, lord_11],
                    "sign": l2_sign if l2_house == 11 else l11_sign,
                    "house": l2_house if l2_house == 11 else l11_house,
                    "detail": detail,
                    "description": "Wealth yoga — a wealth house lord placed in the other wealth house creates a direct pipeline between accumulation (H2) and income (H11)",
                    "category": "Dhana Yoga",
                })

    # ── Chandra-Mangala Yoga (Moon-Mars conjunction) ──────────────────────
    if moon_h and vedic_house("mars") == moon_h:
        yogas.append({
            "name": "Chandra-Mangala Yoga",
            "planets": ["moon", "mars"],
            "sign": sid_sign("moon") or "",
            "house": moon_h,
            "detail": f"Moon and Mars conjunct in H{moon_h}",
            "description": "Moon-Mars conjunction yoga — powerful emotional drive, entrepreneurial instinct, and financially motivated ambition; intensity of feeling fuels decisive action",
            "category": "Conjunction Yoga",
        })

    # ── Budha-Aditya Yoga (Sun-Mercury conjunction) ───────────────────────
    sun_sign = sid_sign("sun")
    mercury_sign = sid_sign("mercury")
    if sun_sign and sun_sign == mercury_sign:
        sun_h = vedic_house("sun")
        yogas.append({
            "name": "Budha-Aditya Yoga",
            "planets": ["sun", "mercury"],
            "sign": sun_sign,
            "house": sun_h,
            "detail": f"Sun and Mercury conjunct in {sun_sign} (H{sun_h})",
            "description": "Sun-Mercury conjunction yoga — solar confidence fused with sharp intellect; exceptional clarity of thought, effective communication, and leadership through intelligence",
            "category": "Conjunction Yoga",
        })

    return yogas


def lahiri_ayanamsa(year: int, month: int, day: int) -> float:
    """Lahiri (Chitrapaksha) ayanamsa — accurate ±0.5° for 1900–2100."""
    decimal_year = year + (month - 1) / 12.0 + (day - 1) / 365.25
    return 23.8531 + (decimal_year - 2000.0) * 0.01397


def _get_nakshatra(sidereal_abs: float) -> dict:
    nak_idx = int(sidereal_abs / _NAKSHATRA_SIZE) % 27
    pos_in_nak = sidereal_abs % _NAKSHATRA_SIZE
    pada = int(pos_in_nak / (_NAKSHATRA_SIZE / 4)) + 1
    lord_seq_idx = nak_idx % 9
    return {
        "name": _NAKSHATRA_NAMES[nak_idx],
        "lord": _NAKSHATRA_LORDS[lord_seq_idx],
        "pada": pada,
        "index": nak_idx,
    }


def _get_navamsha_sign(sidereal_abs: float) -> str:
    sign_idx = int(sidereal_abs / 30) % 12
    sign = _SIGNS[sign_idx]
    element = _SIGN_ELEMENT.get(sign, "Fire")
    pos_in_sign = sidereal_abs % 30
    nav_num = int(pos_in_sign / (30.0 / 9))  # 0–8
    d9_start = _D9_START.get(element, 0)
    return _SIGNS[(d9_start + nav_num) % 12]


def compute_vimshottari_dasha(
    moon_sidereal_abs: float,
    birth_year: int, birth_month: int, birth_day: int,
    current_year: int, current_month: int, current_day: int,
) -> dict:
    """Compute current Vimshottari Mahadasha and Antardasha from Moon's sidereal position."""
    from datetime import date, timedelta

    nak_idx = int(moon_sidereal_abs / _NAKSHATRA_SIZE) % 27
    lord_seq_idx = nak_idx % 9
    lord_name, lord_years = _VIMSHOTTARI_SEQUENCE[lord_seq_idx]

    # Fraction of nakshatra elapsed = fraction of mahadasha used at birth
    fraction_elapsed = (moon_sidereal_abs % _NAKSHATRA_SIZE) / _NAKSHATRA_SIZE
    years_elapsed_at_birth = fraction_elapsed * lord_years

    birth_date = date(birth_year, birth_month, birth_day)
    current_date = date(current_year, current_month, current_day)
    initial_maha_start = birth_date - timedelta(days=round(years_elapsed_at_birth * 365.25))

    # Flat sequence from that starting lord (5 cycles = 600 years, ample coverage)
    flat_seq = [_VIMSHOTTARI_SEQUENCE[(lord_seq_idx + i) % 9] for i in range(45)]

    maha_lord = maha_start = maha_end = None
    maha_years = 0
    cursor = initial_maha_start
    for planet, years in flat_seq:
        period_end = cursor + timedelta(days=round(years * 365.25))
        if cursor <= current_date < period_end:
            maha_lord, maha_start, maha_end, maha_years = planet, cursor, period_end, years
            break
        cursor = period_end

    if not maha_lord:
        return {}

    # Antardasha within current Mahadasha
    maha_seq_idx = next(i for i, (p, _) in enumerate(_VIMSHOTTARI_SEQUENCE) if p == maha_lord)
    antar_lord = antar_start = antar_end = None
    years_remaining_antar = None

    antar_cursor = maha_start
    for i in range(9):
        antar_seq_idx = (maha_seq_idx + i) % 9
        antar_planet, antar_years = _VIMSHOTTARI_SEQUENCE[antar_seq_idx]
        antar_days = round((maha_years * antar_years / 120.0) * 365.25)
        antar_end_dt = antar_cursor + timedelta(days=antar_days)
        if antar_cursor <= current_date < antar_end_dt:
            antar_lord, antar_start, antar_end = antar_planet, antar_cursor, antar_end_dt
            years_remaining_antar = round((antar_end - current_date).days / 365.25, 1)
            break
        antar_cursor = antar_end_dt

    return {
        "mahadasha_lord": maha_lord,
        "mahadasha_start": maha_start.isoformat(),
        "mahadasha_end": maha_end.isoformat(),
        "mahadasha_years": maha_years,
        "years_remaining_mahadasha": round((maha_end - current_date).days / 365.25, 1),
        "antardasha_lord": antar_lord,
        "antardasha_start": antar_start.isoformat() if antar_start else None,
        "antardasha_end": antar_end.isoformat() if antar_end else None,
        "years_remaining_antardasha": years_remaining_antar,
    }


def compute_vedic(
    chart: dict,
    birth_year: int, birth_month: int, birth_day: int,
    current_year: int, current_month: int, current_day: int,
) -> dict:
    """Compute Vedic/Jyotish overlay: Lahiri sidereal positions, nakshatras, navamsha, Vimshottari Dasha."""
    ayanamsa = lahiri_ayanamsa(birth_year, birth_month, birth_day)
    sidereal: dict = {"ayanamsa": round(ayanamsa, 4)}

    for body in list(_PLANETS) + ["ascendant", "midheaven", "north_node"]:
        data = chart.get(body)
        if not data or data.get("abs_pos") is None:
            continue
        sid_abs = (data["abs_pos"] - ayanamsa) % 360
        sid_sign, sid_pos = _sign_from_abs_pos(sid_abs)
        entry: dict = {
            "sidereal_abs": round(sid_abs, 2),
            "sign": sid_sign,
            "position": round(sid_pos, 2),
            "navamsha": _get_navamsha_sign(sid_abs),
        }
        if body == "moon":
            entry["nakshatra"] = _get_nakshatra(sid_abs)
        sidereal[body] = entry

    moon_sid = sidereal.get("moon")
    dasha: dict = {}
    if moon_sid and moon_sid.get("sidereal_abs") is not None:
        dasha = compute_vimshottari_dasha(
            moon_sid["sidereal_abs"],
            birth_year, birth_month, birth_day,
            current_year, current_month, current_day,
        )

    yogas = compute_yogas(sidereal)

    return {"ayanamsa": round(ayanamsa, 4), "sidereal": sidereal, "dasha": dasha, "yogas": yogas}


def compute_upcoming_transits(
    natal_chart: dict,
    current_year: int, current_month: int, current_day: int,
    current_hour: int, current_minute: int,
    current_city: str, current_nation: str,
    days_ahead: int = 90,
) -> list[dict]:
    """
    Find transits that will become exact within `days_ahead` days.
    Uses daily position stepping for slow planets (Jupiter–Pluto) and
    speed-extrapolation for personal planets to keep API calls low.
    Only outer transiting planets (Jupiter through Pluto) are tracked —
    personal planet transits move too fast to be meaningful over 90 days.
    """
    from datetime import date, timedelta

    OUTER_PLANETS = ["jupiter", "saturn", "uranus", "neptune", "pluto"]
    NATAL_POINTS = list(_PLANETS) + ["ascendant", "midheaven", "north_node"]
    ORB_ENTER = 2.0   # start tracking when within 2°
    ORB_EXACT = 0.5   # call it "exact" when within 0.5°

    # Collect natal absolute positions
    natal_pos: dict[str, float] = {}
    for body in NATAL_POINTS:
        d = natal_chart.get(body)
        if d and d.get("abs_pos") is not None:
            natal_pos[body] = d["abs_pos"]

    current_date = date(current_year, current_month, current_day)

    # Step through days; only recompute transit positions when needed
    # For outer planets, positions barely change day-to-day — step every 3 days
    step = 3
    upcoming: dict[str, dict] = {}  # key = "transiting_planet|natal_planet|aspect"

    check_dates = [current_date + timedelta(days=i) for i in range(0, days_ahead + 1, step)]

    for check_date in check_dates:
        try:
            transit_subj = AstrologicalSubject(
                name="Transit",
                year=check_date.year, month=check_date.month, day=check_date.day,
                hour=current_hour, minute=current_minute,
                city=current_city, nation=current_nation, tz_str="UTC", online=True,
            )
        except Exception:
            continue

        for t_planet in OUTER_PLANETS:
            t_data = _safe_planet(transit_subj, t_planet)
            if not t_data or t_data.get("abs_pos") is None:
                continue
            t_pos = t_data["abs_pos"]
            t_retro = t_data.get("retrograde", False)

            for n_planet, n_pos in natal_pos.items():
                result = _find_aspect(t_pos, n_pos, max_orb=ORB_ENTER)
                if not result:
                    continue
                aspect_name, orb = result
                key = f"{t_planet}|{n_planet}|{aspect_name}"
                exact_angle = next(a for nm, a, _ in _MAJOR_ASPECTS if nm == aspect_name)
                applying = _is_applying(t_planet, t_pos, t_retro, n_planet, n_pos, False, exact_angle)

                if key not in upcoming:
                    upcoming[key] = {
                        "transiting_planet": t_planet,
                        "natal_planet": n_planet,
                        "aspect": aspect_name,
                        "first_seen": check_date.isoformat(),
                        "min_orb": orb,
                        "exact_date": check_date.isoformat() if orb <= ORB_EXACT else None,
                        "applying": applying,
                        "retrograde": t_retro,
                    }
                else:
                    # Update minimum orb and exact date
                    if orb < upcoming[key]["min_orb"]:
                        upcoming[key]["min_orb"] = orb
                    if orb <= ORB_EXACT and upcoming[key]["exact_date"] is None:
                        upcoming[key]["exact_date"] = check_date.isoformat()

    # Filter: keep only those that will be exact (≤0.5°) within the window, or are currently applying
    result_list = [
        v for v in upcoming.values()
        if v["exact_date"] is not None or (v["applying"] and v["min_orb"] <= ORB_ENTER)
    ]

    # Sort by exact_date, then by min_orb
    result_list.sort(key=lambda x: (x["exact_date"] or "9999", x["min_orb"]))
    return result_list


def compute_transit_calendar(
    natal_chart: dict,
    current_year: int, current_month: int, current_day: int,
    current_hour: int, current_minute: int,
    current_city: str, current_nation: str,
    months_ahead: int = 12,
) -> dict[str, list[dict]]:
    """
    Month-by-month transit calendar for the next N months.
    Returns a dict keyed by 'YYYY-MM' with sorted lists of transit events.
    Only outer transiting planets (Jupiter–Pluto) against all natal points.
    Uses stored lat/lng from natal chart to avoid geocoding entirely.
    """
    from datetime import date, timedelta

    OUTER_PLANETS = ["jupiter", "saturn", "uranus", "neptune", "pluto"]
    NATAL_POINTS = list(_PLANETS) + ["ascendant", "midheaven", "north_node"]
    # Match the orbs used by compute_upcoming_transits
    ORB_ENTER = 2.0
    ORB_EXACT = 0.5

    natal_pos: dict[str, float] = {}
    for body in NATAL_POINTS:
        d = natal_chart.get(body)
        if d and isinstance(d, dict) and d.get("abs_pos") is not None:
            natal_pos[body] = float(d["abs_pos"])

    if not natal_pos:
        return {}

    # Use stored coordinates to skip geocoding on every step
    lat = natal_chart.get("_current_lat") or natal_chart.get("_natal_lat") or 0.0
    lng = natal_chart.get("_current_lng") or natal_chart.get("_natal_lng") or 0.0
    use_coords = bool(lat or lng)

    current_date = date(current_year, current_month, current_day)
    end_date = current_date + timedelta(days=months_ahead * 30 + 15)
    step = 4  # 4-day steps: ~92 checks for 12 months, fast with cached coords
    check_dates = [
        current_date + timedelta(days=i)
        for i in range(0, (end_date - current_date).days + 1, step)
    ]

    transit_events: dict[str, dict] = {}

    for check_date in check_dates:
        try:
            if use_coords:
                transit_subj = AstrologicalSubject(
                    name="Transit",
                    year=check_date.year, month=check_date.month, day=check_date.day,
                    hour=current_hour, minute=current_minute,
                    lat=lat, lng=lng, tz_str="UTC", online=False,
                )
            else:
                transit_subj = AstrologicalSubject(
                    name="Transit",
                    year=check_date.year, month=check_date.month, day=check_date.day,
                    hour=current_hour, minute=current_minute,
                    city=current_city, nation=current_nation, tz_str="UTC", online=True,
                )
        except Exception:
            continue

        for t_planet in OUTER_PLANETS:
            t_data = _safe_planet(transit_subj, t_planet)
            if not t_data or t_data.get("abs_pos") is None:
                continue
            t_pos = float(t_data["abs_pos"])
            t_retro = t_data.get("retrograde", False)

            for n_planet, n_pos in natal_pos.items():
                result = _find_aspect(t_pos, n_pos, max_orb=ORB_ENTER)
                if not result:
                    continue
                aspect_name, orb = result
                key = f"{t_planet}|{n_planet}|{aspect_name}"
                exact_angle = next(a for nm, a, _ in _MAJOR_ASPECTS if nm == aspect_name)
                applying = _is_applying(t_planet, t_pos, t_retro, n_planet, n_pos, False, exact_angle)

                if key not in transit_events:
                    transit_events[key] = {
                        "transiting_planet": t_planet,
                        "natal_planet": n_planet,
                        "aspect": aspect_name,
                        "first_date": check_date.isoformat(),
                        "last_date": check_date.isoformat(),
                        "exact_date": check_date.isoformat() if orb <= ORB_EXACT else None,
                        "min_orb": orb,
                        "retrograde": t_retro,
                    }
                else:
                    transit_events[key]["last_date"] = check_date.isoformat()
                    if orb < transit_events[key]["min_orb"]:
                        transit_events[key]["min_orb"] = orb
                    if orb <= ORB_EXACT and transit_events[key]["exact_date"] is None:
                        transit_events[key]["exact_date"] = check_date.isoformat()

    # Group by the month of the exact date (fall back to first_date)
    monthly: dict[str, list[dict]] = {}
    for event in transit_events.values():
        month_key = (event["exact_date"] or event["first_date"])[:7]
        monthly.setdefault(month_key, []).append(event)

    for month_events in monthly.values():
        month_events.sort(key=lambda x: (x["exact_date"] or x["first_date"], x["transiting_planet"]))

    return dict(sorted(monthly.items()))


def compute_firdaria(
    birth_year: int, birth_month: int, birth_day: int,
    current_year: int, current_month: int, current_day: int,
    is_day_chart: bool,
) -> dict:
    """Return the current Firdaria major and sub period for the given birth/current dates."""
    from datetime import date, timedelta

    birth_date = date(birth_year, birth_month, birth_day)
    current_date = date(current_year, current_month, current_day)

    sequence = _FIRDARIA_DAY if is_day_chart else _FIRDARIA_NIGHT
    sub_seq_base = _FIRDARIA_SUB_DAY if is_day_chart else _FIRDARIA_SUB_NIGHT

    # Walk through repeating 75-year cycles until current_date is bracketed
    major_lord = major_start = major_end = None
    major_years = 0
    cursor = birth_date

    for _ in range(10):  # 10 cycles × 75 years = 750 years, more than enough
        for planet, years in sequence:
            days = round(years * 365.25)
            period_end = cursor + timedelta(days=days)
            if cursor <= current_date < period_end:
                major_lord, major_start, major_end, major_years = planet, cursor, period_end, years
                break
            cursor = period_end
        if major_lord:
            break

    if not major_lord:
        return {}

    # Sub-periods: nodes have no sub-lords
    sub_lord = sub_start = sub_end = None
    years_remaining_sub = None

    if major_lord not in ("north_node", "south_node"):
        try:
            idx = sub_seq_base.index(major_lord)
        except ValueError:
            idx = 0
        sub_sequence = sub_seq_base[idx:] + sub_seq_base[:idx]
        sub_days = (major_years * 365.25) / 7
        sub_cursor = major_start
        for sub_planet in sub_sequence:
            sub_end_dt = sub_cursor + timedelta(days=round(sub_days))
            if sub_cursor <= current_date < sub_end_dt:
                sub_lord, sub_start, sub_end = sub_planet, sub_cursor, sub_end_dt
                years_remaining_sub = round((sub_end - current_date).days / 365.25, 1)
                break
            sub_cursor = sub_end_dt

    return {
        "major_lord": major_lord,
        "major_period_start": major_start.isoformat(),
        "major_period_end": major_end.isoformat(),
        "major_period_years": major_years,
        "years_remaining_major": round((major_end - current_date).days / 365.25, 1),
        "sub_lord": sub_lord,
        "sub_period_start": sub_start.isoformat() if sub_start else None,
        "sub_period_end": sub_end.isoformat() if sub_end else None,
        "years_remaining_sub": years_remaining_sub,
    }


def generate_transit_svg(
    full_name: str,
    birth_year: int, birth_month: int, birth_day: int,
    birth_hour: int, birth_minute: int,
    city: str, nation: str, tz_str: str,
    transit_year: int, transit_month: int, transit_day: int,
    transit_hour: int, transit_minute: int,
    transit_city: str, transit_nation: str,
    house_system: str = "Placidus",
    natal_lat: float | None = None,
    natal_lng: float | None = None,
    transit_lat: float | None = None,
    transit_lng: float | None = None,
) -> str:
    """Render a transit chart overlay SVG (natal wheel + current sky) via kerykeion."""
    try:
        from kerykeion import KerykeionChartSVG
        hs_code = _HOUSE_SYSTEM_CODES.get(house_system, "P")
        if natal_lat is not None and natal_lng is not None:
            natal = AstrologicalSubject(
                name=full_name,
                year=birth_year, month=birth_month, day=birth_day,
                hour=birth_hour, minute=birth_minute,
                lat=natal_lat, lng=natal_lng, tz_str=tz_str, online=False,
                houses_system_identifier=hs_code,
            )
        else:
            natal = AstrologicalSubject(
                name=full_name,
                year=birth_year, month=birth_month, day=birth_day,
                hour=birth_hour, minute=birth_minute,
                city=city, nation=nation, tz_str=tz_str, online=True,
                houses_system_identifier=hs_code,
            )
        if transit_lat is not None and transit_lng is not None:
            transit = AstrologicalSubject(
                name="Current Sky",
                year=transit_year, month=transit_month, day=transit_day,
                hour=transit_hour, minute=transit_minute,
                lat=transit_lat, lng=transit_lng, tz_str="UTC", online=False,
                houses_system_identifier=hs_code,
            )
        else:
            transit = AstrologicalSubject(
                name="Current Sky",
                year=transit_year, month=transit_month, day=transit_day,
                hour=transit_hour, minute=transit_minute,
                city=transit_city, nation=transit_nation, tz_str="UTC", online=True,
                houses_system_identifier=hs_code,
            )
        return KerykeionChartSVG(natal, chart_type="Transit", second_obj=transit).makeTemplate()
    except Exception:
        return ""


def generate_chart_svg(
    full_name: str,
    birth_year: int, birth_month: int, birth_day: int,
    birth_hour: int, birth_minute: int,
    city: str, nation: str, tz_str: str,
    house_system: str = "Placidus",
    lat: float | None = None,
    lng: float | None = None,
) -> str:
    """Render natal chart wheel as an SVG string via kerykeion."""
    try:
        from kerykeion import KerykeionChartSVG
        hs_code = _HOUSE_SYSTEM_CODES.get(house_system, "P")
        if lat is not None and lng is not None:
            subject = AstrologicalSubject(
                name=full_name,
                year=birth_year, month=birth_month, day=birth_day,
                hour=birth_hour, minute=birth_minute,
                lat=lat, lng=lng, tz_str=tz_str, online=False,
                houses_system_identifier=hs_code,
            )
        else:
            subject = AstrologicalSubject(
                name=full_name,
                year=birth_year, month=birth_month, day=birth_day,
                hour=birth_hour, minute=birth_minute,
                city=city, nation=nation, tz_str=tz_str, online=True,
                houses_system_identifier=hs_code,
            )
        return KerykeionChartSVG(subject, chart_type="Natal").makeTemplate()
    except Exception:
        return ""


def generate_vedic_chart_svg(
    full_name: str,
    birth_year: int, birth_month: int, birth_day: int,
    birth_hour: int, birth_minute: int,
    tz_str: str,
    lat: float,
    lng: float,
) -> str:
    """Render a South Indian square Vedic chart (sidereal Lahiri, Whole Sign)."""
    try:
        subject = AstrologicalSubject(
            name=full_name,
            year=birth_year, month=birth_month, day=birth_day,
            hour=birth_hour, minute=birth_minute,
            lat=lat, lng=lng, tz_str=tz_str, online=False,
            zodiac_type="Sidereal", sidereal_mode="LAHIRI",
            houses_system_identifier="W",
        )

        def _sign_to_idx(sign_str: str) -> int:
            s = (sign_str or "").strip()
            if s in _SIGN_ABBREV:
                return _SIGN_ABBREV[s]
            sl = s.lower()
            for i, name in enumerate(_SIGNS):
                if name.lower() == sl or name[:3].lower() == sl[:3]:
                    return i
            return 0

        # Collect planet → sign index
        _PLANET_ATTRS = [
            ("sun",     "☉ Sun"),
            ("moon",    "☽ Moon"),
            ("mercury", "☿ Mercury"),
            ("venus",   "♀ Venus"),
            ("mars",    "♂ Mars"),
            ("jupiter", "♃ Jupiter"),
            ("saturn",  "♄ Saturn"),
            ("uranus",  "♅ Uranus"),
            ("neptune", "♆ Neptune"),
            ("pluto",   "♇ Pluto"),
        ]
        sign_planets: dict[int, list[tuple[str, bool]]] = {i: [] for i in range(12)}
        for attr, label in _PLANET_ATTRS:
            p = getattr(subject, attr, None)
            if p is not None:
                idx = _sign_to_idx(getattr(p, "sign", "Aries"))
                retro = bool(getattr(p, "retrograde", False))
                sign_planets[idx].append((label, retro))

        # Rahu (North Node) and Ketu (South Node = opposite)
        rahu_p = getattr(subject, "true_node", None)
        if rahu_p is not None:
            rahu_idx = _sign_to_idx(getattr(rahu_p, "sign", "Aries"))
            ketu_idx = (rahu_idx + 6) % 12
            sign_planets[rahu_idx].append(("☊ Rahu", False))
            sign_planets[ketu_idx].append(("☋ Ketu", False))

        # Ascendant sign index
        asc_house = getattr(subject, "first_house", None)
        asc_idx = _sign_to_idx(getattr(asc_house, "sign", "Aries")) if asc_house else 0

        # South Indian grid: sign index → (row, col)
        # Signs are FIXED; Pisces top-left, going clockwise
        _SIGN_GRID: dict[int, tuple[int, int]] = {
            11: (0, 0),  # Pisces
            0:  (0, 1),  # Aries
            1:  (0, 2),  # Taurus
            2:  (0, 3),  # Gemini
            10: (1, 0),  # Aquarius
            3:  (1, 3),  # Cancer
            9:  (2, 0),  # Capricorn
            4:  (2, 3),  # Leo
            8:  (3, 0),  # Sagittarius
            7:  (3, 1),  # Scorpio
            6:  (3, 2),  # Libra
            5:  (3, 3),  # Virgo
        }
        _CENTER = {(1, 1), (1, 2), (2, 1), (2, 2)}
        _SIGN_SHORT = ["Ar", "Ta", "Ge", "Ca", "Le", "Vi",
                       "Li", "Sc", "Sg", "Cp", "Aq", "Pi"]

        SIZE = 560
        CELL = SIZE // 4          # 140 px per cell
        GRID_Y = 34               # vertical offset for title

        BG      = "#1a1a2e"
        CELL_BG = "#16162a"
        ASC_BG  = "#241540"
        CTR_BG  = "#0f0f1a"
        BORDER  = "#3a3a60"
        C_SIGN  = "#8866cc"
        C_HOUSE = "#6655aa"
        C_PLT   = "#e8e0d0"
        C_OUTER = "#8899bb"   # Uranus / Neptune / Pluto (muted)
        C_NODE  = "#e8b060"   # Rahu / Ketu
        C_ASC   = "#c8a8f8"
        C_TITLE = "#d4bfff"

        _OUTER = {"♅ Uranus", "♆ Neptune", "♇ Pluto"}
        _NODES = {"☊ Rahu", "☋ Ketu"}

        total_h = GRID_Y + SIZE
        parts: list[str] = [
            f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'viewBox="0 0 {SIZE} {total_h}" '
            f'style="font-family:Georgia,serif;background:{BG};">',
            f'<rect width="{SIZE}" height="{total_h}" fill="{BG}"/>',
            f'<text x="{SIZE // 2}" y="22" text-anchor="middle" '
            f'fill="{C_TITLE}" font-size="13" font-style="italic">'
            f'{full_name} — Vedic (South Indian · Lahiri)</text>',
        ]

        for sign_i, (row, col) in _SIGN_GRID.items():
            x = col * CELL
            y = GRID_Y + row * CELL
            is_asc = (sign_i == asc_idx)

            parts.append(
                f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" '
                f'fill="{ASC_BG if is_asc else CELL_BG}" stroke="{BORDER}" stroke-width="1.5"/>'
            )

            # House number (top-left)
            house_num = (sign_i - asc_idx) % 12 + 1
            parts.append(
                f'<text x="{x + 5}" y="{y + 14}" fill="{C_HOUSE}" font-size="11">'
                f'{house_num}</text>'
            )

            # Sign abbreviation (top-right)
            parts.append(
                f'<text x="{x + CELL - 5}" y="{y + 14}" text-anchor="end" '
                f'fill="{C_SIGN}" font-size="11">{_SIGN_SHORT[sign_i]}</text>'
            )

            # "Asc" badge just below the header row
            content_y = y + (30 if not is_asc else 44)
            if is_asc:
                parts.append(
                    f'<text x="{x + CELL // 2}" y="{y + 29}" text-anchor="middle" '
                    f'fill="{C_ASC}" font-size="10" font-weight="bold">Asc</text>'
                )

            for pi, (pname, retro) in enumerate(sign_planets.get(sign_i, [])):
                py = content_y + pi * 15
                if py > y + CELL - 5:
                    break
                label = f"{pname}ᴿ" if retro else pname
                if pname in _NODES:
                    color = C_NODE
                elif pname in _OUTER:
                    color = C_OUTER
                else:
                    color = C_PLT
                parts.append(
                    f'<text x="{x + CELL // 2}" y="{py}" text-anchor="middle" '
                    f'fill="{color}" font-size="12">{label}</text>'
                )

        # Center cells (empty)
        for (row, col) in _CENTER:
            x = col * CELL
            y = GRID_Y + row * CELL
            parts.append(
                f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" '
                f'fill="{CTR_BG}" stroke="{BORDER}" stroke-width="1.5"/>'
            )

        cx, cy = SIZE // 2, GRID_Y + SIZE // 2
        parts.append(
            f'<text x="{cx}" y="{cy - 7}" text-anchor="middle" '
            f'fill="{C_HOUSE}" font-size="10" font-style="italic">South Indian</text>'
        )
        parts.append(
            f'<text x="{cx}" y="{cy + 9}" text-anchor="middle" '
            f'fill="{C_HOUSE}" font-size="10" font-style="italic">Lahiri Ayanamsa</text>'
        )

        parts.append('</svg>')
        return "\n".join(parts)
    except Exception:
        return ""


def generate_kundali_svg(chart_data: dict, full_name: str = "") -> str:
    """Generate a North Indian style Kundali (Lagna) chart SVG.

    Uses sidereal Lahiri positions from chart_data['vedic']['sidereal'].
    House 1 is fixed at top-left of the second cell; signs rotate clockwise
    from the Lagna sign.  Planets are labelled with traditional Sanskrit
    abbreviations (Su Mo Me Ve Ma Ju Sa Rā Ke).
    """
    try:
        vedic = chart_data.get("vedic") or {}
        sidereal = vedic.get("sidereal") or {}

        asc = sidereal.get("ascendant")
        if not asc or asc.get("sidereal_abs") is None:
            return ""

        lagna_idx = int(asc["sidereal_abs"] / 30) % 12  # 0=Aries … 11=Pisces

        # North Indian 4×4 grid: house number → (row, col)
        _POS: dict[int, tuple[int, int]] = {
            12: (0, 0),  1: (0, 1),  2: (0, 2),  3: (0, 3),
            11: (1, 0),                            4: (1, 3),
            10: (2, 0),                            5: (2, 3),
             9: (3, 0),  8: (3, 1),  7: (3, 2),  6: (3, 3),
        }
        _CENTER = {(1, 1), (1, 2), (2, 1), (2, 2)}

        # Full planet names
        _NAMES: dict[str, str] = {
            "sun": "Sun", "moon": "Moon", "mercury": "Mercury", "venus": "Venus",
            "mars": "Mars", "jupiter": "Jupiter", "saturn": "Saturn", "north_node": "Rahu",
        }
        _NODES = {"Rahu", "Ketu"}

        # Group planets by sidereal sign index
        sign_planets: dict[int, list[tuple[str, bool]]] = {i: [] for i in range(12)}
        for body, name in _NAMES.items():
            data = sidereal.get(body)
            if data and data.get("sidereal_abs") is not None:
                sidx = int(data["sidereal_abs"] / 30) % 12
                is_retro = bool((chart_data.get(body) or {}).get("retrograde", False))
                sign_planets[sidx].append((name, is_retro))

        # Ketu is always opposite Rahu
        rahu = sidereal.get("north_node")
        if rahu and rahu.get("sidereal_abs") is not None:
            ketu_idx = (int(rahu["sidereal_abs"] / 30) + 6) % 12
            sign_planets[ketu_idx].append(("Ketu", False))

        _SIGN_SHORT = ["Ar", "Ta", "Ge", "Ca", "Le", "Vi",
                       "Li", "Sc", "Sg", "Cp", "Aq", "Pi"]

        SIZE   = 560
        CELL   = SIZE // 4   # 140 px
        TITLE  = 34
        TOTAL  = TITLE + SIZE

        BG      = "#1a1a2e"
        CELL_BG = "#16162a"
        L1_BG   = "#241540"
        CTR_BG  = "#0f0f1a"
        BORDER  = "#3a3a60"
        C_SIGN  = "#8866cc"
        C_HOUSE = "#6655aa"
        C_PLT   = "#e8e0d0"
        C_RETRO = "#f09060"
        C_NODE  = "#e8b060"
        C_L1    = "#c8a8f8"
        C_TITLE = "#d4bfff"

        parts: list[str] = [
            f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'viewBox="0 0 {SIZE} {TOTAL}" '
            f'style="font-family:Georgia,serif;background:{BG};">',
            f'<rect width="{SIZE}" height="{TOTAL}" fill="{BG}"/>',
            f'<text x="{SIZE // 2}" y="22" text-anchor="middle" '
            f'fill="{C_TITLE}" font-size="13" font-style="italic">'
            f'{full_name} — Kundali (North Indian · Lahiri)</text>',
        ]

        for house_num, (row, col) in _POS.items():
            x = col * CELL
            y = TITLE + row * CELL
            is_lagna = (house_num == 1)

            sign_idx = (lagna_idx + house_num - 1) % 12
            planets = sign_planets[sign_idx]

            parts.append(
                f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" '
                f'fill="{L1_BG if is_lagna else CELL_BG}" '
                f'stroke="{BORDER}" stroke-width="1.5"/>'
            )
            # House number (top-left, small)
            parts.append(
                f'<text x="{x + 5}" y="{y + 14}" '
                f'fill="{C_HOUSE}" font-size="11">{house_num}</text>'
            )
            # Sign abbreviation (top-right)
            parts.append(
                f'<text x="{x + CELL - 5}" y="{y + 14}" text-anchor="end" '
                f'fill="{C_SIGN}" font-size="11">{_SIGN_SHORT[sign_idx]}</text>'
            )
            # Lagna badge
            content_y = y + (44 if is_lagna else 30)
            if is_lagna:
                parts.append(
                    f'<text x="{x + CELL // 2}" y="{y + 29}" '
                    f'text-anchor="middle" fill="{C_L1}" '
                    f'font-size="10" font-weight="bold">Lagna</text>'
                )
            # Planets
            for pi, (name, is_retro) in enumerate(planets[:5]):
                py = content_y + pi * 15
                if py > y + CELL - 5:
                    break
                label = f"{name} (R)" if is_retro else name
                color = C_NODE if name in _NODES else (C_RETRO if is_retro else C_PLT)
                parts.append(
                    f'<text x="{x + CELL // 2}" y="{py}" '
                    f'text-anchor="middle" fill="{color}" font-size="10">{label}</text>'
                )

        # Centre 2×2 area
        for (row, col) in _CENTER:
            x, y = col * CELL, TITLE + row * CELL
            parts.append(
                f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" '
                f'fill="{CTR_BG}" stroke="{BORDER}" stroke-width="1.5"/>'
            )

        # Traditional diagonal cross lines
        x1, y1 = 1 * CELL, TITLE + 1 * CELL
        x2, y2 = 3 * CELL, TITLE + 3 * CELL
        parts.append(
            f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
            f'stroke="{BORDER}" stroke-width="1" stroke-dasharray="4,4"/>'
        )
        parts.append(
            f'<line x1="{x2}" y1="{y1}" x2="{x1}" y2="{y2}" '
            f'stroke="{BORDER}" stroke-width="1" stroke-dasharray="4,4"/>'
        )

        cm, cmy = SIZE // 2, TITLE + SIZE // 2
        lagna_sign = _SIGNS[lagna_idx]
        parts.extend([
            f'<text x="{cm}" y="{cmy - 10}" text-anchor="middle" '
            f'fill="{C_HOUSE}" font-size="10" font-style="italic">North Indian</text>',
            f'<text x="{cm}" y="{cmy + 6}" text-anchor="middle" '
            f'fill="{C_SIGN}" font-size="11">Lagna: {lagna_sign}</text>',
            f'<text x="{cm}" y="{cmy + 20}" text-anchor="middle" '
            f'fill="{C_HOUSE}" font-size="9" font-style="italic">Lahiri Ayanamsa</text>',
            '</svg>',
        ])

        return "\n".join(parts)
    except Exception:
        return ""


# ---------------------------------------------------------------------------
# Vimshottari Dasha
# ---------------------------------------------------------------------------

_DASHA_ORDER = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]
_DASHA_YEARS = {
    "Ketu": 7, "Venus": 20, "Sun": 6, "Moon": 10, "Mars": 7,
    "Rahu": 18, "Jupiter": 16, "Saturn": 19, "Mercury": 17,
}
# 27 nakshatras — lord repeats the 9-planet sequence three times (Ketu first)
_NAK_LORDS = [_DASHA_ORDER[i % 9] for i in range(27)]
_NAK_NAMES = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
    "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
    "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishtha",
    "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati",
]


def compute_vimshottari_dasha(chart_data: dict, birth_datetime: "datetime") -> dict:
    """Compute Vimshottari Dasha / Antardasha periods from the Moon's sidereal nakshatra.

    Returns a dict with:
    - nakshatra: name of birth nakshatra
    - birth_lord: ruling dasha lord at birth
    - mahadashas: list of all 9 mahadasha dicts (lord, years, start, end)
    - current_mahadasha: the active mahadasha dict
    - antardashas: list of 9 antardasha dicts within the current mahadasha
    - current_antardasha: the active antardasha dict
    """
    from datetime import timedelta
    try:
        vedic = chart_data.get("vedic") or {}
        sidereal = vedic.get("sidereal") or {}
        moon = sidereal.get("moon")
        if not moon or moon.get("sidereal_abs") is None:
            return {}

        moon_sid = float(moon["sidereal_abs"])
        nak_size = 360.0 / 27  # 13.3333...°
        nak_idx = int(moon_sid / nak_size) % 27
        fraction_elapsed = (moon_sid % nak_size) / nak_size

        start_lord = _NAK_LORDS[nak_idx]
        start_lord_idx = _DASHA_ORDER.index(start_lord)
        start_years = _DASHA_YEARS[start_lord]

        # The current dasha at birth started fraction_elapsed * start_years years before birth
        dasha_start = birth_datetime - timedelta(days=fraction_elapsed * start_years * 365.25)

        # Build full 120-year mahadasha list
        periods = []
        cur = dasha_start
        for i in range(9):
            lord = _DASHA_ORDER[(start_lord_idx + i) % 9]
            years = _DASHA_YEARS[lord]
            end = cur + timedelta(days=years * 365.25)
            periods.append({
                "lord": lord,
                "years": years,
                "start": cur.date().isoformat(),
                "end": end.date().isoformat(),
            })
            cur = end

        import datetime as _dt
        today_iso = _dt.date.today().isoformat()
        current_maha = next((p for p in periods if p["start"] <= today_iso <= p["end"]), None)

        # Antardashas for current mahadasha
        antardashas: list = []
        current_antar = None
        if current_maha:
            maha_lord = current_maha["lord"]
            maha_idx = _DASHA_ORDER.index(maha_lord)
            maha_years = _DASHA_YEARS[maha_lord]
            from datetime import datetime as _datetime
            ad_cur = _datetime.fromisoformat(current_maha["start"])
            for i in range(9):
                ad_lord = _DASHA_ORDER[(maha_idx + i) % 9]
                ad_years = _DASHA_YEARS[ad_lord]
                ad_days = (ad_years / 120.0) * maha_years * 365.25
                ad_end = ad_cur + timedelta(days=ad_days)
                antardashas.append({
                    "lord": ad_lord,
                    "start": ad_cur.date().isoformat(),
                    "end": ad_end.date().isoformat(),
                })
                ad_cur = ad_end
            current_antar = next(
                (ad for ad in antardashas if ad["start"] <= today_iso <= ad["end"]), None
            )

        return {
            "nakshatra": _NAK_NAMES[nak_idx],
            "birth_lord": start_lord,
            "mahadashas": periods,
            "current_mahadasha": current_maha,
            "antardashas": antardashas,
            "current_antardasha": current_antar,
        }
    except Exception:
        return {}


# ---------------------------------------------------------------------------
# Transit Calendar
# ---------------------------------------------------------------------------

_CAL_ASPECTS = [
    ("Conjunction", 0, 2.5),
    ("Sextile", 60, 2.0),
    ("Square", 90, 2.0),
    ("Trine", 120, 2.0),
    ("Opposition", 180, 2.5),
]
_CAL_PLANET_SWE: dict = {}  # filled lazily below


def _ensure_cal_swe() -> bool:
    global _CAL_PLANET_SWE
    if _CAL_PLANET_SWE:
        return True
    try:
        import swisseph as swe
        _CAL_PLANET_SWE = {
            "Sun": swe.SUN, "Moon": swe.MOON, "Mercury": swe.MERCURY,
            "Venus": swe.VENUS, "Mars": swe.MARS, "Jupiter": swe.JUPITER,
            "Saturn": swe.SATURN,
        }
        return True
    except Exception:
        return False


def compute_transit_calendar(chart_data: dict, from_date: "date", days: int = 35) -> list[dict]:
    """Return upcoming exact transit aspects to natal planets for the next `days` days.

    Each event dict has: date, transit_planet, natal_planet, aspect, orb.
    Finds local-minimum-orb days (the exact aspect date) within each transit window.
    """
    from datetime import timedelta
    if not _ensure_cal_swe():
        return []

    import swisseph as swe

    # Natal tropical positions
    natal: dict[str, float] = {}
    _natal_keys = {
        "Sun": "sun", "Moon": "moon", "Mercury": "mercury", "Venus": "venus",
        "Mars": "mars", "Jupiter": "jupiter", "Saturn": "saturn",
        "Uranus": "uranus", "Neptune": "neptune", "Pluto": "pluto",
    }
    for label, key in _natal_keys.items():
        d = chart_data.get(key)
        if d and d.get("abs_pos") is not None:
            natal[label] = float(d["abs_pos"])
    for angle_key, angle_label in [("ascendant", "ASC"), ("midheaven", "MC")]:
        d = chart_data.get(angle_key)
        if d and d.get("abs_pos") is not None:
            natal[angle_label] = float(d["abs_pos"])

    # Compute daily positions for transit planets (+2 boundary days for min detection)
    scan_dates = [from_date + timedelta(days=i) for i in range(days + 2)]
    daily: dict[str, list] = {p: [] for p in _CAL_PLANET_SWE}
    for d in scan_dates:
        jd = swe.julday(d.year, d.month, d.day, 12.0)
        for planet, sw_id in _CAL_PLANET_SWE.items():
            try:
                res = swe.calc_ut(jd, sw_id, swe.FLG_SWIEPH)
                daily[planet].append(res[0][0])
            except Exception:
                daily[planet].append(None)

    events: list[dict] = []
    for t_planet, positions in daily.items():
        for n_label, n_pos in natal.items():
            if n_label == t_planet:
                continue
            for asp_name, asp_angle, orb_thresh in _CAL_ASPECTS:
                orbs: list = []
                for pos in positions:
                    if pos is None:
                        orbs.append(None)
                        continue
                    diff = (pos - n_pos - asp_angle) % 360
                    if diff > 180:
                        diff -= 360
                    orbs.append(abs(diff))

                # Find local minima within orb — each is an "exact" date
                for i in range(1, len(scan_dates) - 1):
                    if any(orbs[j] is None for j in (i - 1, i, i + 1)):
                        continue
                    if orbs[i] <= orb_thresh and orbs[i] <= orbs[i - 1] and orbs[i] <= orbs[i + 1]:
                        events.append({
                            "date": scan_dates[i].isoformat(),
                            "transit_planet": t_planet,
                            "natal_planet": n_label,
                            "aspect": asp_name,
                            "orb": round(orbs[i], 2),
                        })

    events.sort(key=lambda e: e["date"])
    return events


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
    """Annual profection + monthly sub-profection within the current year."""
    age = current_year - birth_year
    if (current_month, current_day) < (birth_month, birth_day):
        age -= 1
    profected_house = (age % 12) + 1

    house_data = (chart.get("houses") or {}).get(str(profected_house)) or {}
    house_sign = house_data.get("sign")
    lord = _SIGN_RULER.get(house_sign) if house_sign else None
    lord_data = chart.get(lord) if lord else None

    # Monthly profection: each month within the profection year activates the next house
    if (current_year, current_month, current_day) >= (
            (current_year if (current_month, current_day) >= (birth_month, birth_day) else current_year - 1),
            birth_month, birth_day):
        last_bday_year = (current_year if (current_month, current_day) >= (birth_month, birth_day)
                          else current_year - 1)
    else:
        last_bday_year = current_year - 1
    months_elapsed = (current_year - last_bday_year) * 12 + (current_month - birth_month)
    if current_day < birth_day:
        months_elapsed -= 1
    months_elapsed = max(0, months_elapsed)

    monthly_house = ((profected_house - 1 + months_elapsed) % 12) + 1
    monthly_house_data = (chart.get("houses") or {}).get(str(monthly_house)) or {}
    monthly_sign = monthly_house_data.get("sign")
    monthly_lord = _SIGN_RULER.get(monthly_sign) if monthly_sign else None
    monthly_lord_data = chart.get(monthly_lord) if monthly_lord else None

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
        "monthly_house": monthly_house,
        "monthly_house_sign": monthly_sign,
        "monthly_lord": monthly_lord,
        "monthly_lord_sign": monthly_lord_data.get("sign") if monthly_lord_data else None,
        "monthly_lord_house": monthly_lord_data.get("house") if monthly_lord_data else None,
        "months_elapsed": months_elapsed,
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
    try:
        subject = AstrologicalSubject(
            name="Transit",
            year=year, month=month, day=day, hour=hour, minute=minute,
            city=city, nation=nation, tz_str=tz_str, online=True,
        )
    except Exception:
        coords = _geocode_with_fallback(city, nation)
        if coords is None:
            raise
        subject = AstrologicalSubject(
            name="Transit",
            year=year, month=month, day=day, hour=hour, minute=minute,
            lat=coords[0], lng=coords[1], tz_str=tz_str, online=False,
        )
    # Cache geocoded current-location coords so SVG generation can reuse them
    try:
        natal_chart["_current_lat"] = float(getattr(subject, "lat", None) or 0)
        natal_chart["_current_lng"] = float(getattr(subject, "lng", None) or 0)
    except (TypeError, ValueError):
        pass

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


_SYNASTRY_ORB = 6.0  # tighter than natal for inter-chart aspects

# Priority order for sorting synastry aspects by significance
_SYNASTRY_PRIORITY = {
    "sun": 0, "moon": 1, "ascendant": 2, "venus": 3, "mars": 4,
    "midheaven": 5, "mercury": 6, "jupiter": 7, "saturn": 8,
    "uranus": 9, "neptune": 10, "pluto": 11, "chiron": 12,
    "north_node": 13,
}


def compute_synastry(chart_a: dict, chart_b: dict) -> dict:
    """
    Compare two natal charts for synastry analysis.
    Returns cross-aspects, house overlays (both directions), and composite midpoint chart.
    """
    # Collect body positions for both charts
    def _bodies(chart: dict) -> dict[str, tuple[float, bool]]:
        out: dict[str, tuple[float, bool]] = {}
        for planet in _PLANETS:
            d = chart.get(planet)
            if d and d.get("abs_pos") is not None:
                out[planet] = (d["abs_pos"], d.get("retrograde", False))
        for key in ("ascendant", "midheaven"):
            d = chart.get(key)
            if d and d.get("abs_pos") is not None:
                out[key] = (d["abs_pos"], False)
        chiron = chart.get("chiron")
        if chiron and chiron.get("abs_pos") is not None:
            out["chiron"] = (chiron["abs_pos"], chiron.get("retrograde", False))
        nn = chart.get("north_node")
        if nn and nn.get("abs_pos") is not None:
            out["north_node"] = (nn["abs_pos"], False)
        return out

    bodies_a = _bodies(chart_a)
    bodies_b = _bodies(chart_b)

    # ── Cross-aspects (A ↔ B) ─────────────────────────────────────────────
    cross_aspects: list[dict] = []
    for p_a, (pos_a, retro_a) in bodies_a.items():
        for p_b, (pos_b, retro_b) in bodies_b.items():
            result = _find_aspect(pos_a, pos_b, max_orb=_SYNASTRY_ORB)
            if not result:
                continue
            aspect_name, orb = result
            exact_angle = next(a for nm, a, _ in _MAJOR_ASPECTS if nm == aspect_name)
            applying = _is_applying(p_a, pos_a, retro_a, p_b, pos_b, retro_b, exact_angle)
            cross_aspects.append({
                "planet_a": p_a, "planet_b": p_b,
                "aspect": aspect_name, "orb": orb, "applying": applying,
            })

    cross_aspects.sort(key=lambda x: (
        min(_SYNASTRY_PRIORITY.get(x["planet_a"], 14), _SYNASTRY_PRIORITY.get(x["planet_b"], 14)),
        x["orb"],
    ))

    # ── House overlays — B's planets in A's whole-sign houses ────────────
    def _overlays(chart_host: dict, bodies_guest: dict[str, tuple[float, bool]]) -> list[dict]:
        asc = chart_host.get("ascendant")
        if not asc or asc.get("abs_pos") is None:
            return []
        host_lagna_idx = int(asc["abs_pos"] / 30) % 12
        overlays = []
        for planet, (pos, _) in bodies_guest.items():
            sign_idx = int(pos / 30) % 12
            house_num = ((sign_idx - host_lagna_idx) % 12) + 1
            overlays.append({
                "planet": planet,
                "sign": _SIGNS[sign_idx],
                "house_in_partner": house_num,
            })
        overlays.sort(key=lambda x: _SYNASTRY_PRIORITY.get(x["planet"], 14))
        return overlays

    house_overlays_b_in_a = _overlays(chart_a, bodies_b)
    house_overlays_a_in_b = _overlays(chart_b, bodies_a)

    # ── Composite chart (midpoint method) ────────────────────────────────
    def _midpoint(pos_a: float, pos_b: float) -> float:
        diff = (pos_b - pos_a) % 360
        if diff > 180:
            return (pos_a + (360 - diff) / 2) % 360
        return (pos_a + diff / 2) % 360

    composite: dict = {}
    for body in list(_PLANETS) + ["ascendant", "midheaven", "chiron", "north_node"]:
        a_data = chart_a.get(body)
        b_data = chart_b.get(body)
        if not a_data or not b_data:
            continue
        if a_data.get("abs_pos") is None or b_data.get("abs_pos") is None:
            continue
        mid = _midpoint(a_data["abs_pos"], b_data["abs_pos"])
        sign, pos = _sign_from_abs_pos(mid)
        entry: dict = {"abs_pos": round(mid, 2), "sign": sign, "position": round(pos, 2)}
        dignity = _get_dignity(body, sign)
        if dignity:
            entry["dignity"] = dignity
        composite[body] = entry

    # Composite aspects (internal aspects within the composite chart)
    composite_aspects: list[dict] = []
    comp_bodies = {k: (v["abs_pos"], False) for k, v in composite.items() if v.get("abs_pos") is not None}
    comp_list = list(comp_bodies.items())
    for i, (p1, (pos1, _)) in enumerate(comp_list):
        for p2, (pos2, _) in comp_list[i + 1:]:
            result = _find_aspect(pos1, pos2)
            if result:
                aspect_name, orb = result
                composite_aspects.append({"planet1": p1, "planet2": p2, "aspect": aspect_name, "orb": orb})
    composite_aspects.sort(key=lambda x: (
        min(_SYNASTRY_PRIORITY.get(x["planet1"], 14), _SYNASTRY_PRIORITY.get(x["planet2"], 14)),
        x["orb"],
    ))

    return {
        "cross_aspects": cross_aspects,
        "house_overlays_b_in_a": house_overlays_b_in_a,
        "house_overlays_a_in_b": house_overlays_a_in_b,
        "composite": composite,
        "composite_aspects": composite_aspects,
    }


def compute_arabic_parts(chart: dict) -> dict:
    """
    Compute classical Arabic Parts (Lots) beyond Fortune.
    - Part of Spirit (Daimon): intentional self, life purpose
    - Part of Eros: desire, attraction, what we find beautiful
    - Part of Marriage: relationship timing and type
    All use the same sectarian logic as Part of Fortune.
    """
    asc = chart.get("ascendant")
    sun = chart.get("sun")
    moon = chart.get("moon")
    venus = chart.get("venus")

    if not asc or not sun or not moon:
        return {}
    asc_abs = asc.get("abs_pos")
    sun_abs = sun.get("abs_pos")
    moon_abs = moon.get("abs_pos")
    if asc_abs is None or sun_abs is None or moon_abs is None:
        return {}

    raw_house = sun.get("house")
    sun_house_num = raw_house if isinstance(raw_house, int) else _HOUSE_NUMBER.get(str(raw_house), 0)
    is_day = sun_house_num >= 7

    result: dict = {}

    # Part of Spirit (Daimon) — inverse sect formula of Fortune; represents intentional soul direction
    spirit_abs = (asc_abs + sun_abs - moon_abs) % 360 if is_day else (asc_abs + moon_abs - sun_abs) % 360
    s_sign, s_pos = _sign_from_abs_pos(spirit_abs)
    spirit: dict = {"abs_pos": round(spirit_abs, 2), "sign": s_sign, "position": round(s_pos, 2), "chart_type": "day" if is_day else "night"}
    d = _get_dignity("sun", s_sign)
    if d:
        spirit["dignity"] = d
    result["spirit"] = spirit

    if venus and venus.get("abs_pos") is not None:
        venus_abs = venus["abs_pos"]

        # Part of Eros — desire, attraction, aesthetic longing; ASC + Venus - Sun
        eros_abs = (asc_abs + venus_abs - sun_abs) % 360
        e_sign, e_pos = _sign_from_abs_pos(eros_abs)
        eros: dict = {"abs_pos": round(eros_abs, 2), "sign": e_sign, "position": round(e_pos, 2)}
        d = _get_dignity("venus", e_sign)
        if d:
            eros["dignity"] = d
        result["eros"] = eros

        # Part of Marriage — relationship; ASC + Descendant - Venus (Descendant = ASC + 180)
        desc_abs = (asc_abs + 180) % 360
        marriage_abs = (asc_abs + desc_abs - venus_abs) % 360
        m_sign, m_pos = _sign_from_abs_pos(marriage_abs)
        marriage: dict = {"abs_pos": round(marriage_abs, 2), "sign": m_sign, "position": round(m_pos, 2)}
        d = _get_dignity("venus", m_sign)
        if d:
            marriage["dignity"] = d
        result["marriage"] = marriage

    return result


def compute_antiscia(chart: dict, orb: float = 1.5) -> list[dict]:
    """
    Detect antiscia (mirror across Cancer-Capricorn solstice axis) and
    contra-antiscia (mirror across Aries-Libra equinox axis) between natal bodies.

    Antiscia: pos1 + pos2 ≈ 180° — planets "equidistant from the solstice"
    Contra-antiscia: pos1 + pos2 ≈ 0°/360° — equidistant from the equinox
    """
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

    connections: list[dict] = []
    body_list = list(bodies.items())

    for i, (p1, pos1) in enumerate(body_list):
        for p2, pos2 in body_list[i + 1:]:
            total = (pos1 + pos2) % 360

            # Antiscia: sum ≈ 180°
            anti_diff = abs(total - 180)
            anti_diff = min(anti_diff, 360 - anti_diff)
            if anti_diff <= orb:
                connections.append({
                    "planet1": p1, "planet2": p2,
                    "type": "antiscia", "orb": round(anti_diff, 2),
                    "axis": "Cancer-Capricorn (solstice)",
                })

            # Contra-antiscia: sum ≈ 0°/360°
            contra_diff = min(total, 360 - total)
            if contra_diff <= orb:
                connections.append({
                    "planet1": p1, "planet2": p2,
                    "type": "contra-antiscia", "orb": round(contra_diff, 2),
                    "axis": "Aries-Libra (equinox)",
                })

    connections.sort(key=lambda x: x["orb"])
    return connections


def compute_almuten_figuris(chart: dict) -> Optional[dict]:
    """Find the Almuten Figuris: the planet with the highest cumulative dignity score
    at the chart's five key positions (Sun, Moon, ASC, Part of Fortune, Part of Spirit).

    Scoring per position: domicile=5, exaltation=4, triplicity=3, term(bound)=2, face=1.
    Detriment=-5, fall=-4 are applied as penalties. The winning planet is the
    traditional 'master of the chart', often different from the chart ruler.
    """
    _SCORED_PLANETS = ["sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn"]

    # Positions to evaluate (sign, position-within-sign, abs_pos)
    positions: list[tuple[str, str, float, float]] = []  # (label, sign, pos_in_sign, abs)

    sun = chart.get("sun")
    if sun and sun.get("sign") and sun.get("position") is not None and sun.get("abs_pos") is not None:
        positions.append(("sun", sun["sign"], float(sun["position"]), float(sun["abs_pos"])))

    moon = chart.get("moon")
    if moon and moon.get("sign") and moon.get("position") is not None and moon.get("abs_pos") is not None:
        positions.append(("moon", moon["sign"], float(moon["position"]), float(moon["abs_pos"])))

    asc = chart.get("ascendant")
    if asc and asc.get("sign") and asc.get("position") is not None and asc.get("abs_pos") is not None:
        positions.append(("ascendant", asc["sign"], float(asc["position"]), float(asc["abs_pos"])))

    pof = chart.get("part_of_fortune")
    if pof and pof.get("abs_pos") is not None:
        sign, pos = _sign_from_abs_pos(float(pof["abs_pos"]))
        positions.append(("part_of_fortune", sign, pos, float(pof["abs_pos"])))

    spirit = (chart.get("arabic_parts") or {}).get("spirit")
    if spirit and spirit.get("abs_pos") is not None:
        sign, pos = _sign_from_abs_pos(float(spirit["abs_pos"]))
        positions.append(("part_of_spirit", sign, pos, float(spirit["abs_pos"])))

    if not positions:
        return None

    is_day = (chart.get("sect") or {}).get("chart_type", "").lower() == "day"

    scores: dict[str, int] = {p: 0 for p in _SCORED_PLANETS}
    breakdown: dict[str, list[str]] = {p: [] for p in _SCORED_PLANETS}

    for label, sign, pos_in_sign, _abs in positions:
        element = _SIGN_ELEMENT.get(sign)
        for planet in _SCORED_PLANETS:
            dig = _DIGNITIES.get(planet) or {}

            # Domicile / detriment
            if sign in dig.get("domicile", []):
                scores[planet] += 5
                breakdown[planet].append(f"domicile@{label}")
            elif sign in dig.get("detriment", []):
                scores[planet] -= 5

            # Exaltation / fall
            if sign in dig.get("exaltation", []):
                scores[planet] += 4
                breakdown[planet].append(f"exaltation@{label}")
            elif sign in dig.get("fall", []):
                scores[planet] -= 4

            # Triplicity (day lord = 3, night lord = 3, cooperating = 1)
            if element:
                trip = _TRIPLICITY_RULERS.get(element, {})
                if is_day and trip.get("day") == planet:
                    scores[planet] += 3
                    breakdown[planet].append(f"triplicity(day)@{label}")
                elif not is_day and trip.get("night") == planet:
                    scores[planet] += 3
                    breakdown[planet].append(f"triplicity(night)@{label}")
                if trip.get("cooperating") == planet:
                    scores[planet] += 1
                    breakdown[planet].append(f"triplicity(coop)@{label}")

            # Egyptian term (bound) — 2 points
            for start, end, term_planet in _EGYPTIAN_TERMS.get(sign, []):
                if start <= pos_in_sign < end and term_planet == planet:
                    scores[planet] += 2
                    breakdown[planet].append(f"term@{label}")
                    break

            # Face (decan) — 1 point
            face_idx = int(pos_in_sign // 10)
            faces = _FACES.get(sign, [])
            if face_idx < len(faces) and faces[face_idx] == planet:
                scores[planet] += 1
                breakdown[planet].append(f"face@{label}")

    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    winner_name, winner_score = sorted_scores[0]
    runner_up = sorted_scores[1] if len(sorted_scores) > 1 else None

    # Enrich with the winner's natal placement
    winner_data = chart.get(winner_name) or {}

    return {
        "planet": winner_name,
        "score": winner_score,
        "sign": winner_data.get("sign"),
        "position": winner_data.get("position"),
        "house": winner_data.get("house"),
        "retrograde": winner_data.get("retrograde", False),
        "dignity": winner_data.get("dignity"),
        "runner_up": runner_up[0] if runner_up else None,
        "runner_up_score": runner_up[1] if runner_up else None,
        "all_scores": scores,
        "breakdown": breakdown[winner_name],
    }


def compute_dispositor_tree(chart: dict) -> dict:
    """Trace sign-rulership chains to find the final dispositor.

    Each planet is 'disposed by' the ruler of its sign. Following the chain leads to:
    - A final dispositor: a planet in its own sign (pinnacle of chart authority)
    - A mutual reception: two planets each in the other's sign (co-rulership cycle)
    - A longer cycle: 3+ planets in a circular chain
    When one planet is the sole final dispositor, it has authority over all others.
    """
    planet_sign: dict[str, str] = {}
    for p in _PLANETS:
        d = chart.get(p)
        if d and d.get("sign"):
            planet_sign[p] = d["sign"]

    if not planet_sign:
        return {}

    # Trace chain from each planet
    chains: dict[str, list[str]] = {}
    for start in planet_sign:
        chain = [start]
        current = start
        visited: set[str] = {start}
        while True:
            sign = planet_sign.get(current)
            if not sign:
                break
            dispositor = _SIGN_RULER.get(sign)
            if not dispositor or dispositor not in planet_sign:
                break
            if dispositor == current:      # in own sign — final dispositor
                break
            if dispositor in visited:      # cycle
                chain.append(f"↺{dispositor}")
                break
            chain.append(dispositor)
            visited.add(dispositor)
            current = dispositor
        chains[start] = chain

    # Final dispositors: planets in their own sign
    final_dispositors = [
        p for p in planet_sign
        if _SIGN_RULER.get(planet_sign[p]) == p
    ]

    # Check for mutual receptions (pairs each in the other's sign)
    mutual_reception_pairs: list[tuple[str, str]] = []
    checked: set[frozenset] = set()
    for p in planet_sign:
        dispositor = _SIGN_RULER.get(planet_sign[p])
        if dispositor and dispositor in planet_sign and dispositor != p:
            if _SIGN_RULER.get(planet_sign[dispositor]) == p:
                pair = frozenset({p, dispositor})
                if pair not in checked:
                    mutual_reception_pairs.append((p, dispositor))
                    checked.add(pair)

    return {
        "chains": chains,
        "final_dispositors": final_dispositors,
        "single_final_dispositor": final_dispositors[0] if len(final_dispositors) == 1 else None,
        "mutual_reception_cycles": [list(pair) for pair in
                                    [frozenset(p) for p in mutual_reception_pairs]],
        "has_single_ruler": len(final_dispositors) == 1,
    }


_geocode_cache: dict[str, tuple[float, float]] = {}


def _geocode_with_fallback(city: str, nation: str) -> tuple[float, float] | None:
    """Geocode a city using Nominatim (OpenStreetMap). No API key required."""
    key = f"{city.lower().strip()},{nation.lower().strip()}"
    if key in _geocode_cache:
        return _geocode_cache[key]
    try:
        import requests as _req
        resp = _req.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": f"{city}, {nation}", "format": "json", "limit": 1},
            headers={"User-Agent": "PersonalAstrologerAgent/1.0"},
            timeout=10,
        )
        data = resp.json()
        if data:
            coords: tuple[float, float] = (float(data[0]["lat"]), float(data[0]["lon"]))
            _geocode_cache[key] = coords
            return coords
    except Exception:
        pass
    return None


def compute_chart(
    full_name: str,
    birth_year: int, birth_month: int, birth_day: int,
    birth_hour: int, birth_minute: int,
    city: str, nation: str, tz_str: str,
    house_system: str = "Placidus",
) -> dict:
    hs_code = _HOUSE_SYSTEM_CODES.get(house_system, "P")
    # Try kerykeion's GeoNames lookup first (uses SQLite cache); fall back to Nominatim
    try:
        subject = AstrologicalSubject(
            name=full_name,
            year=birth_year, month=birth_month, day=birth_day,
            hour=birth_hour, minute=birth_minute,
            city=city, nation=nation, tz_str=tz_str, online=True,
            houses_system_identifier=hs_code,
        )
    except Exception:
        coords = _geocode_with_fallback(city, nation)
        if coords is None:
            raise
        subject = AstrologicalSubject(
            name=full_name,
            year=birth_year, month=birth_month, day=birth_day,
            hour=birth_hour, minute=birth_minute,
            lat=coords[0], lng=coords[1], tz_str=tz_str, online=False,
            houses_system_identifier=hs_code,
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

    # Major asteroids: Ceres, Pallas, Juno, Vesta via swisseph (needs chart["houses"])
    try:
        import os, swisseph as _swe, kerykeion as _kery, pytz as _pytz
        from datetime import datetime as _dt
        _swe.set_ephe_path(os.path.join(os.path.dirname(_kery.__file__), "sweph"))
        _tz = _pytz.timezone(tz_str or "UTC")
        _local = _tz.localize(_dt(birth_year, birth_month, birth_day, birth_hour, birth_minute))
        _utc = _local.astimezone(_pytz.UTC)
        _jd = _swe.julday(_utc.year, _utc.month, _utc.day,
                          _utc.hour + _utc.minute / 60.0 + _utc.second / 3600.0)
        for _ast_name, _ast_id in _ASTEROID_IDS.items():
            chart[_ast_name] = _compute_asteroid_pos(_jd, _ast_id, chart["houses"])
    except Exception:
        for _ast_name in _ASTEROID_IDS:
            chart[_ast_name] = None

    # Natal lunar phase, Part of Fortune, stelliums, mutual receptions
    chart["lunar_phase"] = compute_lunar_phase(chart)
    chart["part_of_fortune"] = compute_part_of_fortune(chart)
    chart["stelliums"] = compute_stelliums(chart)
    chart["mutual_receptions"] = compute_mutual_receptions(chart)

    # Anaretic degrees, planetary sect, fixed star conjunctions
    chart["anaretic_degrees"] = compute_anaretic_degrees(chart)
    chart["sect"] = compute_sect(chart)
    chart["fixed_stars"] = compute_fixed_star_conjunctions(chart)

    # Additional classical lots and antiscia
    chart["arabic_parts"] = compute_arabic_parts(chart)
    chart["antiscia"] = compute_antiscia(chart)

    # Store natal metadata needed for primary directions and parans
    try:
        chart["_natal_armc"] = float(getattr(subject, "armc", None) or 0)
        chart["_natal_lat"] = float(getattr(subject, "lat", None) or 0)
        chart["_natal_lng"] = float(getattr(subject, "lng", None) or 0)
    except (TypeError, ValueError):
        chart["_natal_armc"] = None
        chart["_natal_lat"] = None
        chart["_natal_lng"] = None

    # Minor aspects (natal)
    try:
        chart["minor_aspects"] = compute_minor_aspects(chart)
    except Exception:
        chart["minor_aspects"] = []

    # Parans
    try:
        chart["parans"] = compute_parans(
            natal_chart=chart,
            birth_year=birth_year, birth_month=birth_month, birth_day=birth_day,
            birth_hour=birth_hour, birth_minute=birth_minute,
            tz_str=tz_str,
        )
    except Exception:
        chart["parans"] = []

    # Declinations and parallel/contra-parallel aspects
    try:
        decl_data = compute_declinations(
            birth_year, birth_month, birth_day, birth_hour, birth_minute, tz_str
        )
        chart["declinations"] = _add_angle_declinations(chart, decl_data)
        chart["parallel_aspects"] = compute_parallel_aspects(chart, decl_data)
    except Exception:
        chart["declinations"] = {}
        chart["parallel_aspects"] = []

    # Prenatal lunation (syzygy) degree
    try:
        chart["prenatal_syzygy"] = compute_prenatal_syzygy(
            birth_year, birth_month, birth_day, birth_hour, birth_minute, tz_str
        )
    except Exception:
        chart["prenatal_syzygy"] = {}

    # Almuten Figuris and dispositor tree (computed last; need full chart)
    try:
        chart["almuten_figuris"] = compute_almuten_figuris(chart)
    except Exception:
        chart["almuten_figuris"] = None
    try:
        chart["dispositor_tree"] = compute_dispositor_tree(chart)
    except Exception:
        chart["dispositor_tree"] = None

    return chart


_TRANSIT_PLANET_NAMES = {
    "jupiter": "Jupiter", "saturn": "Saturn",
    "uranus": "Uranus", "neptune": "Neptune", "pluto": "Pluto",
}

_NATAL_POINT_THEMES = {
    "sun": "identity & purpose",
    "moon": "emotions & home",
    "mercury": "communication & thinking",
    "venus": "relationships & values",
    "mars": "drive & action",
    "jupiter": "growth & expansion",
    "saturn": "structure & discipline",
    "uranus": "change & disruption",
    "neptune": "dreams & illusions",
    "pluto": "transformation",
    "ascendant": "self-presentation",
    "midheaven": "career & reputation",
    "north_node": "life direction",
    "chiron": "healing & wounds",
}

_ASPECT_TONE = {
    "Conjunction": "fusion of energies",
    "Sextile": "gentle opportunity",
    "Square": "friction and pressure",
    "Trine": "ease and flow",
    "Opposition": "tension and awareness",
}


def compute_daily_sky(
    natal_chart: dict,
    current_year: int,
    current_month: int,
    current_day: int,
    current_hour: int = 12,
    current_minute: int = 0,
) -> dict:
    """Return today's personalised sky snapshot: Moon, retrograde planets, closest active transit."""
    lat = natal_chart.get("_natal_lat") or 0.0
    lng = natal_chart.get("_natal_lng") or 0.0

    try:
        sky = AstrologicalSubject(
            name="Today",
            year=current_year, month=current_month, day=current_day,
            hour=current_hour, minute=current_minute,
            lat=lat, lng=lng, tz_str="UTC", online=False,
        )
    except Exception:
        return {}

    result: dict = {}

    # Moon sign, degree, void-of-course
    moon_data = _safe_planet(sky, "moon")
    if moon_data:
        result["moon_sign"] = moon_data["sign"]
        result["moon_degree"] = round(moon_data["position"], 1)
        moon_abs = moon_data.get("abs_pos", 0.0)
        sign_end_abs = (int(moon_abs / 30) + 1) * 30.0
        degrees_remaining = sign_end_abs - moon_abs
        voc = True
        for p_name in ["sun", "mercury", "venus", "mars", "jupiter", "saturn"]:
            if not voc:
                break
            pd = _safe_planet(sky, p_name)
            if not pd:
                continue
            p_abs = pd.get("abs_pos", 0.0)
            for _, angle, max_orb in _MAJOR_ASPECTS:
                for sign_dir in (1, -1):
                    target = (p_abs + sign_dir * angle) % 360
                    diff_forward = (target - moon_abs + 360) % 360
                    if diff_forward <= degrees_remaining + max_orb:
                        voc = False
                        break
                if not voc:
                    break
        result["moon_voc"] = voc
    else:
        result["moon_sign"] = None
        result["moon_voc"] = False

    # Retrograde planets
    retro = []
    for p_name in _PLANETS[2:]:  # skip sun, moon
        pd = _safe_planet(sky, p_name)
        if pd and pd.get("retrograde"):
            retro.append({"planet": p_name, "sign": pd["sign"]})
    result["retrograde_planets"] = retro

    # Closest applying outer-planet transit to any natal point
    outer = ["jupiter", "saturn", "uranus", "neptune", "pluto"]
    natal_points = list(_PLANETS) + ["ascendant", "midheaven", "north_node", "chiron"]
    best = None
    best_orb = 999.0

    for t_name in outer:
        td = _safe_planet(sky, t_name)
        if not td:
            continue
        t_abs = td.get("abs_pos", 0.0)
        for n_name in natal_points:
            nd = natal_chart.get(n_name)
            if not nd or not isinstance(nd, dict):
                continue
            n_abs = nd.get("abs_pos")
            if n_abs is None:
                continue
            for asp_name, angle, max_orb in _MAJOR_ASPECTS:
                diff = abs((t_abs - n_abs + 180) % 360 - 180)
                orb = abs(diff - angle)
                if orb <= max_orb and orb < best_orb:
                    best_orb = orb
                    theme = _NATAL_POINT_THEMES.get(n_name, n_name)
                    tone = _ASPECT_TONE.get(asp_name, asp_name.lower())
                    retro_mark = " Rx" if td.get("retrograde") else ""
                    best = {
                        "transit_planet": t_name,
                        "transit_sign": td["sign"],
                        "transit_retrograde": td.get("retrograde", False),
                        "aspect": asp_name,
                        "natal_point": n_name,
                        "natal_sign": nd.get("sign"),
                        "orb": round(orb, 2),
                        "summary": (
                            f"{_TRANSIT_PLANET_NAMES[t_name]}{retro_mark} {asp_name.lower()} "
                            f"your {n_name.replace('_', ' ').title()} "
                            f"({round(orb, 1)}° orb) — {tone} around {theme}"
                        ),
                    }

    result["closest_transit"] = best
    return result
