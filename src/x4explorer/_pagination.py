"""Pagination helpers for x4explorer."""

from __future__ import annotations

from dataclasses import dataclass

_VALID_PER_PAGE = (10, 25, 50, 100)
_DEFAULT_PER_PAGE = 10


@dataclass(frozen=True, slots=True)
class Page:
    """Pagination metadata."""

    number: int
    per_page: int
    total_rows: int

    @property
    def total_pages(self) -> int:
        return max(1, (self.total_rows + self.per_page - 1) // self.per_page)

    @property
    def offset(self) -> int:
        return (self.number - 1) * self.per_page

    @property
    def has_prev(self) -> bool:
        return self.number > 1

    @property
    def has_next(self) -> bool:
        return self.number < self.total_pages


def parse_page_params(
    page_raw: str | None,
    per_page_raw: str | None,
) -> tuple[int, int]:
    """Parse and clamp page and per_page from query params.

    Returns (page, per_page) with safe defaults.
    """
    try:
        page = max(1, int(page_raw or "1"))
    except (ValueError, TypeError):
        page = 1

    try:
        per_page = int(per_page_raw) if per_page_raw else _DEFAULT_PER_PAGE
    except (ValueError, TypeError):
        per_page = _DEFAULT_PER_PAGE

    if per_page not in _VALID_PER_PAGE:
        per_page = _DEFAULT_PER_PAGE

    return page, per_page
