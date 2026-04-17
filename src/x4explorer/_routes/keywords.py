"""Keyword list and detail route handlers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from x4explorer._db import get_db
from x4explorer._pagination import parse_page_params, parse_sort_params
from x4explorer._routes.dashboard import _is_htmx_fragment

if TYPE_CHECKING:
    from starlette.requests import Request
    from starlette.responses import Response
    from starlette.templating import Jinja2Templates

from x4explorer._queries import (
    _KEYWORD_SORT_COLUMNS,
    get_all_datatype_names,
    get_keyword,
    get_keyword_filter_options,
    get_keyword_properties,
    list_keywords,
)


async def keyword_list(request: Request) -> Response:
    """Render paginated keyword list with filters."""
    templates: Jinja2Templates = request.app.state.templates
    conn = get_db()

    page_num, per_page = parse_page_params(
        request.query_params.get("page"),
        request.query_params.get("per_page"),
    )

    script = request.query_params.get("script", "").strip() or None
    query = request.query_params.get("q", "").strip() or None
    sort, direction = parse_sort_params(
        request.query_params.get("sort"),
        request.query_params.get("dir"),
        allowed=_KEYWORD_SORT_COLUMNS,
        default="name",
    )

    keywords, page_info = list_keywords(
        conn,
        script=script,
        query=query,
        sort=sort,
        direction=direction,
        page=page_num,
        per_page=per_page,
    )
    filter_options = get_keyword_filter_options(conn)

    context = {
        "request": request,
        "current": "keywords",
        "keywords": keywords,
        "page": page_info,
        "filters": filter_options,
        "script": script or "",
        "query": query or "",
        "sort": sort,
        "dir": direction,
    }

    if _is_htmx_fragment(request):
        response = templates.TemplateResponse(request, "scripts/_keywords_table.html", context)
    else:
        response = templates.TemplateResponse(request, "scripts/keywords.html", context)
    response.headers["Vary"] = "HX-Request"
    return response


async def keyword_detail(request: Request) -> Response:
    """Render keyword detail with properties."""
    from starlette.responses import Response as StarletteResponse

    templates: Jinja2Templates = request.app.state.templates
    conn = get_db()
    name = request.path_params["name"]

    keyword = get_keyword(conn, name)
    if keyword is None:
        return StarletteResponse("Keyword not found", status_code=404)

    properties = get_keyword_properties(conn, name)
    all_datatype_names = get_all_datatype_names(conn)

    context = {
        "request": request,
        "current": "keywords",
        "keyword": keyword,
        "properties": properties,
        "all_datatype_names": all_datatype_names,
    }
    return templates.TemplateResponse(request, "scripts/keyword_detail.html", context)
