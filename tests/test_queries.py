"""Tests for database query helpers."""

from __future__ import annotations

import sqlite3
from typing import TYPE_CHECKING

from x4explorer._queries import get_meta, get_table_counts, search

if TYPE_CHECKING:
    from pathlib import Path


class TestGetTableCounts:
    def test_returns_all_counts(self, test_db: Path) -> None:
        conn = sqlite3.connect(test_db)
        conn.row_factory = sqlite3.Row
        counts = get_table_counts(conn)
        conn.close()
        assert counts["wares"] == 15
        assert counts["macros"] == 8
        assert counts["components"] == 6
        assert counts["game_files"] == 3

    def test_empty_tables_return_zero(self, tmp_path: Path) -> None:
        db = tmp_path / "empty.db"
        conn = sqlite3.connect(db)
        conn.executescript("""
            CREATE TABLE macros (name TEXT PRIMARY KEY, value TEXT);
            CREATE TABLE components (name TEXT PRIMARY KEY, value TEXT);
            CREATE TABLE wares (ware_id TEXT PRIMARY KEY);
            CREATE TABLE game_files (virtual_path TEXT PRIMARY KEY);
            CREATE TABLE script_datatypes (name TEXT PRIMARY KEY);
            CREATE TABLE script_keywords (name TEXT PRIMARY KEY);
        """)
        counts = get_table_counts(conn)
        conn.close()
        assert all(v == 0 for v in counts.values())


class TestGetMeta:
    def test_returns_value(self, test_db: Path) -> None:
        conn = sqlite3.connect(test_db)
        conn.row_factory = sqlite3.Row
        val = get_meta(conn, "game_dir")
        conn.close()
        assert val == "/test/X4 Foundations"

    def test_missing_key_returns_none(self, test_db: Path) -> None:
        conn = sqlite3.connect(test_db)
        conn.row_factory = sqlite3.Row
        val = get_meta(conn, "nonexistent")
        conn.close()
        assert val is None


class TestSearch:
    def test_search_wares(self, test_db: Path) -> None:
        conn = sqlite3.connect(test_db)
        conn.row_factory = sqlite3.Row
        results, page = search(conn, "energy")
        conn.close()
        ware_ids = [r["id"] for r in results if r["type"] == "ware"]
        assert "energycells" in ware_ids
        assert page.total_rows >= 1

    def test_search_macros(self, test_db: Path) -> None:
        conn = sqlite3.connect(test_db)
        conn.row_factory = sqlite3.Row
        results, _ = search(conn, "fighter")
        conn.close()
        macro_names = [r["id"] for r in results if r["type"] == "macro"]
        assert "ship_arg_s_fighter_01_a_macro" in macro_names

    def test_search_components(self, test_db: Path) -> None:
        conn = sqlite3.connect(test_db)
        conn.row_factory = sqlite3.Row
        results, _ = search(conn, "engine")
        conn.close()
        comp_names = [r["id"] for r in results if r["type"] == "component"]
        assert "engine_test_mk1" in comp_names

    def test_search_with_type_filter(self, test_db: Path) -> None:
        conn = sqlite3.connect(test_db)
        conn.row_factory = sqlite3.Row
        results, _ = search(conn, "ship", type_filter="ware")
        conn.close()
        types = {r["type"] for r in results}
        assert types == {"ware"}

    def test_empty_query_returns_empty(self, test_db: Path) -> None:
        conn = sqlite3.connect(test_db)
        conn.row_factory = sqlite3.Row
        results, page = search(conn, "")
        conn.close()
        assert results == []
        assert page.total_rows == 0

    def test_like_wildcards_escaped(self, test_db: Path) -> None:
        conn = sqlite3.connect(test_db)
        conn.row_factory = sqlite3.Row
        results, _ = search(conn, "%")
        conn.close()
        assert results == []

    def test_pagination(self, test_db: Path) -> None:
        conn = sqlite3.connect(test_db)
        conn.row_factory = sqlite3.Row
        # "s" matches multiple fixtures across all tables
        results, page = search(conn, "s", page=1, per_page=2)
        conn.close()
        assert len(results) == 2
        assert page.total_rows > 2
        assert page.has_next

    def test_pagination_page_2(self, test_db: Path) -> None:
        conn = sqlite3.connect(test_db)
        conn.row_factory = sqlite3.Row
        results_p1, _ = search(conn, "s", page=1, per_page=2)
        results_p2, page = search(conn, "s", page=2, per_page=2)
        conn.close()
        # Pages should have different results
        ids_p1 = {r["id"] for r in results_p1}
        ids_p2 = {r["id"] for r in results_p2}
        assert ids_p1.isdisjoint(ids_p2)
        assert page.has_prev
