"""Tests for the dashboard and search routes."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from starlette.testclient import TestClient


class TestDashboard:
    def test_returns_200(self, client: TestClient) -> None:
        response = client.get("/")
        assert response.status_code == 200

    def test_contains_game_dir(self, client: TestClient) -> None:
        response = client.get("/")
        assert "/test/X4 Foundations" in response.text

    def test_contains_table_counts(self, client: TestClient) -> None:
        response = client.get("/")
        assert "15" in response.text  # wares count
        assert "8" in response.text  # macros count

    def test_contains_nav_links(self, client: TestClient) -> None:
        response = client.get("/")
        text = response.text
        assert 'href="/search"' in text
        assert 'href="/wares"' in text
        assert 'href="/macros"' in text
        assert 'href="/components"' in text
        assert 'href="/conflicts"' in text
        assert 'href="/scripts/datatypes"' in text
        assert 'href="/scripts/keywords"' in text

    def test_contains_search_input(self, client: TestClient) -> None:
        response = client.get("/")
        assert 'type="search"' in response.text


class TestSearch:
    def test_empty_search_returns_200(self, client: TestClient) -> None:
        response = client.get("/search")
        assert response.status_code == 200

    def test_search_returns_results(self, client: TestClient) -> None:
        response = client.get("/search?q=ship")
        assert response.status_code == 200
        assert "ship_arg_s_fighter_01_a" in response.text

    def test_search_results_contain_type(self, client: TestClient) -> None:
        response = client.get("/search?q=energy")
        assert response.status_code == 200
        assert "ware" in response.text

    def test_search_no_results(self, client: TestClient) -> None:
        response = client.get("/search?q=zzzznonexistent")
        assert response.status_code == 200
        assert "No results" in response.text

    def test_search_type_filter(self, client: TestClient) -> None:
        response = client.get("/search?q=ship&type=ware")
        assert response.status_code == 200
        assert "ship_arg_s_fighter_01_a" in response.text

    def test_search_type_all_returns_results(self, client: TestClient) -> None:
        response = client.get("/search?q=energy&type=all")
        assert response.status_code == 200
        assert "energycells" in response.text

    def test_htmx_returns_partial(self, client: TestClient) -> None:
        response = client.get("/search?q=energy", headers={"HX-Request": "true"})
        assert response.status_code == 200
        assert "<html" not in response.text
        assert "energycells" in response.text

    def test_htmx_boosted_returns_full_page(self, client: TestClient) -> None:
        response = client.get(
            "/search?q=energy",
            headers={"HX-Request": "true", "HX-Boosted": "true"},
        )
        assert response.status_code == 200
        assert "<html" in response.text
