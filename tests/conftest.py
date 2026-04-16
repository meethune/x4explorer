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

        -- Wares
        INSERT INTO wares VALUES
            ('energycells', '{20201,301}', 'energy', 'container',
             6, 'container economy', 10, 16, 22);
        INSERT INTO wares VALUES
            ('ship_arg_s_fighter_01_a', '{20101,200}', 'ships_argon', 'ship',
             1, 'ship', 100000, 130000, 160000);
        INSERT INTO wares VALUES
            ('advancedcomposites', '{20201,401}', 'hightech', 'container',
             32, 'container economy', 432, 540, 648);

        -- Ware owners
        INSERT INTO ware_owners VALUES ('energycells', 'argon');
        INSERT INTO ware_owners VALUES ('energycells', 'teladi');

        -- Macros
        INSERT INTO macros VALUES
            ('ship_arg_s_fighter_01_a_macro',
             'assets/units/size_s/macros/ship_arg_s_fighter_01_a_macro');
        INSERT INTO macros VALUES
            ('engine_test_mk1_macro',
             'assets/props/engines/macros/engine_test_mk1_macro');

        -- Macro properties
        INSERT INTO macro_properties VALUES
            ('ship_arg_s_fighter_01_a_macro', 'class', 'ship_s');
        INSERT INTO macro_properties VALUES
            ('ship_arg_s_fighter_01_a_macro', 'component_ref', 'ship_arg_s_fighter_01');

        -- Components
        INSERT INTO components VALUES
            ('ship_arg_s_fighter_01',
             'assets/units/size_s/ship_arg_s_fighter_01');
        INSERT INTO components VALUES
            ('engine_test_mk1',
             'assets/props/engines/engine_test_mk1');

        -- Game files (a few for count testing)
        INSERT INTO game_files VALUES ('index/macros.xml', 1000, 1000000, 'abc');
        INSERT INTO game_files VALUES ('index/components.xml', 500, 1000000, 'def');
        INSERT INTO game_files VALUES ('libraries/wares.xml', 2000, 1000000, 'ghi');
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
