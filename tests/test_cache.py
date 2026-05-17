"""
Tests for cache/report_cache.py.
Uses a temporary database so tests never touch the real cache file.
"""
import json
import time
import pytest
from pathlib import Path
from unittest.mock import patch


# ---------------------------------------------------------------------------
# Redirect DB to a temp file for every test
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def tmp_cache_db(tmp_path, monkeypatch):
    """Point _DB_PATH to a fresh temp file for each test."""
    import cache.report_cache as rc
    monkeypatch.setattr(rc, "_DB_PATH", tmp_path / "test_cache.db")
    yield


# ---------------------------------------------------------------------------
# Key builders — deterministic, collision-free
# ---------------------------------------------------------------------------

from cache.report_cache import (
    make_chart_key,
    make_report_key,
    make_synastry_report_key,
    get_chart, set_chart,
    get_report, set_report,
    purge_expired,
    _CHART_TTL, _REPORT_TTL,
)


def test_chart_key_deterministic():
    k1 = make_chart_key("1990-05-15", "Mumbai, India", "14:30", "Asia/Kolkata", "Placidus", "New York, USA", "2026-05-17")
    k2 = make_chart_key("1990-05-15", "Mumbai, India", "14:30", "Asia/Kolkata", "Placidus", "New York, USA", "2026-05-17")
    assert k1 == k2


def test_chart_key_differs_by_dob():
    k1 = make_chart_key("1990-05-15", "Mumbai, India", "14:30", "Asia/Kolkata", "Placidus", "New York, USA", "2026-05-17")
    k2 = make_chart_key("1991-05-15", "Mumbai, India", "14:30", "Asia/Kolkata", "Placidus", "New York, USA", "2026-05-17")
    assert k1 != k2


def test_chart_key_differs_by_house_system():
    k1 = make_chart_key("1990-05-15", "Mumbai, India", "14:30", "Asia/Kolkata", "Placidus", "New York, USA", "2026-05-17")
    k2 = make_chart_key("1990-05-15", "Mumbai, India", "14:30", "Asia/Kolkata", "Whole Sign", "New York, USA", "2026-05-17")
    assert k1 != k2


def test_chart_key_differs_by_current_date():
    k1 = make_chart_key("1990-05-15", "Mumbai, India", "14:30", "Asia/Kolkata", "Placidus", "New York, USA", "2026-05-17")
    k2 = make_chart_key("1990-05-15", "Mumbai, India", "14:30", "Asia/Kolkata", "Placidus", "New York, USA", "2026-05-18")
    assert k1 != k2


def test_report_key_deterministic():
    k1 = make_report_key("1990-05-15", "Mumbai, India", "14:30", "Asia/Kolkata", "Placidus", "New York, USA", "2026-05-17", "career", "")
    k2 = make_report_key("1990-05-15", "Mumbai, India", "14:30", "Asia/Kolkata", "Placidus", "New York, USA", "2026-05-17", "career", "")
    assert k1 == k2


def test_report_key_differs_by_focus():
    k1 = make_report_key("1990-05-15", "Mumbai, India", "14:30", "Asia/Kolkata", "Placidus", "New York, USA", "2026-05-17", "career", "")
    k2 = make_report_key("1990-05-15", "Mumbai, India", "14:30", "Asia/Kolkata", "Placidus", "New York, USA", "2026-05-17", "relationships", "")
    assert k1 != k2


def test_report_key_differs_from_chart_key():
    ck = make_chart_key("1990-05-15", "Mumbai, India", "14:30", "Asia/Kolkata", "Placidus", "New York, USA", "2026-05-17")
    rk = make_report_key("1990-05-15", "Mumbai, India", "14:30", "Asia/Kolkata", "Placidus", "New York, USA", "2026-05-17", "", "")
    assert ck != rk


def test_synastry_report_key_deterministic():
    k1 = make_synastry_report_key("1990-05-15", "London, UK", "10:00", "1992-06-20", "Paris, France", "08:00", "2026-05-17")
    k2 = make_synastry_report_key("1990-05-15", "London, UK", "10:00", "1992-06-20", "Paris, France", "08:00", "2026-05-17")
    assert k1 == k2


def test_synastry_report_key_differs_by_dob_b():
    k1 = make_synastry_report_key("1990-05-15", "London, UK", "10:00", "1992-06-20", "Paris, France", "08:00", "2026-05-17")
    k2 = make_synastry_report_key("1990-05-15", "London, UK", "10:00", "1993-06-20", "Paris, France", "08:00", "2026-05-17")
    assert k1 != k2


# ---------------------------------------------------------------------------
# Chart cache — round-trip
# ---------------------------------------------------------------------------

def test_chart_cache_miss_returns_none():
    assert get_chart("nonexistent-key") is None


def test_chart_cache_round_trip():
    data = {"sun": {"sign": "Aries"}, "moon": {"sign": "Taurus"}}
    set_chart("key1", data)
    result = get_chart("key1")
    assert result == data


def test_chart_cache_stores_nested_structures():
    data = {"planets": [{"name": "Sun", "pos": 15.5}], "aspects": []}
    set_chart("key2", data)
    result = get_chart("key2")
    assert result["planets"][0]["pos"] == 15.5


def test_chart_cache_overwrite():
    set_chart("key3", {"version": 1})
    set_chart("key3", {"version": 2})
    assert get_chart("key3")["version"] == 2


def test_chart_cache_expired_returns_none():
    import cache.report_cache as rc
    set_chart("exp-key", {"data": "old"})
    # Manually backdating the timestamp
    import sqlite3
    with sqlite3.connect(rc._DB_PATH) as conn:
        conn.execute("UPDATE chart_cache SET ts = ? WHERE key = ?",
                     (time.time() - _CHART_TTL - 1, "exp-key"))
    assert get_chart("exp-key") is None


def test_chart_cache_not_expired_returns_data():
    set_chart("fresh-key", {"data": "fresh"})
    assert get_chart("fresh-key") is not None


# ---------------------------------------------------------------------------
# Report cache — round-trip
# ---------------------------------------------------------------------------

def test_report_cache_miss_returns_none():
    assert get_report("no-such-key") is None


def test_report_cache_round_trip():
    text = "# My Astrological Reading\n\nYour Sun is in Aries..."
    set_report("rkey1", text)
    assert get_report("rkey1") == text


def test_report_cache_overwrite():
    set_report("rkey2", "old report")
    set_report("rkey2", "new report")
    assert get_report("rkey2") == "new report"


def test_report_cache_expired_returns_none():
    import cache.report_cache as rc
    set_report("rexp-key", "old report")
    import sqlite3
    with sqlite3.connect(rc._DB_PATH) as conn:
        conn.execute("UPDATE report_cache SET ts = ? WHERE key = ?",
                     (time.time() - _REPORT_TTL - 1, "rexp-key"))
    assert get_report("rexp-key") is None


def test_report_cache_not_expired_returns_data():
    set_report("rfresh-key", "fresh report")
    assert get_report("rfresh-key") == "fresh report"


# ---------------------------------------------------------------------------
# purge_expired
# ---------------------------------------------------------------------------

def test_purge_removes_expired_chart_entries():
    import cache.report_cache as rc
    set_chart("old1", {"x": 1})
    set_chart("new1", {"x": 2})
    import sqlite3
    with sqlite3.connect(rc._DB_PATH) as conn:
        conn.execute("UPDATE chart_cache SET ts = ? WHERE key = ?",
                     (time.time() - _CHART_TTL - 1, "old1"))
    purge_expired()
    assert get_chart("old1") is None
    assert get_chart("new1") is not None


def test_purge_removes_expired_report_entries():
    import cache.report_cache as rc
    set_report("rold1", "old")
    set_report("rnew1", "new")
    import sqlite3
    with sqlite3.connect(rc._DB_PATH) as conn:
        conn.execute("UPDATE report_cache SET ts = ? WHERE key = ?",
                     (time.time() - _REPORT_TTL - 1, "rold1"))
    purge_expired()
    assert get_report("rold1") is None
    assert get_report("rnew1") == "new"


def test_purge_on_empty_db_no_crash():
    purge_expired()  # should not raise


# ---------------------------------------------------------------------------
# Error resilience — cache failures must not break callers
# ---------------------------------------------------------------------------

def test_get_chart_bad_db_returns_none(monkeypatch, tmp_path):
    import cache.report_cache as rc
    monkeypatch.setattr(rc, "_DB_PATH", tmp_path / "readonly_dir" / "cache.db")
    # Path doesn't exist → connection will fail → should return None
    result = get_chart("any-key")
    assert result is None


def test_set_chart_bad_db_no_raise(monkeypatch, tmp_path):
    import cache.report_cache as rc
    monkeypatch.setattr(rc, "_DB_PATH", tmp_path / "readonly_dir" / "cache.db")
    set_chart("any-key", {"data": "x"})  # must not raise


def test_get_report_bad_db_returns_none(monkeypatch, tmp_path):
    import cache.report_cache as rc
    monkeypatch.setattr(rc, "_DB_PATH", tmp_path / "readonly_dir" / "cache.db")
    assert get_report("any-key") is None


def test_set_report_bad_db_no_raise(monkeypatch, tmp_path):
    import cache.report_cache as rc
    monkeypatch.setattr(rc, "_DB_PATH", tmp_path / "readonly_dir" / "cache.db")
    set_report("any-key", "some text")  # must not raise
