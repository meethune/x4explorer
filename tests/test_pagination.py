"""Tests for pagination helpers."""

from __future__ import annotations

from x4explorer._pagination import Page, parse_page_params, parse_sort_params


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

    def test_page_clamped_to_upper_bound(self) -> None:
        page = Page(number=999, per_page=10, total_rows=25)
        assert page.number == 3
        assert not page.has_next


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


class TestParseSortParams:
    def test_valid_sort(self) -> None:
        sort, direction = parse_sort_params(
            "name", "asc", allowed=frozenset({"name", "value"}), default="name"
        )
        assert sort == "name"
        assert direction == "asc"

    def test_invalid_sort_uses_default(self) -> None:
        sort, _ = parse_sort_params(
            "malicious", None, allowed=frozenset({"name", "value"}), default="name"
        )
        assert sort == "name"

    def test_none_sort_uses_default(self) -> None:
        sort, _ = parse_sort_params(None, None, allowed=frozenset({"name"}), default="name")
        assert sort == "name"

    def test_invalid_direction_uses_asc(self) -> None:
        _, direction = parse_sort_params(
            "name", "DROP TABLE", allowed=frozenset({"name"}), default="name"
        )
        assert direction == "asc"

    def test_direction_case_insensitive(self) -> None:
        _, direction = parse_sort_params(
            "name", "DESC", allowed=frozenset({"name"}), default="name"
        )
        assert direction == "desc"
