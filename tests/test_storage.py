"""
Tests for storage/db.py — SQLite persistence for natal and synastry readings.

Strategy: uses a fresh in-memory-equivalent temp file per test so the real
charts.db is never touched.
"""
import json
import pytest
from pathlib import Path
from unittest.mock import patch


# ── Helpers ──────────────────────────────────────────────────────────────────

def _tmp_db(tmp_path: Path):
    """Return a patched db module pointing at a fresh temp DB."""
    import storage.db as db
    tmp_file = tmp_path / "test_charts.db"
    with patch.object(db, "_DB_PATH", tmp_file):
        db.init_db()
        yield db


@pytest.fixture()
def db(tmp_path):
    yield from _tmp_db(tmp_path)


_NATAL = {
    "full_name": "Jane Doe",
    "parsed_dob": "1990-05-15",
    "birth_location": "Mumbai, India",
    "current_location": "New York, USA",
    "parsed_current_datetime": "2026-05-17T12:00:00+00:00",
    "final_report": "This is the report.",
    "chart_data": {
        "sun": {"sign": "Taurus", "position": 24.5},
        "chart_svg": "<svg/>",   # should be stripped on save
    },
}

_SYNASTRY = {
    "name_a": "Alice",
    "dob_a": "1990-03-21",
    "loc_a": "London, UK",
    "name_b": "Bob",
    "dob_b": "1988-11-15",
    "loc_b": "Paris, France",
    "chart_a": {"sun": {"sign": "Aries"}, "chart_svg": "<svg/>"},
    "chart_b": {"sun": {"sign": "Scorpio"}, "vedic_svg": "<svg/>"},
    "report": "Great compatibility.",
}


# ── init_db ───────────────────────────────────────────────────────────────────

def test_init_db_is_idempotent(db):
    db.init_db()  # second call must not raise
    db.init_db()


# ── save_natal / list_charts / load_chart ─────────────────────────────────────

def test_save_natal_returns_id(db):
    row_id = db.save_natal(_NATAL)
    assert isinstance(row_id, int)
    assert row_id > 0


def test_list_charts_after_save(db):
    db.save_natal(_NATAL)
    charts = db.list_charts()
    assert len(charts) == 1
    assert charts[0]["chart_type"] == "natal"
    assert charts[0]["name"] == "Jane Doe"


def test_load_chart_roundtrip(db):
    row_id = db.save_natal(_NATAL)
    loaded = db.load_chart(row_id)
    assert loaded is not None
    assert loaded["full_name"] == "Jane Doe"
    assert loaded["final_report"] == "This is the report."


def test_save_natal_strips_svg(db):
    row_id = db.save_natal(_NATAL)
    loaded = db.load_chart(row_id)
    # chart_svg should have been removed before saving
    assert "chart_svg" not in (loaded.get("chart_data") or {})
    # other chart fields preserved
    assert loaded["chart_data"]["sun"]["sign"] == "Taurus"


def test_load_chart_missing_id_returns_none(db):
    assert db.load_chart(9999) is None


def test_list_charts_sorted_newest_first(db):
    db.save_natal({**_NATAL, "full_name": "Alice"})
    db.save_natal({**_NATAL, "full_name": "Bob"})
    charts = db.list_charts()
    assert charts[0]["name"] == "Bob"   # most recent first


# ── save_synastry ─────────────────────────────────────────────────────────────

def test_save_synastry_returns_id(db):
    row_id = db.save_synastry(_SYNASTRY)
    assert isinstance(row_id, int)


def test_save_synastry_name_format(db):
    db.save_synastry(_SYNASTRY)
    charts = db.list_charts()
    assert charts[0]["name"] == "Alice & Bob"
    assert charts[0]["chart_type"] == "synastry"


def test_save_synastry_strips_svgs(db):
    row_id = db.save_synastry(_SYNASTRY)
    loaded = db.load_chart(row_id)
    assert "chart_svg" not in (loaded.get("chart_a") or {})
    assert "vedic_svg" not in (loaded.get("chart_b") or {})
    assert loaded["report"] == "Great compatibility."


# ── delete_chart ──────────────────────────────────────────────────────────────

def test_delete_chart_removes_entry(db):
    row_id = db.save_natal(_NATAL)
    db.delete_chart(row_id)
    assert db.load_chart(row_id) is None
    assert db.list_charts() == []


def test_delete_nonexistent_does_not_raise(db):
    db.delete_chart(9999)  # must not raise


# ── mixed natal + synastry in list ────────────────────────────────────────────

def test_list_charts_mixed_types(db):
    db.save_natal(_NATAL)
    db.save_synastry(_SYNASTRY)
    charts = db.list_charts()
    assert len(charts) == 2
    types = {c["chart_type"] for c in charts}
    assert types == {"natal", "synastry"}
