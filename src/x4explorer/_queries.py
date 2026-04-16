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


_WARE_SORT_COLUMNS = frozenset(
    {
        "ware_id",
        "name_ref",
        "ware_group",
        "transport",
        "volume",
        "price_min",
        "price_avg",
        "price_max",
    }
)


def list_wares(
    conn: sqlite3.Connection,
    *,
    group: str | None = None,
    transport: str | None = None,
    tag: str | None = None,
    query: str | None = None,
    sort: str = "ware_id",
    direction: str = "asc",
    page: int = 1,
    per_page: int = 10,
) -> tuple[list[sqlite3.Row], Page]:
    """List wares with optional filters, paginated."""
    clauses: list[str] = []
    params: list[object] = []

    if group:
        clauses.append("ware_group = ?")
        params.append(group)
    if transport:
        clauses.append("transport = ?")
        params.append(transport)
    if tag:
        escaped = _escape_like(tag)
        clauses.append("tags LIKE ? ESCAPE '\\'")
        params.append(f"%{escaped}%")
    if query:
        escaped = _escape_like(query)
        clauses.append("(ware_id LIKE ? ESCAPE '\\' OR name_ref LIKE ? ESCAPE '\\')")
        params.extend([f"%{escaped}%", f"%{escaped}%"])

    where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
    total = conn.execute(f"SELECT COUNT(*) FROM wares{where}", params).fetchone()[0]  # noqa: S608

    if sort not in _WARE_SORT_COLUMNS:
        sort = "ware_id"
    order_dir = "DESC" if direction.upper() == "DESC" else "ASC"

    page_info = Page(number=max(1, page), per_page=per_page, total_rows=total)
    rows = conn.execute(
        f"SELECT * FROM wares{where} ORDER BY {sort} {order_dir} LIMIT ? OFFSET ?",  # noqa: S608
        (*params, per_page, page_info.offset),
    ).fetchall()
    return rows, page_info


def get_ware(conn: sqlite3.Connection, ware_id: str) -> sqlite3.Row | None:
    """Return a single ware by ID."""
    result: sqlite3.Row | None = conn.execute(
        "SELECT * FROM wares WHERE ware_id = ?", (ware_id,)
    ).fetchone()
    return result


def get_ware_owners(conn: sqlite3.Connection, ware_id: str) -> list[sqlite3.Row]:
    """Return owners for a ware."""
    return conn.execute("SELECT faction FROM ware_owners WHERE ware_id = ?", (ware_id,)).fetchall()


def get_ware_macro(conn: sqlite3.Connection, ware_id: str) -> str | None:
    """Find the macro name that references this ware via component_ref.

    Looks for a macro whose component_ref matches a component that
    shares a name prefix with the ware_id.
    """
    row = conn.execute(
        "SELECT m.name FROM macros m "
        "JOIN macro_properties mp ON m.name = mp.macro_name "
        "WHERE mp.property_key = 'component_ref' "
        "AND m.name LIKE ? ESCAPE '\\'",
        (f"%{_escape_like(ware_id)}%",),
    ).fetchone()
    return row[0] if row else None


def get_ware_filter_options(conn: sqlite3.Connection) -> dict[str, list[str]]:
    """Return distinct values for ware filter dropdowns."""
    groups = [
        r[0]
        for r in conn.execute(
            "SELECT DISTINCT ware_group FROM wares WHERE ware_group != '' ORDER BY ware_group"
        ).fetchall()
    ]
    transports = [
        r[0]
        for r in conn.execute(
            "SELECT DISTINCT transport FROM wares WHERE transport != '' ORDER BY transport"
        ).fetchall()
    ]
    # Tags are space-separated — extract individual distinct tags
    tag_set: set[str] = set()
    for r in conn.execute("SELECT DISTINCT tags FROM wares WHERE tags != ''").fetchall():
        tag_set.update(r[0].split())
    tags = sorted(tag_set)

    return {"groups": groups, "transports": transports, "tags": tags}
