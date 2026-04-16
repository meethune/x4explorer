"""Test fixtures for x4explorer."""

from __future__ import annotations

import sqlite3
from typing import TYPE_CHECKING

import pytest
from starlette.testclient import TestClient

from x4explorer._app import create_app

if TYPE_CHECKING:
    from pathlib import Path


def _create_test_db(path: Path) -> None:
    """Create a test database matching x4cat's index schema."""
    conn = sqlite3.connect(path)
    conn.executescript("""
        CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
        CREATE TABLE macros (name TEXT PRIMARY KEY, value TEXT NOT NULL);
        CREATE TABLE components (name TEXT PRIMARY KEY, value TEXT NOT NULL);
        CREATE TABLE wares (
            ware_id TEXT PRIMARY KEY, name_ref TEXT DEFAULT '',
            ware_group TEXT DEFAULT '', transport TEXT DEFAULT '',
            volume INTEGER DEFAULT 0, tags TEXT DEFAULT '',
            price_min INTEGER DEFAULT 0, price_avg INTEGER DEFAULT 0,
            price_max INTEGER DEFAULT 0
        );
        CREATE TABLE ware_owners (
            ware_id TEXT NOT NULL, faction TEXT NOT NULL,
            PRIMARY KEY (ware_id, faction),
            FOREIGN KEY (ware_id) REFERENCES wares(ware_id)
        );
        CREATE TABLE macro_properties (
            macro_name TEXT NOT NULL, property_key TEXT NOT NULL,
            property_val TEXT DEFAULT '',
            PRIMARY KEY (macro_name, property_key),
            FOREIGN KEY (macro_name) REFERENCES macros(name)
        );
        CREATE TABLE game_files (
            virtual_path TEXT PRIMARY KEY, size INTEGER,
            mtime INTEGER, md5 TEXT
        );

        INSERT INTO meta VALUES ('game_dir', '/test/X4 Foundations');
    """)
    conn.commit()
    conn.close()


@pytest.fixture()
def test_db(tmp_path: Path) -> Path:
    """Create a test database and return its path."""
    db_path = tmp_path / "test.db"
    _create_test_db(db_path)
    return db_path


@pytest.fixture()
def client(test_db: Path) -> TestClient:
    """Create a test client with a populated database."""
    app = create_app(test_db)
    with TestClient(app) as c:
        yield c  # type: ignore[misc]
