"""Component list and detail route handlers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from x4explorer._db import get_db
from x4explorer._pagination import parse_page_params
from x4explorer._routes.dashboard import _is_htmx_fragment

if TYPE_CHECKING:
    from starlette.requests import Request
    from starlette.responses import Response
    from starlette.templating import Jinja2Templates

from x4explorer._queries import get_component, get_component_macros, list_components


async def component_list(request: Request) -> Response:
    """Render paginated component list."""
    templates: Jinja2Templates = request.app.state.templates
    conn = get_db()

    page_num, per_page = parse_page_params(
        request.query_params.get("page"),
        request.query_params.get("per_page"),
    )

    query = request.query_params.get("q", "").strip() or None
    sort = request.query_params.get("sort", "name")
    direction = request.query_params.get("dir", "asc")

    components, page_info = list_components(
        conn,
        query=query,
        sort=sort,
        direction=direction,
        page=page_num,
        per_page=per_page,
    )

    context = {
        "request": request,
        "current": "components",
        "components": components,
        "page": page_info,
        "query": query or "",
        "sort": sort,
        "dir": direction,
    }

    if _is_htmx_fragment(request):
        response = templates.TemplateResponse(request, "components/_table.html", context)
    else:
        response = templates.TemplateResponse(request, "components/list.html", context)
    response.headers["Vary"] = "HX-Request"
    return response


async def component_detail(request: Request) -> Response:
    """Render component detail page."""
    from starlette.responses import Response as StarletteResponse

    templates: Jinja2Templates = request.app.state.templates
    conn = get_db()
    name = request.path_params["name"]

    component = get_component(conn, name)
    if component is None:
        return StarletteResponse("Component not found", status_code=404)

    referencing_macros = get_component_macros(conn, name)

    context = {
        "request": request,
        "current": "components",
        "component": component,
        "referencing_macros": referencing_macros,
    }
    return templates.TemplateResponse(request, "components/detail.html", context)
