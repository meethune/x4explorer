"""Ware list and detail route handlers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from x4explorer._db import get_db
from x4explorer._pagination import parse_page_params
from x4explorer._routes.dashboard import _is_htmx_fragment

if TYPE_CHECKING:
    from starlette.requests import Request
    from starlette.responses import Response
    from starlette.templating import Jinja2Templates

from x4explorer._queries import (
    get_ware,
    get_ware_filter_options,
    get_ware_macro,
    get_ware_owners,
    list_wares,
)


async def ware_list(request: Request) -> Response:
    """Render paginated ware list with filters."""
    templates: Jinja2Templates = request.app.state.templates
    conn = get_db()

    page_num, per_page = parse_page_params(
        request.query_params.get("page"),
        request.query_params.get("per_page"),
    )

    group = request.query_params.get("group", "").strip() or None
    transport = request.query_params.get("transport", "").strip() or None
    tag = request.query_params.get("tag", "").strip() or None
    query = request.query_params.get("q", "").strip() or None
    sort = request.query_params.get("sort", "ware_id")
    direction = request.query_params.get("dir", "asc")

    wares, page_info = list_wares(
        conn,
        group=group,
        transport=transport,
        tag=tag,
        query=query,
        sort=sort,
        direction=direction,
        page=page_num,
        per_page=per_page,
    )
    filter_options = get_ware_filter_options(conn)

    context = {
        "request": request,
        "current": "wares",
        "wares": wares,
        "page": page_info,
        "filters": filter_options,
        "group": group or "",
        "transport": transport or "",
        "tag": tag or "",
        "query": query or "",
        "sort": sort,
        "dir": direction,
    }

    if _is_htmx_fragment(request):
        response = templates.TemplateResponse(request, "wares/_table.html", context)
    else:
        response = templates.TemplateResponse(request, "wares/list.html", context)
    response.headers["Vary"] = "HX-Request"
    return response


async def ware_detail(request: Request) -> Response:
    """Render ware detail page."""
    from starlette.responses import Response as StarletteResponse

    templates: Jinja2Templates = request.app.state.templates
    conn = get_db()
    ware_id = request.path_params["ware_id"]

    ware = get_ware(conn, ware_id)
    if ware is None:
        return StarletteResponse("Ware not found", status_code=404)

    owners = get_ware_owners(conn, ware_id)
    macro_name = get_ware_macro(conn, ware_id)

    context = {
        "request": request,
        "current": "wares",
        "ware": ware,
        "owners": owners,
        "macro_name": macro_name,
    }
    return templates.TemplateResponse(request, "wares/detail.html", context)
