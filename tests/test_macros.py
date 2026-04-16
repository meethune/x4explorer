"""Tests for macro list and detail routes."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from starlette.testclient import TestClient


class TestMacroList:
    def test_returns_200(self, client: TestClient) -> None:
        response = client.get("/macros")
        assert response.status_code == 200

    def test_contains_macro_names(self, client: TestClient) -> None:
        response = client.get("/macros")
        assert "ship_arg_s_fighter_01_a_macro" in response.text
        assert "engine_test_mk1_macro" in response.text

    def test_contains_class_column(self, client: TestClient) -> None:
        response = client.get("/macros")
        assert "ship_s" in response.text

    def test_filter_by_class(self, client: TestClient) -> None:
        response = client.get("/macros?class=engine")
        assert response.status_code == 200
        assert "engine_test_mk1_macro" in response.text
        assert "ship_arg_s_fighter_01_a_macro" not in response.text

    def test_filter_by_search(self, client: TestClient) -> None:
        response = client.get("/macros?q=fighter")
        assert response.status_code == 200
        assert "ship_arg_s_fighter_01_a_macro" in response.text
        assert "engine_test_mk1_macro" not in response.text

    def test_pagination(self, client: TestClient) -> None:
        response = client.get("/macros?per_page=10")
        assert response.status_code == 200

    def test_sort_by_name(self, client: TestClient) -> None:
        response = client.get("/macros?sort=name&dir=desc&per_page=100")
        assert response.status_code == 200
        text = response.text
        weapon_pos = text.index("weapon_gen_s_laser_01_mk1_macro")
        cluster_pos = text.index("cluster_01_macro")
        assert weapon_pos < cluster_pos

    def test_invalid_sort_column_ignored(self, client: TestClient) -> None:
        response = client.get("/macros?sort=malicious")
        assert response.status_code == 200

    def test_htmx_returns_partial(self, client: TestClient) -> None:
        response = client.get("/macros", headers={"HX-Request": "true"})
        assert response.status_code == 200
        assert "<html" not in response.text
        assert "ship_arg_s_fighter_01_a_macro" in response.text

    def test_htmx_boosted_returns_full_page(self, client: TestClient) -> None:
        response = client.get(
            "/macros",
            headers={"HX-Request": "true", "HX-Boosted": "true"},
        )
        assert response.status_code == 200
        assert "<html" in response.text


class TestMacroDetail:
    def test_returns_200(self, client: TestClient) -> None:
        response = client.get("/macros/ship_arg_s_fighter_01_a_macro")
        assert response.status_code == 200

    def test_contains_properties(self, client: TestClient) -> None:
        response = client.get("/macros/ship_arg_s_fighter_01_a_macro")
        assert "hull.max" in response.text
        assert "3100" in response.text

    def test_contains_class(self, client: TestClient) -> None:
        response = client.get("/macros/ship_arg_s_fighter_01_a_macro")
        assert "ship_s" in response.text

    def test_contains_component_link(self, client: TestClient) -> None:
        response = client.get("/macros/ship_arg_s_fighter_01_a_macro")
        assert "/components/ship_arg_s_fighter_01" in response.text

    def test_contains_ware_link(self, client: TestClient) -> None:
        response = client.get("/macros/ship_arg_s_fighter_01_a_macro")
        assert "/wares/" in response.text

    def test_contains_file_path(self, client: TestClient) -> None:
        response = client.get("/macros/ship_arg_s_fighter_01_a_macro")
        assert "assets/units/size_s/macros/ship_arg_s_fighter_01_a_macro" in response.text

    def test_missing_macro_returns_404(self, client: TestClient) -> None:
        response = client.get("/macros/nonexistent")
        assert response.status_code == 404
