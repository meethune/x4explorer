"""Tests for database connection lifecycle."""

from __future__ import annotations

import sqlite3
from typing import TYPE_CHECKING

import pytest

from x4explorer._db import _validate_schema, close_db, find_default_db, init_db

if TYPE_CHECKING:
    from pathlib import Path


class TestInitDb:
    def test_missing_file_raises(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError, match="Database not found"):
            init_db(tmp_path / "nonexistent.db")

    def test_opens_valid_db(self, test_db: Path) -> None:
        init_db(test_db)
        close_db()

    def test_sets_read_only(self, test_db: Path) -> None:
        init_db(test_db)
        from x4explorer._db import get_db

        conn = get_db()
        with pytest.raises(sqlite3.OperationalError):
            conn.execute("INSERT INTO meta VALUES ('x', 'y')")
        close_db()


class TestValidateSchema:
    def test_valid_schema_passes(self, test_db: Path) -> None:
        conn = sqlite3.connect(test_db)
        _validate_schema(conn)
        conn.close()

    def test_missing_table_raises(self, tmp_path: Path) -> None:
        db = tmp_path / "incomplete.db"
        conn = sqlite3.connect(db)
        conn.execute("CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT)")
        conn.commit()
        with pytest.raises(RuntimeError, match="missing tables"):
            _validate_schema(conn)
        conn.close()


class TestFindDefaultDb:
    def test_returns_none_when_no_cache(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "empty_cache"))
        assert find_default_db() is None
