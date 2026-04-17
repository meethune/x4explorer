"""Macro list and detail route handlers."""

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
    _MACRO_SORT_COLUMNS,
    get_macro,
    get_macro_filter_options,
    get_macro_properties,
    get_macro_ware,
    list_macros,
)


async def macro_list(request: Request) -> Response:
    """Render paginated macro list with filters."""
    templates: Jinja2Templates = request.app.state.templates
    conn = get_db()

    page_num, per_page = parse_page_params(
        request.query_params.get("page"),
        request.query_params.get("per_page"),
    )

    macro_class = request.query_params.get("class", "").strip() or None
    query = request.query_params.get("q", "").strip() or None
    sort, direction = parse_sort_params(
        request.query_params.get("sort"),
        request.query_params.get("dir"),
        allowed=_MACRO_SORT_COLUMNS,
        default="name",
    )

    macros, page_info = list_macros(
        conn,
        macro_class=macro_class,
        query=query,
        sort=sort,
        direction=direction,
        page=page_num,
        per_page=per_page,
    )
    filter_options = get_macro_filter_options(conn)

    context = {
        "request": request,
        "current": "macros",
        "macros": macros,
        "page": page_info,
        "filters": filter_options,
        "macro_class": macro_class or "",
        "query": query or "",
        "sort": sort,
        "dir": direction,
    }

    if _is_htmx_fragment(request):
        response = templates.TemplateResponse(request, "macros/_table.html", context)
    else:
        response = templates.TemplateResponse(request, "macros/list.html", context)
    response.headers["Vary"] = "HX-Request"
    return response


async def macro_detail(request: Request) -> Response:
    """Render macro detail page."""
    from starlette.responses import Response as StarletteResponse

    templates: Jinja2Templates = request.app.state.templates
    conn = get_db()
    name = request.path_params["name"]

    macro = get_macro(conn, name)
    if macro is None:
        return StarletteResponse("Macro not found", status_code=404)

    properties = get_macro_properties(conn, name)
    props_dict = {p["property_key"]: p["property_val"] for p in properties}
    component_ref = props_dict.get("component_ref")
    ware_id = get_macro_ware(conn, name)

    context = {
        "request": request,
        "current": "macros",
        "macro": macro,
        "properties": properties,
        "component_ref": component_ref,
        "ware_id": ware_id,
    }
    return templates.TemplateResponse(request, "macros/detail.html", context)
