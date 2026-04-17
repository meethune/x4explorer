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
            name_resolved TEXT DEFAULT '',
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
            ('energycells', '{20201,301}', 'Energy Cells', 'energy',
             'container', 6, 'container economy', 10, 16, 22);
        INSERT INTO wares VALUES
            ('ship_arg_s_fighter_01_a', '{20101,200}', 'Argon Fighter',
             'ships_argon', 'ship', 1, 'ship', 100000, 130000, 160000);
        INSERT INTO wares VALUES
            ('advancedcomposites', '{20201,401}', 'Advanced Composites',
             'hightech', 'container', 32, 'container economy', 432, 540, 648);
        INSERT INTO wares VALUES
            ('antimattercells', '{20201,201}', 'Antimatter Cells',
             'refined', 'container', 18, 'container economy', 121, 202, 282);
        INSERT INTO wares VALUES
            ('claytronics', '{20201,501}', 'Claytronics',
             'hightech', 'container', 60, 'container economy', 1276, 1594, 1912);
        INSERT INTO wares VALUES
            ('graphene', '{20201,601}', 'Graphene',
             'refined', 'container', 20, 'container economy', 66, 110, 154);
        INSERT INTO wares VALUES
            ('hullparts', '{20201,701}', 'Hull Parts',
             'shiptech', 'container', 24, 'container economy', 138, 230, 322);
        INSERT INTO wares VALUES
            ('microchips', '{20201,801}', 'Microchips',
             'shiptech', 'container', 22, 'container economy', 28, 46, 64);
        INSERT INTO wares VALUES
            ('ore', '{20201,901}', 'Ore',
             'minerals', 'solid', 10, 'container economy', 30, 50, 70);
        INSERT INTO wares VALUES
            ('silicon', '{20201,1001}', 'Silicon',
             'minerals', 'solid', 10, 'container economy', 67, 134, 201);
        INSERT INTO wares VALUES
            ('water', '{20201,1101}', 'Water',
             'ice', 'liquid', 6, 'container economy', 18, 32, 46);
        INSERT INTO wares VALUES
            ('wheat', '{20201,1201}', 'Wheat',
             'agricultural', 'container', 6, 'container economy', 6, 12, 18);
        INSERT INTO wares VALUES
            ('engine_arg_s_allround_01_mk1', '{20107,100}', 'Allround Engine Mk1',
             'engines', 'equipment', 1, 'engine equipment', 1000, 1500, 2000);
        INSERT INTO wares VALUES
            ('shield_arg_s_standard_01_mk1', '{20108,100}', 'Standard Shield Mk1',
             'shields', 'equipment', 1, 'shield equipment', 800, 1200, 1600);
        INSERT INTO wares VALUES
            ('missile_guided_mk1', '{20110,100}', 'Guided Missile Mk1',
             'missiles', 'equipment', 1, 'missile', 50, 75, 100);

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

        -- Script datatypes (inheritance chain: ship -> container -> component)
        CREATE TABLE script_datatypes (
            name TEXT PRIMARY KEY, base_type TEXT,
            suffix TEXT, is_pseudo INTEGER DEFAULT 0
        );
        CREATE TABLE script_keywords (
            name TEXT PRIMARY KEY, description TEXT DEFAULT '',
            type TEXT, script TEXT DEFAULT 'any'
        );
        CREATE TABLE script_properties (
            owner_name TEXT NOT NULL, owner_kind TEXT NOT NULL,
            prop_name TEXT NOT NULL, result_desc TEXT DEFAULT '',
            result_type TEXT,
            PRIMARY KEY (owner_name, owner_kind, prop_name)
        );

        INSERT INTO script_datatypes VALUES ('component', NULL, NULL, 0);
        INSERT INTO script_datatypes VALUES ('destructible', 'component', NULL, 0);
        INSERT INTO script_datatypes VALUES ('object', 'destructible', NULL, 0);
        INSERT INTO script_datatypes VALUES ('controllable', 'object', NULL, 0);
        INSERT INTO script_datatypes VALUES ('container', 'controllable', NULL, 0);
        INSERT INTO script_datatypes VALUES ('ship', 'container', NULL, 0);
        INSERT INTO script_datatypes VALUES ('station', 'container', NULL, 0);
        INSERT INTO script_datatypes VALUES ('integer', NULL, NULL, 1);
        INSERT INTO script_datatypes VALUES ('boolean', NULL, NULL, 1);

        -- Script properties for datatypes
        INSERT INTO script_properties VALUES
            ('component', 'datatype', 'exists', 'true iff exists', 'boolean');
        INSERT INTO script_properties VALUES
            ('component', 'datatype', 'name', 'the name', 'string');
        INSERT INTO script_properties VALUES
            ('ship', 'datatype', 'speed', 'current speed', 'integer');
        INSERT INTO script_properties VALUES
            ('ship', 'datatype', 'pilot', 'the pilot', 'controllable');
        INSERT INTO script_properties VALUES
            ('container', 'datatype', 'cargo', 'cargo list', 'string');
        INSERT INTO script_properties VALUES
            ('controllable', 'datatype', 'owner', 'the owner', 'entity');

        -- Script keywords
        INSERT INTO script_keywords VALUES
            ('player', 'Player data', 'entity', 'any');
        INSERT INTO script_keywords VALUES
            ('this', 'Current entity', 'component', 'md');
        INSERT INTO script_keywords VALUES
            ('event', 'Event info', NULL, 'ai');

        -- Script properties for keywords
        INSERT INTO script_properties VALUES
            ('player', 'keyword', 'money', 'player credits', 'integer');
        INSERT INTO script_properties VALUES
            ('this', 'keyword', 'ship', 'the ship', 'ship');

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
