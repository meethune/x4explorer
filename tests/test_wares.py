"""Tests for ware list and detail routes."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from starlette.testclient import TestClient


class TestWareList:
    def test_returns_200(self, client: TestClient) -> None:
        response = client.get("/wares")
        assert response.status_code == 200

    def test_contains_ware_ids(self, client: TestClient) -> None:
        response = client.get("/wares")
        assert "energycells" in response.text
        assert "advancedcomposites" in response.text

    def test_pagination(self, client: TestClient) -> None:
        response = client.get("/wares?per_page=10")
        assert response.status_code == 200
        assert "Page 1" in response.text

    def test_page_2(self, client: TestClient) -> None:
        response = client.get("/wares?per_page=10&page=2")
        assert response.status_code == 200
        assert "Page 2" in response.text

    def test_filter_by_group(self, client: TestClient) -> None:
        response = client.get("/wares?group=energy")
        assert response.status_code == 200
        assert "energycells" in response.text
        assert "advancedcomposites" not in response.text

    def test_filter_by_transport(self, client: TestClient) -> None:
        response = client.get("/wares?transport=solid")
        assert response.status_code == 200
        assert "ore" in response.text
        assert "energycells" not in response.text

    def test_filter_by_tag(self, client: TestClient) -> None:
        response = client.get("/wares?tag=ship")
        assert response.status_code == 200
        assert "ship_arg_s_fighter_01_a" in response.text
        assert "energycells" not in response.text

    def test_filter_by_search(self, client: TestClient) -> None:
        response = client.get("/wares?q=energy")
        assert response.status_code == 200
        assert "energycells" in response.text

    def test_sort_by_price(self, client: TestClient) -> None:
        response = client.get("/wares?sort=price_avg&dir=desc&per_page=100")
        assert response.status_code == 200
        # ship_arg should appear before energycells when sorted by price desc
        text = response.text
        ship_pos = text.index("ship_arg_s_fighter_01_a")
        energy_pos = text.index("energycells")
        assert ship_pos < energy_pos

    def test_invalid_sort_column_ignored(self, client: TestClient) -> None:
        response = client.get("/wares?sort=malicious_col")
        assert response.status_code == 200

    def test_htmx_returns_partial(self, client: TestClient) -> None:
        response = client.get("/wares", headers={"HX-Request": "true"})
        assert response.status_code == 200
        assert "<html" not in response.text
        assert "energycells" in response.text

    def test_htmx_boosted_returns_full_page(self, client: TestClient) -> None:
        response = client.get(
            "/wares",
            headers={"HX-Request": "true", "HX-Boosted": "true"},
        )
        assert response.status_code == 200
        assert "<html" in response.text


class TestWareDetail:
    def test_returns_200(self, client: TestClient) -> None:
        response = client.get("/wares/energycells")
        assert response.status_code == 200

    def test_contains_price_data(self, client: TestClient) -> None:
        response = client.get("/wares/energycells")
        assert "16" in response.text  # price_avg

    def test_contains_owners(self, client: TestClient) -> None:
        response = client.get("/wares/energycells")
        assert "argon" in response.text
        assert "teladi" in response.text

    def test_contains_macro_link(self, client: TestClient) -> None:
        response = client.get("/wares/ship_arg_s_fighter_01_a")
        assert "ship_arg_s_fighter_01_a_macro" in response.text
        assert "/macros/" in response.text

    def test_missing_ware_returns_404(self, client: TestClient) -> None:
        response = client.get("/wares/nonexistent")
        assert response.status_code == 404
