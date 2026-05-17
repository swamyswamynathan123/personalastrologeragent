import pytest
from llm.report import _compute_convergences, _compute_synastry_convergences


_BASE_STATE = {
    "full_name": "Jane Doe",
    "parsed_dob": "1990-05-15",
    "birth_location": "Mumbai, Maharashtra, India",
    "birth_time": "14:30",
    "birth_time_timezone": "Asia/Kolkata",
    "current_location": "New York, NY, USA",
    "parsed_current_datetime": "2026-05-15T12:00:00+00:00",
}


def _chart(
    profection_lord=None, firdaria_major=None, maha_lord=None,
    transits=None, upcoming=None, solar_arc_aspects=None, progressed_aspects=None,
):
    c = {
        "transits": transits or [],
        "upcoming_transits": upcoming or [],
        "solar_arc_aspects": solar_arc_aspects or [],
        "progressed_aspects": progressed_aspects or [],
    }
    if profection_lord:
        c["profection"] = {
            "lord_of_year": profection_lord, "age": 30, "profected_house": 1,
            "lord_position": "10", "lord_sign": "Capricorn",
        }
    if firdaria_major:
        c["firdaria"] = {
            "major_lord": firdaria_major, "major_period_end": "2030-01-01",
            "years_remaining_major": 4, "major_period_years": 10,
        }
    if maha_lord:
        c["vedic"] = {
            "dasha": {
                "mahadasha_lord": maha_lord, "mahadasha_end": "2030-01-01",
                "years_remaining_mahadasha": 4, "mahadasha_years": 19,
            }
        }
    return c


# --- Triple / dual convergence ---

def test_triple_convergence_detected():
    results = _compute_convergences(_chart("saturn", "saturn", "saturn"), _BASE_STATE)
    assert any("TRIPLE CONVERGENCE" in r for r in results)


def test_triple_convergence_not_false_positive():
    results = _compute_convergences(_chart("saturn", "jupiter", "mars"), _BASE_STATE)
    assert not any("TRIPLE CONVERGENCE" in r for r in results)


def test_cross_tradition_convergence_fird_maha():
    results = _compute_convergences(_chart("mars", "jupiter", "jupiter"), _BASE_STATE)
    assert any("CROSS-TRADITION" in r for r in results)


def test_annual_amplification_prof_fird():
    results = _compute_convergences(_chart("venus", "venus", "saturn"), _BASE_STATE)
    assert any("ANNUAL AMPLIFICATION" in r for r in results)


def test_vedic_western_annual_sync_prof_maha():
    results = _compute_convergences(_chart("mars", "venus", "mars"), _BASE_STATE)
    assert any("VEDIC-WESTERN ANNUAL SYNC" in r for r in results)


# --- Year lord transit ---

def test_year_lord_under_outer_planet_transit():
    c = _chart("saturn")
    c["transits"] = [{"natal_planet": "saturn", "transiting_planet": "pluto",
                      "aspect": "conjunction", "orb": "1.2", "applying": True}]
    results = _compute_convergences(c, _BASE_STATE)
    assert any("YEAR LORD UNDER TRANSIT" in r for r in results)


def test_year_lord_transit_inner_planet_ignored():
    c = _chart("saturn")
    c["transits"] = [{"natal_planet": "saturn", "transiting_planet": "venus",
                      "aspect": "trine", "orb": "1.0", "applying": True}]
    results = _compute_convergences(c, _BASE_STATE)
    assert not any("YEAR LORD UNDER TRANSIT" in r for r in results)


def test_no_profection_no_year_lord_transit():
    c = _chart()
    c["transits"] = [{"natal_planet": "saturn", "transiting_planet": "pluto",
                      "aspect": "conjunction", "orb": "1.0"}]
    results = _compute_convergences(c, _BASE_STATE)
    assert not any("YEAR LORD" in r for r in results)


# --- Solar arc to angles ---

def test_solar_arc_applying_to_midheaven():
    c = _chart()
    c["solar_arc_aspects"] = [{"directed_planet": "arc_sun", "natal_planet": "midheaven",
                                "aspect": "conjunction", "orb": "0.3", "applying": True}]
    results = _compute_convergences(c, _BASE_STATE)
    assert any("SOLAR ARC TO ANGLE" in r for r in results)


def test_solar_arc_applying_to_ascendant():
    c = _chart()
    c["solar_arc_aspects"] = [{"directed_planet": "arc_saturn", "natal_planet": "ascendant",
                                "aspect": "square", "orb": "0.8", "applying": True}]
    results = _compute_convergences(c, _BASE_STATE)
    assert any("SOLAR ARC TO ANGLE" in r for r in results)


def test_solar_arc_separating_not_flagged():
    c = _chart()
    c["solar_arc_aspects"] = [{"directed_planet": "arc_sun", "natal_planet": "ascendant",
                                "aspect": "conjunction", "orb": "0.3", "applying": False}]
    results = _compute_convergences(c, _BASE_STATE)
    assert not any("SOLAR ARC TO ANGLE" in r for r in results)


def test_solar_arc_to_non_angle_not_flagged():
    c = _chart()
    c["solar_arc_aspects"] = [{"directed_planet": "arc_sun", "natal_planet": "saturn",
                                "aspect": "conjunction", "orb": "0.3", "applying": True}]
    results = _compute_convergences(c, _BASE_STATE)
    assert not any("SOLAR ARC TO ANGLE" in r for r in results)


# --- Exact progressed aspects ---

def test_exact_progressed_aspect_within_half_degree():
    c = _chart()
    c["progressed_aspects"] = [{"progressed_planet": "moon", "natal_planet": "sun",
                                 "aspect": "conjunction", "orb": "0.2", "applying": True}]
    results = _compute_convergences(c, _BASE_STATE)
    assert any("EXACT PROGRESSED ASPECT" in r for r in results)


def test_progressed_aspect_over_half_degree_not_flagged():
    c = _chart()
    c["progressed_aspects"] = [{"progressed_planet": "moon", "natal_planet": "sun",
                                 "aspect": "conjunction", "orb": "0.8", "applying": True}]
    results = _compute_convergences(c, _BASE_STATE)
    assert not any("EXACT PROGRESSED ASPECT" in r for r in results)


def test_exact_progressed_separating_not_flagged():
    c = _chart()
    c["progressed_aspects"] = [{"progressed_planet": "moon", "natal_planet": "sun",
                                 "aspect": "conjunction", "orb": "0.1", "applying": False}]
    results = _compute_convergences(c, _BASE_STATE)
    assert not any("EXACT PROGRESSED ASPECT" in r for r in results)


# --- Multi-outer pressure ---

def test_multi_outer_pressure_two_planets():
    c = _chart()
    c["transits"] = [
        {"natal_planet": "sun", "transiting_planet": "pluto", "aspect": "square", "orb": "1.5"},
        {"natal_planet": "sun", "transiting_planet": "saturn", "aspect": "opposition", "orb": "2.0"},
    ]
    results = _compute_convergences(c, _BASE_STATE)
    assert any("MULTI-OUTER PRESSURE" in r for r in results)


def test_single_outer_planet_not_flagged():
    c = _chart()
    c["transits"] = [{"natal_planet": "sun", "transiting_planet": "pluto", "aspect": "square", "orb": "1.5"}]
    results = _compute_convergences(c, _BASE_STATE)
    assert not any("MULTI-OUTER PRESSURE" in r for r in results)


# --- Edge cases ---

def test_empty_chart_returns_empty():
    assert _compute_convergences({}, _BASE_STATE) == []


def test_all_none_fields_no_crash():
    c = _chart(None, None, None)
    results = _compute_convergences(c, _BASE_STATE)
    assert isinstance(results, list)


# =============================================================================
# _compute_synastry_convergences
# =============================================================================

_NAME_A = "Alice"
_NAME_B = "Bob"
_CHART_A: dict = {}
_CHART_B: dict = {}


def _syn(cross_aspects=None, overlays_b_in_a=None, overlays_a_in_b=None, composite=None):
    return {
        "cross_aspects": cross_aspects or [],
        "house_overlays_b_in_a": overlays_b_in_a or [],
        "house_overlays_a_in_b": overlays_a_in_b or [],
        "composite": composite or {},
        "composite_aspects": [],
    }


def _aspect(planet_a, planet_b, aspect="conjunction", orb="1.0", applying=True):
    return {"planet_a": planet_a, "planet_b": planet_b, "aspect": aspect,
            "orb": orb, "applying": applying}


# --- Sun-Moon inter-aspects ---

def test_mutual_luminaries_detected():
    s = _syn(cross_aspects=[
        _aspect("sun", "moon"),
        _aspect("moon", "sun"),
    ])
    results = _compute_synastry_convergences(_NAME_A, _CHART_A, _NAME_B, _CHART_B, s)
    assert any("MUTUAL LUMINARIES" in r for r in results)


def test_single_sun_moon_aspect_detected():
    s = _syn(cross_aspects=[_aspect("sun", "moon")])
    results = _compute_synastry_convergences(_NAME_A, _CHART_A, _NAME_B, _CHART_B, s)
    assert any("SUN-MOON INTER-ASPECT" in r for r in results)


def test_no_sun_moon_aspect_not_flagged():
    s = _syn(cross_aspects=[_aspect("venus", "mars")])
    results = _compute_synastry_convergences(_NAME_A, _CHART_A, _NAME_B, _CHART_B, s)
    assert not any("SUN-MOON" in r or "MUTUAL LUMINARIES" in r for r in results)


# --- Double whammy ---

def test_double_whammy_detected():
    s = _syn(cross_aspects=[
        _aspect("venus", "mars", "conjunction"),
        _aspect("mars", "venus", "trine"),
    ])
    results = _compute_synastry_convergences(_NAME_A, _CHART_A, _NAME_B, _CHART_B, s)
    assert any("DOUBLE WHAMMY" in r for r in results)


def test_single_venus_mars_not_double_whammy():
    s = _syn(cross_aspects=[_aspect("venus", "mars")])
    results = _compute_synastry_convergences(_NAME_A, _CHART_A, _NAME_B, _CHART_B, s)
    assert not any("DOUBLE WHAMMY" in r for r in results)


def test_double_whammy_excludes_sun_moon_pair():
    # sun-moon handled separately — should NOT also appear as a double whammy
    s = _syn(cross_aspects=[
        _aspect("sun", "moon"),
        _aspect("moon", "sun"),
    ])
    results = _compute_synastry_convergences(_NAME_A, _CHART_A, _NAME_B, _CHART_B, s)
    assert not any("DOUBLE WHAMMY" in r for r in results)


# --- Saturn contacts ---

def test_saturn_square_sun_flagged():
    s = _syn(cross_aspects=[_aspect("saturn", "sun", "square")])
    results = _compute_synastry_convergences(_NAME_A, _CHART_A, _NAME_B, _CHART_B, s)
    assert any("SATURN-LUMINARY" in r for r in results)


def test_saturn_trine_sun_not_flagged():
    s = _syn(cross_aspects=[_aspect("saturn", "sun", "trine")])
    results = _compute_synastry_convergences(_NAME_A, _CHART_A, _NAME_B, _CHART_B, s)
    assert not any("SATURN-LUMINARY" in r for r in results)


def test_saturn_opposite_moon_flagged():
    s = _syn(cross_aspects=[_aspect("moon", "saturn", "opposition")])
    results = _compute_synastry_convergences(_NAME_A, _CHART_A, _NAME_B, _CHART_B, s)
    assert any("SATURN-LUMINARY" in r for r in results)


# --- Angular overlays ---

def test_angular_overlay_single_detected():
    s = _syn(overlays_b_in_a=[{"planet": "sun", "sign": "Aries", "house_in_partner": 1}])
    results = _compute_synastry_convergences(_NAME_A, _CHART_A, _NAME_B, _CHART_B, s)
    assert any("ANGULAR OVERLAY" in r for r in results)


def test_angular_saturation_three_planets():
    overlays = [
        {"planet": "sun", "sign": "Aries", "house_in_partner": 1},
        {"planet": "moon", "sign": "Cancer", "house_in_partner": 7},
        {"planet": "venus", "sign": "Taurus", "house_in_partner": 10},
    ]
    s = _syn(overlays_b_in_a=overlays)
    results = _compute_synastry_convergences(_NAME_A, _CHART_A, _NAME_B, _CHART_B, s)
    assert any("ANGULAR SATURATION" in r for r in results)


def test_non_angular_overlay_not_flagged():
    s = _syn(overlays_b_in_a=[{"planet": "sun", "sign": "Aries", "house_in_partner": 3}])
    results = _compute_synastry_convergences(_NAME_A, _CHART_A, _NAME_B, _CHART_B, s)
    assert not any("ANGULAR" in r for r in results)


# --- Composite angular planets ---

def test_composite_angular_planet_detected():
    s = _syn(composite={"sun": {"sign": "Aries", "position": "15", "house": 1}})
    results = _compute_synastry_convergences(_NAME_A, _CHART_A, _NAME_B, _CHART_B, s)
    assert any("COMPOSITE ANGULAR" in r for r in results)


def test_composite_non_angular_not_flagged():
    s = _syn(composite={"sun": {"sign": "Aries", "position": "15", "house": 3}})
    results = _compute_synastry_convergences(_NAME_A, _CHART_A, _NAME_B, _CHART_B, s)
    assert not any("COMPOSITE ANGULAR" in r for r in results)


def test_empty_synastry_no_crash():
    results = _compute_synastry_convergences(_NAME_A, {}, _NAME_B, {}, {})
    assert isinstance(results, list)
    assert results == []
