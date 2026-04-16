"""Tests for pagination helpers."""

from __future__ import annotations

from x4explorer._pagination import Page, parse_page_params


class TestPage:
    def test_total_pages(self) -> None:
        assert Page(number=1, per_page=10, total_rows=25).total_pages == 3
        assert Page(number=1, per_page=10, total_rows=10).total_pages == 1
        assert Page(number=1, per_page=10, total_rows=0).total_pages == 1

    def test_offset(self) -> None:
        assert Page(number=1, per_page=10, total_rows=50).offset == 0
        assert Page(number=3, per_page=10, total_rows=50).offset == 20

    def test_has_prev(self) -> None:
        assert not Page(number=1, per_page=10, total_rows=50).has_prev
        assert Page(number=2, per_page=10, total_rows=50).has_prev

    def test_has_next(self) -> None:
        assert Page(number=1, per_page=10, total_rows=50).has_next
        assert not Page(number=5, per_page=10, total_rows=50).has_next


class TestParsePageParams:
    def test_defaults(self) -> None:
        page, per_page = parse_page_params(None, None)
        assert page == 1
        assert per_page == 10

    def test_valid_values(self) -> None:
        page, per_page = parse_page_params("3", "25")
        assert page == 3
        assert per_page == 25

    def test_invalid_page_defaults_to_1(self) -> None:
        page, _ = parse_page_params("abc", None)
        assert page == 1

    def test_negative_page_clamps_to_1(self) -> None:
        page, _ = parse_page_params("-5", None)
        assert page == 1

    def test_invalid_per_page_defaults(self) -> None:
        _, per_page = parse_page_params(None, "999")
        assert per_page == 10

    def test_valid_per_page_options(self) -> None:
        for size in (10, 25, 50, 100):
            _, per_page = parse_page_params(None, str(size))
            assert per_page == size

    def test_cookie_fallback(self) -> None:
        _, per_page = parse_page_params(None, None, per_page_cookie="25")
        assert per_page == 25

    def test_query_param_overrides_cookie(self) -> None:
        _, per_page = parse_page_params(None, "50", per_page_cookie="25")
        assert per_page == 50

    def test_invalid_cookie_uses_default(self) -> None:
        _, per_page = parse_page_params(None, None, per_page_cookie="999")
        assert per_page == 10
