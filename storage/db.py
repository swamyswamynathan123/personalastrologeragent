"""SQLite-backed persistence for saved natal and synastry readings."""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path

_DB_PATH = Path(__file__).parent.parent / "charts.db"


def _conn() -> sqlite3.Connection:
    return sqlite3.connect(_DB_PATH)


def init_db() -> None:
    with _conn() as con:
        con.execute("""
        CREATE TABLE IF NOT EXISTS saved_charts (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            chart_type  TEXT    NOT NULL,
            name        TEXT    NOT NULL,
            created_at  TEXT    NOT NULL,
            state_json  TEXT    NOT NULL
        )
        """)
        con.commit()


def _strip_svgs(d: dict) -> dict:
    """Remove large SVG blobs before serialising — they can be regenerated."""
    result = {**d}
    if cd := result.get("chart_data"):
        result["chart_data"] = {k: v for k, v in cd.items() if not k.endswith("_svg")}
    return result


def save_natal(state: dict) -> int:
    """Persist a natal reading.  Returns the new row id."""
    name = (state.get("full_name") or "Unknown").strip()
    payload = json.dumps(_strip_svgs(state), default=str)
    with _conn() as con:
        cur = con.execute(
            "INSERT INTO saved_charts (chart_type, name, created_at, state_json) VALUES (?, ?, ?, ?)",
            ("natal", name, datetime.utcnow().isoformat(), payload),
        )
        con.commit()
        return cur.lastrowid


def save_synastry(syn: dict) -> int:
    """Persist a synastry reading.  Returns the new row id."""
    name_a = (syn.get("name_a") or "?").strip()
    name_b = (syn.get("name_b") or "?").strip()
    clean = {**syn}
    for key in ("chart_a", "chart_b"):
        if cd := clean.get(key):
            clean[key] = {k: v for k, v in cd.items() if not k.endswith("_svg")}
    payload = json.dumps(clean, default=str)
    with _conn() as con:
        cur = con.execute(
            "INSERT INTO saved_charts (chart_type, name, created_at, state_json) VALUES (?, ?, ?, ?)",
            ("synastry", f"{name_a} & {name_b}", datetime.utcnow().isoformat(), payload),
        )
        con.commit()
        return cur.lastrowid


def list_charts() -> list[dict]:
    """Return all saved charts sorted newest-first (no state_json)."""
    with _conn() as con:
        rows = con.execute(
            "SELECT id, chart_type, name, created_at FROM saved_charts ORDER BY created_at DESC"
        ).fetchall()
    return [{"id": r[0], "chart_type": r[1], "name": r[2], "created_at": r[3]} for r in rows]


def load_chart(chart_id: int) -> dict | None:
    """Return the deserialized state dict for a saved chart, or None."""
    with _conn() as con:
        row = con.execute(
            "SELECT state_json FROM saved_charts WHERE id = ?", (chart_id,)
        ).fetchone()
    return json.loads(row[0]) if row else None


def delete_chart(chart_id: int) -> None:
    with _conn() as con:
        con.execute("DELETE FROM saved_charts WHERE id = ?", (chart_id,))
        con.commit()
