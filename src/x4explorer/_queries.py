"""Database query helpers for x4explorer."""

from __future__ import annotations

from typing import TYPE_CHECKING

from x4explorer._pagination import Page

if TYPE_CHECKING:
    import sqlite3

_COUNTABLE_TABLES = ("macros", "components", "wares", "game_files")


def _escape_like(value: str) -> str:
    """Escape SQL LIKE wildcards for literal matching."""
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def get_table_counts(conn: sqlite3.Connection) -> dict[str, int]:
    """Return row counts for primary tables."""
    return {
        table: conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]  # noqa: S608
        for table in _COUNTABLE_TABLES
    }


def get_meta(conn: sqlite3.Connection, key: str) -> str | None:
    """Return a value from the meta table, or None."""
    row = conn.execute("SELECT value FROM meta WHERE key = ?", (key,)).fetchone()
    return row[0] if row else None


def search(
    conn: sqlite3.Connection,
    query: str,
    *,
    type_filter: str | None = None,
    page: int = 1,
    per_page: int = 50,
) -> tuple[list[dict[str, str]], Page]:
    """Search across wares, macros, and components.

    Returns (results_page, page_info) where results_page is the
    current page slice and page_info has pagination metadata.
    """
    if not query or not query.strip():
        return [], Page(number=1, per_page=per_page, total_rows=0)

    escaped = _escape_like(query.strip())
    pattern = f"%{escaped}%"
    results: list[dict[str, str]] = []

    if type_filter is None or type_filter == "ware":
        rows = conn.execute(
            "SELECT ware_id, name_ref, ware_group, transport "
            "FROM wares "
            "WHERE ware_id LIKE ? ESCAPE '\\' OR name_ref LIKE ? ESCAPE '\\'",
            (pattern, pattern),
        ).fetchall()
        for row in rows:
            detail = row["ware_group"]
            if row["transport"]:
                detail += f" [{row['transport']}]"
            results.append({"type": "ware", "id": row["ware_id"], "detail": detail})

    if type_filter is None or type_filter == "macro":
        rows = conn.execute(
            "SELECT name, value FROM macros WHERE name LIKE ? ESCAPE '\\'",
            (pattern,),
        ).fetchall()
        for row in rows:
            results.append({"type": "macro", "id": row["name"], "detail": row["value"]})

    if type_filter is None or type_filter == "component":
        rows = conn.execute(
            "SELECT name, value FROM components WHERE name LIKE ? ESCAPE '\\'",
            (pattern,),
        ).fetchall()
        for row in rows:
            results.append({"type": "component", "id": row["name"], "detail": row["value"]})

    page_info = Page(number=max(1, page), per_page=per_page, total_rows=len(results))
    start = page_info.offset
    end = start + per_page
    return results[start:end], page_info
