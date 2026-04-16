"""Script datatypes and keywords route handlers."""

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
    get_all_datatype_names,
    get_datatype,
    get_datatype_filter_options,
    get_datatype_properties,
    get_inheritance_chain,
    get_keyword,
    get_keyword_filter_options,
    get_keyword_properties,
    list_datatypes,
    list_keywords,
)


async def datatype_list(request: Request) -> Response:
    """Render paginated datatype list with filters."""
    templates: Jinja2Templates = request.app.state.templates
    conn = get_db()

    page_num, per_page = parse_page_params(
        request.query_params.get("page"),
        request.query_params.get("per_page"),
    )

    base_type = request.query_params.get("base_type", "").strip() or None
    query = request.query_params.get("q", "").strip() or None
    sort = request.query_params.get("sort", "name")
    direction = request.query_params.get("dir", "asc")

    datatypes, page_info = list_datatypes(
        conn,
        base_type=base_type,
        query=query,
        sort=sort,
        direction=direction,
        page=page_num,
        per_page=per_page,
    )
    filter_options = get_datatype_filter_options(conn)

    context = {
        "request": request,
        "current": "datatypes",
        "datatypes": datatypes,
        "page": page_info,
        "filters": filter_options,
        "base_type": base_type or "",
        "query": query or "",
        "sort": sort,
        "dir": direction,
    }

    if _is_htmx_fragment(request):
        response = templates.TemplateResponse(request, "scripts/_datatypes_table.html", context)
    else:
        response = templates.TemplateResponse(request, "scripts/datatypes.html", context)
    response.headers["Vary"] = "HX-Request"
    return response


async def datatype_detail(request: Request) -> Response:
    """Render datatype detail with inheritance chain and properties."""
    from starlette.responses import Response as StarletteResponse

    templates: Jinja2Templates = request.app.state.templates
    conn = get_db()
    name = request.path_params["name"]

    datatype = get_datatype(conn, name)
    if datatype is None:
        return StarletteResponse("Datatype not found", status_code=404)

    chain = get_inheritance_chain(conn, name)
    all_datatype_names = get_all_datatype_names(conn)

    # Build properties with source info: own first, then inherited
    own_props = get_datatype_properties(conn, name)
    inherited: list[dict[str, object]] = []
    for ancestor in chain[1:]:  # skip self
        ancestor_props = get_datatype_properties(conn, ancestor["name"])
        for p in ancestor_props:
            inherited.append(
                {
                    "prop_name": p["prop_name"],
                    "result_desc": p["result_desc"],
                    "result_type": p["result_type"],
                    "source": ancestor["name"],
                }
            )

    context = {
        "request": request,
        "current": "datatypes",
        "datatype": datatype,
        "chain": chain,
        "own_props": own_props,
        "inherited_props": inherited,
        "all_datatype_names": all_datatype_names,
    }
    return templates.TemplateResponse(request, "scripts/datatype_detail.html", context)


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
    sort = request.query_params.get("sort", "name")
    direction = request.query_params.get("dir", "asc")

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
