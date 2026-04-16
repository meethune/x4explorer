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

        -- Wares (enough for pagination: 15 total)
        INSERT INTO wares VALUES
            ('energycells', '{20201,301}', 'energy', 'container',
             6, 'container economy', 10, 16, 22);
        INSERT INTO wares VALUES
            ('ship_arg_s_fighter_01_a', '{20101,200}', 'ships_argon', 'ship',
             1, 'ship', 100000, 130000, 160000);
        INSERT INTO wares VALUES
            ('advancedcomposites', '{20201,401}', 'hightech', 'container',
             32, 'container economy', 432, 540, 648);
        INSERT INTO wares VALUES
            ('antimattercells', '{20201,201}', 'refined', 'container',
             18, 'container economy', 121, 202, 282);
        INSERT INTO wares VALUES
            ('claytronics', '{20201,501}', 'hightech', 'container',
             60, 'container economy', 1276, 1594, 1912);
        INSERT INTO wares VALUES
            ('graphene', '{20201,601}', 'refined', 'container',
             20, 'container economy', 66, 110, 154);
        INSERT INTO wares VALUES
            ('hullparts', '{20201,701}', 'shiptech', 'container',
             24, 'container economy', 138, 230, 322);
        INSERT INTO wares VALUES
            ('microchips', '{20201,801}', 'shiptech', 'container',
             22, 'container economy', 28, 46, 64);
        INSERT INTO wares VALUES
            ('ore', '{20201,901}', 'minerals', 'solid',
             10, 'container economy', 30, 50, 70);
        INSERT INTO wares VALUES
            ('silicon', '{20201,1001}', 'minerals', 'solid',
             10, 'container economy', 67, 134, 201);
        INSERT INTO wares VALUES
            ('water', '{20201,1101}', 'ice', 'liquid',
             6, 'container economy', 18, 32, 46);
        INSERT INTO wares VALUES
            ('wheat', '{20201,1201}', 'agricultural', 'container',
             6, 'container economy', 6, 12, 18);
        INSERT INTO wares VALUES
            ('engine_arg_s_allround_01_mk1', '{20107,100}', 'engines',
             'equipment', 1, 'engine equipment', 1000, 1500, 2000);
        INSERT INTO wares VALUES
            ('shield_arg_s_standard_01_mk1', '{20108,100}', 'shields',
             'equipment', 1, 'shield equipment', 800, 1200, 1600);
        INSERT INTO wares VALUES
            ('missile_guided_mk1', '{20110,100}', 'missiles',
             'equipment', 1, 'missile', 50, 75, 100);

        -- Ware owners
        INSERT INTO ware_owners VALUES ('energycells', 'argon');
        INSERT INTO ware_owners VALUES ('energycells', 'teladi');
        INSERT INTO ware_owners VALUES ('ship_arg_s_fighter_01_a', 'argon');

        -- Macros (enough for pagination and class filter testing)
        INSERT INTO macros VALUES
            ('ship_arg_s_fighter_01_a_macro',
             'assets/units/size_s/macros/ship_arg_s_fighter_01_a_macro');
        INSERT INTO macros VALUES
            ('ship_arg_m_bomber_01_a_macro',
             'assets/units/size_m/macros/ship_arg_m_bomber_01_a_macro');
        INSERT INTO macros VALUES
            ('engine_test_mk1_macro',
             'assets/props/engines/macros/engine_test_mk1_macro');
        INSERT INTO macros VALUES
            ('engine_test_mk2_macro',
             'assets/props/engines/macros/engine_test_mk2_macro');
        INSERT INTO macros VALUES
            ('shield_arg_s_standard_01_macro',
             'assets/props/shields/macros/shield_arg_s_standard_01_macro');
        INSERT INTO macros VALUES
            ('weapon_gen_s_laser_01_mk1_macro',
             'assets/props/weapons/macros/weapon_gen_s_laser_01_mk1_macro');
        INSERT INTO macros VALUES
            ('cluster_01_macro',
             'maps/xu_ep2_universe/clusters/cluster_01_macro');
        INSERT INTO macros VALUES
            ('sector_001_macro',
             'maps/xu_ep2_universe/sectors/sector_001_macro');

        -- Macro properties
        INSERT INTO macro_properties VALUES
            ('ship_arg_s_fighter_01_a_macro', 'class', 'ship_s');
        INSERT INTO macro_properties VALUES
            ('ship_arg_s_fighter_01_a_macro', 'component_ref',
             'ship_arg_s_fighter_01');
        INSERT INTO macro_properties VALUES
            ('ship_arg_s_fighter_01_a_macro', 'hull.max', '3100');
        INSERT INTO macro_properties VALUES
            ('ship_arg_s_fighter_01_a_macro', 'purpose.primary', 'fight');
        INSERT INTO macro_properties VALUES
            ('ship_arg_m_bomber_01_a_macro', 'class', 'ship_m');
        INSERT INTO macro_properties VALUES
            ('ship_arg_m_bomber_01_a_macro', 'component_ref',
             'ship_arg_m_bomber_01');
        INSERT INTO macro_properties VALUES
            ('engine_test_mk1_macro', 'class', 'engine');
        INSERT INTO macro_properties VALUES
            ('engine_test_mk1_macro', 'component_ref', 'engine_test_mk1');
        INSERT INTO macro_properties VALUES
            ('engine_test_mk2_macro', 'class', 'engine');
        INSERT INTO macro_properties VALUES
            ('engine_test_mk2_macro', 'component_ref', 'engine_test_mk2');
        INSERT INTO macro_properties VALUES
            ('shield_arg_s_standard_01_macro', 'class', 'shieldgenerator');
        INSERT INTO macro_properties VALUES
            ('shield_arg_s_standard_01_macro', 'component_ref',
             'shield_arg_s_standard_01');
        INSERT INTO macro_properties VALUES
            ('weapon_gen_s_laser_01_mk1_macro', 'class', 'weapon');
        INSERT INTO macro_properties VALUES
            ('weapon_gen_s_laser_01_mk1_macro', 'component_ref',
             'weapon_gen_s_laser_01_mk1');
        INSERT INTO macro_properties VALUES
            ('cluster_01_macro', 'class', 'cluster');
        INSERT INTO macro_properties VALUES
            ('sector_001_macro', 'class', 'sector');

        -- Components
        INSERT INTO components VALUES
            ('ship_arg_s_fighter_01',
             'assets/units/size_s/ship_arg_s_fighter_01');
        INSERT INTO components VALUES
            ('ship_arg_m_bomber_01',
             'assets/units/size_m/ship_arg_m_bomber_01');
        INSERT INTO components VALUES
            ('engine_test_mk1',
             'assets/props/engines/engine_test_mk1');
        INSERT INTO components VALUES
            ('engine_test_mk2',
             'assets/props/engines/engine_test_mk2');
        INSERT INTO components VALUES
            ('shield_arg_s_standard_01',
             'assets/props/shields/shield_arg_s_standard_01');
        INSERT INTO components VALUES
            ('weapon_gen_s_laser_01_mk1',
             'assets/props/weapons/weapon_gen_s_laser_01_mk1');

        -- Game files
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
