"""Database connection lifecycle for x4explorer."""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path

_CONNECTION: sqlite3.Connection | None = None


def init_db(db_path: Path) -> None:
    """Open the SQLite database at startup (read-only)."""
    global _CONNECTION  # noqa: PLW0603
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA query_only = ON")
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
