"""Database connection lifecycle for x4explorer."""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path

_CONNECTION: sqlite3.Connection | None = None

_REQUIRED_TABLES = frozenset(
    {
        "meta",
        "macros",
        "components",
        "wares",
        "ware_owners",
        "macro_properties",
        "game_files",
    }
)


def _validate_schema(conn: sqlite3.Connection) -> None:
    """Verify the database has the expected tables."""
    rows = conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()
    existing = {row[0] for row in rows}
    missing = _REQUIRED_TABLES - existing
    if missing:
        raise RuntimeError(
            f"Database schema mismatch — missing tables: {', '.join(sorted(missing))}. "
            f"Re-run 'x4cat index' to rebuild."
        )


def init_db(db_path: Path) -> None:
    """Open the SQLite database at startup (read-only).

    Uses URI mode for OS-level read-only enforcement and sets
    performance PRAGMAs for read-heavy workloads.

    All route handlers must be ``async def`` so they run on the
    event loop thread — this single connection is not thread-safe.
    """
    global _CONNECTION  # noqa: PLW0603
    if not db_path.exists():
        raise FileNotFoundError(f"Database not found: {db_path}")
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA query_only = ON")
    conn.execute("PRAGMA mmap_size = 268435456")
    conn.execute("PRAGMA cache_size = -8000")
    conn.execute("PRAGMA temp_store = MEMORY")
    _validate_schema(conn)
    _CONNECTION = conn


def get_db() -> sqlite3.Connection:
    """Return the shared read-only database connection."""
    if _CONNECTION is None:
        raise RuntimeError("Database not initialized — call init_db() first")
    return _CONNECTION


def close_db() -> None:
    """Close the database connection at shutdown."""
    global _CONNECTION  # noqa: PLW0603
    if _CONNECTION is not None:
        _CONNECTION.close()
        _CONNECTION = None


def find_default_db() -> Path | None:
    """Find the most recent x4cat index in the default cache directory."""
    cache_dir = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "x4cat"
    if not cache_dir.exists():
        return None
    dbs = sorted(cache_dir.glob("*.db"), key=lambda p: p.stat().st_mtime)
    return dbs[-1] if dbs else None
