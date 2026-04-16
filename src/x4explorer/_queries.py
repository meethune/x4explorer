"""Database query helpers for x4explorer."""

from __future__ import annotations

from typing import TYPE_CHECKING

from x4explorer._pagination import Page

if TYPE_CHECKING:
    import sqlite3

_COUNTABLE_TABLES = (
    "macros",
    "components",
    "wares",
    "game_files",
    "script_datatypes",
    "script_keywords",
)


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

    if type_filter is None or type_filter == "datatype":
        rows = conn.execute(
            "SELECT name, base_type FROM script_datatypes WHERE name LIKE ? ESCAPE '\\'",
            (pattern,),
        ).fetchall()
        for row in rows:
            detail = f"base: {row['base_type']}" if row["base_type"] else ""
            results.append({"type": "datatype", "id": row["name"], "detail": detail})

    if type_filter is None or type_filter == "keyword":
        rows = conn.execute(
            "SELECT name, description, script FROM script_keywords "
            "WHERE name LIKE ? ESCAPE '\\' OR description LIKE ? ESCAPE '\\'",
            (pattern, pattern),
        ).fetchall()
        for row in rows:
            detail = row["description"]
            if row["script"]:
                detail += f" [{row['script']}]"
            results.append({"type": "keyword", "id": row["name"], "detail": detail})

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


# --- Macros ---

_MACRO_SORT_COLUMNS = frozenset({"name", "value"})


def list_macros(
    conn: sqlite3.Connection,
    *,
    macro_class: str | None = None,
    query: str | None = None,
    sort: str = "name",
    direction: str = "asc",
    page: int = 1,
    per_page: int = 10,
) -> tuple[list[sqlite3.Row], Page]:
    """List macros with class and component_ref from properties, paginated."""
    clauses: list[str] = []
    params: list[object] = []

    if macro_class:
        clauses.append("mp_class.property_val = ?")
        params.append(macro_class)
    if query:
        escaped = _escape_like(query)
        clauses.append("m.name LIKE ? ESCAPE '\\'")
        params.append(f"%{escaped}%")

    where = f" WHERE {' AND '.join(clauses)}" if clauses else ""

    count_sql = (
        "SELECT COUNT(*) FROM macros m "
        "LEFT JOIN macro_properties mp_class "
        "ON m.name = mp_class.macro_name AND mp_class.property_key = 'class'"
        f"{where}"
    )
    total = conn.execute(count_sql, params).fetchone()[0]

    if sort not in _MACRO_SORT_COLUMNS:
        sort = "name"
    sort_col = f"m.{sort}"
    order_dir = "DESC" if direction.upper() == "DESC" else "ASC"

    page_info = Page(number=max(1, page), per_page=per_page, total_rows=total)
    rows = conn.execute(
        "SELECT m.name, m.value, "
        "mp_class.property_val AS class, "
        "mp_comp.property_val AS component_ref "
        "FROM macros m "
        "LEFT JOIN macro_properties mp_class "
        "ON m.name = mp_class.macro_name AND mp_class.property_key = 'class' "
        "LEFT JOIN macro_properties mp_comp "
        "ON m.name = mp_comp.macro_name AND mp_comp.property_key = 'component_ref'"
        f"{where} ORDER BY {sort_col} {order_dir} LIMIT ? OFFSET ?",
        (*params, per_page, page_info.offset),
    ).fetchall()
    return rows, page_info


def get_macro(conn: sqlite3.Connection, name: str) -> sqlite3.Row | None:
    """Return a single macro by name."""
    result: sqlite3.Row | None = conn.execute(
        "SELECT * FROM macros WHERE name = ?", (name,)
    ).fetchone()
    return result


def get_macro_properties(conn: sqlite3.Connection, macro_name: str) -> list[sqlite3.Row]:
    """Return all properties for a macro, sorted by key."""
    return conn.execute(
        "SELECT property_key, property_val FROM macro_properties "
        "WHERE macro_name = ? ORDER BY property_key",
        (macro_name,),
    ).fetchall()


def get_macro_ware(conn: sqlite3.Connection, macro_name: str) -> str | None:
    """Find a ware ID that matches this macro name."""
    # Ware IDs often match a prefix of the macro name (minus _macro suffix)
    prefix = macro_name.removesuffix("_macro")
    row = conn.execute(
        "SELECT ware_id FROM wares WHERE ware_id = ? OR ware_id = ?",
        (prefix, macro_name),
    ).fetchone()
    return row[0] if row else None


def get_macro_filter_options(conn: sqlite3.Connection) -> dict[str, list[str]]:
    """Return distinct macro class values for filter dropdown."""
    classes = [
        r[0]
        for r in conn.execute(
            "SELECT DISTINCT property_val FROM macro_properties "
            "WHERE property_key = 'class' AND property_val != '' "
            "ORDER BY property_val"
        ).fetchall()
    ]
    return {"classes": classes}


# --- Components ---

_COMPONENT_SORT_COLUMNS = frozenset({"name", "value"})


def list_components(
    conn: sqlite3.Connection,
    *,
    query: str | None = None,
    sort: str = "name",
    direction: str = "asc",
    page: int = 1,
    per_page: int = 10,
) -> tuple[list[sqlite3.Row], Page]:
    """List components, paginated."""
    clauses: list[str] = []
    params: list[object] = []

    if query:
        escaped = _escape_like(query)
        clauses.append("name LIKE ? ESCAPE '\\'")
        params.append(f"%{escaped}%")

    where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
    total = conn.execute(
        f"SELECT COUNT(*) FROM components{where}",
        params,  # noqa: S608
    ).fetchone()[0]

    if sort not in _COMPONENT_SORT_COLUMNS:
        sort = "name"
    order_dir = "DESC" if direction.upper() == "DESC" else "ASC"

    page_info = Page(number=max(1, page), per_page=per_page, total_rows=total)
    rows = conn.execute(
        f"SELECT * FROM components{where} ORDER BY {sort} {order_dir} "  # noqa: S608
        "LIMIT ? OFFSET ?",
        (*params, per_page, page_info.offset),
    ).fetchall()
    return rows, page_info


def get_component(conn: sqlite3.Connection, name: str) -> sqlite3.Row | None:
    """Return a single component by name."""
    result: sqlite3.Row | None = conn.execute(
        "SELECT * FROM components WHERE name = ?", (name,)
    ).fetchone()
    return result


def get_component_macros(conn: sqlite3.Connection, component_name: str) -> list[sqlite3.Row]:
    """Return macros that reference this component via component_ref."""
    return conn.execute(
        "SELECT macro_name FROM macro_properties "
        "WHERE property_key = 'component_ref' AND property_val = ?",
        (component_name,),
    ).fetchall()


# --- Script Datatypes ---

_DATATYPE_SORT_COLUMNS = frozenset({"name", "base_type"})


def list_datatypes(
    conn: sqlite3.Connection,
    *,
    base_type: str | None = None,
    query: str | None = None,
    sort: str = "name",
    direction: str = "asc",
    page: int = 1,
    per_page: int = 10,
) -> tuple[list[sqlite3.Row], Page]:
    """List script datatypes, paginated."""
    clauses: list[str] = []
    params: list[object] = []

    if base_type:
        clauses.append("base_type = ?")
        params.append(base_type)
    if query:
        escaped = _escape_like(query)
        clauses.append("name LIKE ? ESCAPE '\\'")
        params.append(f"%{escaped}%")

    where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
    total = conn.execute(
        f"SELECT COUNT(*) FROM script_datatypes{where}",  # noqa: S608
        params,
    ).fetchone()[0]

    if sort not in _DATATYPE_SORT_COLUMNS:
        sort = "name"
    order_dir = "DESC" if direction.upper() == "DESC" else "ASC"

    page_info = Page(number=max(1, page), per_page=per_page, total_rows=total)
    rows = conn.execute(
        f"SELECT * FROM script_datatypes{where} ORDER BY {sort} {order_dir} "  # noqa: S608
        "LIMIT ? OFFSET ?",
        (*params, per_page, page_info.offset),
    ).fetchall()
    return rows, page_info


def get_datatype(conn: sqlite3.Connection, name: str) -> sqlite3.Row | None:
    """Return a single script datatype by name."""
    result: sqlite3.Row | None = conn.execute(
        "SELECT * FROM script_datatypes WHERE name = ?", (name,)
    ).fetchone()
    return result


def get_inheritance_chain(conn: sqlite3.Connection, name: str) -> list[sqlite3.Row]:
    """Walk the base_type chain, returning [self, parent, grandparent, ...]."""
    chain: list[sqlite3.Row] = []
    current = name
    seen: set[str] = set()
    while current and current not in seen:
        seen.add(current)
        row = conn.execute(
            "SELECT name, base_type FROM script_datatypes WHERE name = ?",
            (current,),
        ).fetchone()
        if not row:
            break
        chain.append(row)
        current = row["base_type"]
    return chain


def get_datatype_properties(conn: sqlite3.Connection, datatype_name: str) -> list[sqlite3.Row]:
    """Return properties owned by this datatype."""
    return conn.execute(
        "SELECT prop_name, result_desc, result_type FROM script_properties "
        "WHERE owner_name = ? AND owner_kind = 'datatype' ORDER BY prop_name",
        (datatype_name,),
    ).fetchall()


def get_all_datatype_names(conn: sqlite3.Connection) -> set[str]:
    """Return the set of all datatype names (for result_type linking)."""
    return {r[0] for r in conn.execute("SELECT name FROM script_datatypes").fetchall()}


def get_datatype_filter_options(conn: sqlite3.Connection) -> dict[str, list[str]]:
    """Return distinct base_type values for filter dropdown."""
    base_types = [
        r[0]
        for r in conn.execute(
            "SELECT DISTINCT base_type FROM script_datatypes "
            "WHERE base_type IS NOT NULL AND base_type != '' "
            "ORDER BY base_type"
        ).fetchall()
    ]
    return {"base_types": base_types}


# --- Script Keywords ---

_KEYWORD_SORT_COLUMNS = frozenset({"name", "description", "type", "script"})


def list_keywords(
    conn: sqlite3.Connection,
    *,
    script: str | None = None,
    query: str | None = None,
    sort: str = "name",
    direction: str = "asc",
    page: int = 1,
    per_page: int = 10,
) -> tuple[list[sqlite3.Row], Page]:
    """List script keywords, paginated."""
    clauses: list[str] = []
    params: list[object] = []

    if script:
        clauses.append("script = ?")
        params.append(script)
    if query:
        escaped = _escape_like(query)
        clauses.append("name LIKE ? ESCAPE '\\'")
        params.append(f"%{escaped}%")

    where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
    total = conn.execute(
        f"SELECT COUNT(*) FROM script_keywords{where}",  # noqa: S608
        params,
    ).fetchone()[0]

    if sort not in _KEYWORD_SORT_COLUMNS:
        sort = "name"
    order_dir = "DESC" if direction.upper() == "DESC" else "ASC"

    page_info = Page(number=max(1, page), per_page=per_page, total_rows=total)
    rows = conn.execute(
        f"SELECT * FROM script_keywords{where} ORDER BY {sort} {order_dir} "  # noqa: S608
        "LIMIT ? OFFSET ?",
        (*params, per_page, page_info.offset),
    ).fetchall()
    return rows, page_info


def get_keyword(conn: sqlite3.Connection, name: str) -> sqlite3.Row | None:
    """Return a single script keyword by name."""
    result: sqlite3.Row | None = conn.execute(
        "SELECT * FROM script_keywords WHERE name = ?", (name,)
    ).fetchone()
    return result


def get_keyword_properties(conn: sqlite3.Connection, keyword_name: str) -> list[sqlite3.Row]:
    """Return properties owned by this keyword."""
    return conn.execute(
        "SELECT prop_name, result_desc, result_type FROM script_properties "
        "WHERE owner_name = ? AND owner_kind = 'keyword' ORDER BY prop_name",
        (keyword_name,),
    ).fetchall()


def get_keyword_filter_options(conn: sqlite3.Connection) -> dict[str, list[str]]:
    """Return distinct script values for filter dropdown."""
    scripts = [
        r[0]
        for r in conn.execute(
            "SELECT DISTINCT script FROM script_keywords WHERE script != '' ORDER BY script"
        ).fetchall()
    ]
    return {"scripts": scripts}
