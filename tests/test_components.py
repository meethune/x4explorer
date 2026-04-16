"""Tests for component list and detail routes."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from starlette.testclient import TestClient


class TestComponentList:
    def test_returns_200(self, client: TestClient) -> None:
        response = client.get("/components")
        assert response.status_code == 200

    def test_contains_component_names(self, client: TestClient) -> None:
        response = client.get("/components")
        assert "ship_arg_s_fighter_01" in response.text
        assert "engine_test_mk1" in response.text

    def test_contains_file_paths(self, client: TestClient) -> None:
        response = client.get("/components")
        assert "assets/units/size_s/ship_arg_s_fighter_01" in response.text

    def test_filter_by_search(self, client: TestClient) -> None:
        response = client.get("/components?q=engine")
        assert response.status_code == 200
        assert "engine_test_mk1" in response.text
        assert "ship_arg_s_fighter_01" not in response.text

    def test_pagination(self, client: TestClient) -> None:
        response = client.get("/components?per_page=10")
        assert response.status_code == 200

    def test_sort_by_name(self, client: TestClient) -> None:
        response = client.get("/components?sort=name&dir=desc&per_page=100")
        assert response.status_code == 200
        text = response.text
        weapon_pos = text.index("weapon_gen_s_laser_01_mk1")
        engine_pos = text.index("engine_test_mk1")
        assert weapon_pos < engine_pos

    def test_htmx_returns_partial(self, client: TestClient) -> None:
        response = client.get("/components", headers={"HX-Request": "true"})
        assert response.status_code == 200
        assert "<html" not in response.text

    def test_htmx_boosted_returns_full_page(self, client: TestClient) -> None:
        response = client.get(
            "/components",
            headers={"HX-Request": "true", "HX-Boosted": "true"},
        )
        assert response.status_code == 200
        assert "<html" in response.text


class TestComponentDetail:
    def test_returns_200(self, client: TestClient) -> None:
        response = client.get("/components/ship_arg_s_fighter_01")
        assert response.status_code == 200

    def test_contains_file_path(self, client: TestClient) -> None:
        response = client.get("/components/ship_arg_s_fighter_01")
        assert "assets/units/size_s/ship_arg_s_fighter_01" in response.text

    def test_contains_referencing_macros(self, client: TestClient) -> None:
        response = client.get("/components/ship_arg_s_fighter_01")
        assert "ship_arg_s_fighter_01_a_macro" in response.text
        assert "/macros/" in response.text

    def test_missing_component_returns_404(self, client: TestClient) -> None:
        response = client.get("/components/nonexistent")
        assert response.status_code == 404
