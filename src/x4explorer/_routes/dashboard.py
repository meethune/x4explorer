"""Dashboard and search route handlers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from x4explorer._db import get_db

if TYPE_CHECKING:
    from starlette.requests import Request
    from starlette.responses import Response
    from starlette.templating import Jinja2Templates

from x4explorer._pagination import Page, parse_page_params
from x4explorer._queries import get_meta, get_table_counts, search


def _is_htmx_fragment(request: Request) -> bool:
    """Return True if the request expects an HTML fragment."""
    is_htmx = request.headers.get("HX-Request") == "true"
    is_boosted = request.headers.get("HX-Boosted") == "true"
    return is_htmx and not is_boosted


async def dashboard(request: Request) -> Response:
    """Render the dashboard with index stats and search."""
    templates: Jinja2Templates = request.app.state.templates
    conn = get_db()
    context = {
        "request": request,
        "current": "dashboard",
        "game_dir": get_meta(conn, "game_dir"),
        "counts": get_table_counts(conn),
    }
    return templates.TemplateResponse(request, "dashboard.html", context)


async def search_page(request: Request) -> Response:
    """Render search results."""
    templates: Jinja2Templates = request.app.state.templates
    conn = get_db()
    query = request.query_params.get("q", "").strip()
    type_raw = request.query_params.get("type", "")
    type_filter = type_raw if type_raw in ("ware", "macro", "component") else None
    page_num, per_page = parse_page_params(
        request.query_params.get("page"),
        request.query_params.get("per_page"),
    )

    if query:
        results, page_info = search(
            conn, query, type_filter=type_filter, page=page_num, per_page=per_page
        )
    else:
        results = []
        page_info = Page(number=1, per_page=per_page, total_rows=0)

    context = {
        "request": request,
        "current": "search",
        "query": query,
        "type_filter": type_filter or "all",
        "results": results,
        "page": page_info,
    }

    if _is_htmx_fragment(request):
        response = templates.TemplateResponse(request, "_search_results.html", context)
    else:
        response = templates.TemplateResponse(request, "search.html", context)
    response.headers["Vary"] = "HX-Request"
    return response
