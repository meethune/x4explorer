"""Tests for script datatypes and keywords routes."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from starlette.testclient import TestClient


class TestDatatypeList:
    def test_returns_200(self, client: TestClient) -> None:
        response = client.get("/scripts/datatypes")
        assert response.status_code == 200

    def test_contains_datatype_names(self, client: TestClient) -> None:
        response = client.get("/scripts/datatypes")
        assert "ship" in response.text
        assert "component" in response.text

    def test_contains_base_type(self, client: TestClient) -> None:
        response = client.get("/scripts/datatypes?per_page=100")
        assert "container" in response.text

    def test_filter_by_base_type(self, client: TestClient) -> None:
        response = client.get("/scripts/datatypes?base_type=component")
        assert response.status_code == 200
        assert "destructible" in response.text
        assert "ship" not in response.text

    def test_filter_by_search(self, client: TestClient) -> None:
        response = client.get("/scripts/datatypes?q=ship")
        assert response.status_code == 200
        assert "ship" in response.text

    def test_sort_by_name(self, client: TestClient) -> None:
        response = client.get("/scripts/datatypes?sort=name&dir=desc&per_page=100")
        assert response.status_code == 200
        text = response.text
        # In desc order, "station" comes before "object" in the table body
        station_pos = text.index("/scripts/datatypes/station")
        object_pos = text.index("/scripts/datatypes/object")
        assert station_pos < object_pos

    def test_htmx_returns_partial(self, client: TestClient) -> None:
        response = client.get("/scripts/datatypes", headers={"HX-Request": "true"})
        assert response.status_code == 200
        assert "<html" not in response.text

    def test_htmx_boosted_returns_full_page(self, client: TestClient) -> None:
        response = client.get(
            "/scripts/datatypes",
            headers={"HX-Request": "true", "HX-Boosted": "true"},
        )
        assert response.status_code == 200
        assert "<html" in response.text


class TestDatatypeDetail:
    def test_returns_200(self, client: TestClient) -> None:
        response = client.get("/scripts/datatypes/ship")
        assert response.status_code == 200

    def test_contains_own_properties(self, client: TestClient) -> None:
        response = client.get("/scripts/datatypes/ship")
        assert "speed" in response.text
        assert "pilot" in response.text

    def test_contains_inherited_properties(self, client: TestClient) -> None:
        response = client.get("/scripts/datatypes/ship")
        # ship inherits from container -> controllable -> ... -> component
        assert "exists" in response.text  # from component
        assert "cargo" in response.text  # from container

    def test_contains_inheritance_chain(self, client: TestClient) -> None:
        response = client.get("/scripts/datatypes/ship")
        assert "container" in response.text
        assert "component" in response.text

    def test_inheritance_chain_has_links(self, client: TestClient) -> None:
        response = client.get("/scripts/datatypes/ship")
        assert "/scripts/datatypes/container" in response.text

    def test_result_type_links(self, client: TestClient) -> None:
        response = client.get("/scripts/datatypes/ship")
        # pilot property has result_type='controllable' which is a known datatype
        assert "/scripts/datatypes/controllable" in response.text

    def test_missing_returns_404(self, client: TestClient) -> None:
        response = client.get("/scripts/datatypes/nonexistent")
        assert response.status_code == 404


class TestKeywordList:
    def test_returns_200(self, client: TestClient) -> None:
        response = client.get("/scripts/keywords")
        assert response.status_code == 200

    def test_contains_keyword_names(self, client: TestClient) -> None:
        response = client.get("/scripts/keywords")
        assert "player" in response.text
        assert "this" in response.text

    def test_filter_by_script(self, client: TestClient) -> None:
        response = client.get("/scripts/keywords?script=md")
        assert response.status_code == 200
        assert "this" in response.text
        assert "event" not in response.text

    def test_htmx_returns_partial(self, client: TestClient) -> None:
        response = client.get("/scripts/keywords", headers={"HX-Request": "true"})
        assert response.status_code == 200
        assert "<html" not in response.text


class TestKeywordDetail:
    def test_returns_200(self, client: TestClient) -> None:
        response = client.get("/scripts/keywords/player")
        assert response.status_code == 200

    def test_contains_properties(self, client: TestClient) -> None:
        response = client.get("/scripts/keywords/player")
        assert "money" in response.text

    def test_result_type_links(self, client: TestClient) -> None:
        response = client.get("/scripts/keywords/this")
        # 'ship' property has result_type='ship' which is a known datatype
        assert "/scripts/datatypes/ship" in response.text

    def test_missing_returns_404(self, client: TestClient) -> None:
        response = client.get("/scripts/keywords/nonexistent")
        assert response.status_code == 404
