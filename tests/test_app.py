"""Smoke test — does the app start and serve."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from starlette.testclient import TestClient


def test_index_returns_200(client: TestClient) -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "x4explorer" in response.text
