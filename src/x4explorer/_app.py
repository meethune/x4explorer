"""Starlette application factory."""

from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING

from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates

from x4explorer._db import close_db, init_db
from x4explorer._routes.components import component_detail, component_list
from x4explorer._routes.dashboard import dashboard, search_page
from x4explorer._routes.macros import macro_detail, macro_list
from x4explorer._routes.scripts import (
    datatype_detail,
    datatype_list,
    keyword_detail,
    keyword_list,
)
from x4explorer._routes.wares import ware_detail, ware_list

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, MutableMapping
    from pathlib import Path
    from typing import Any

    from starlette.types import ASGIApp, Receive, Scope, Send

_BASE_DIR = __import__("pathlib").Path(__file__).resolve().parent.parent.parent
_TEMPLATE_DIR = _BASE_DIR / "templates"
_STATIC_DIR = _BASE_DIR / "static"


class _SecurityHeadersMiddleware:
    """Add standard security response headers."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_with_headers(message: MutableMapping[str, Any]) -> None:
            if isinstance(message, dict) and message.get("type") == "http.response.start":
                headers = list(message.get("headers", []))
                headers.extend(
                    [
                        (b"x-content-type-options", b"nosniff"),
                        (b"x-frame-options", b"DENY"),
                        (b"referrer-policy", b"strict-origin-when-cross-origin"),
                    ]
                )
                message["headers"] = headers
            await send(message)

        await self.app(scope, receive, send_with_headers)


@contextlib.asynccontextmanager
async def _lifespan(app: Starlette) -> AsyncIterator[None]:
    init_db(app.state.db_path)
    yield
    close_db()


def create_app(db_path: Path, *, debug: bool = False) -> Starlette:
    """Create the Starlette application."""
    templates = Jinja2Templates(directory=str(_TEMPLATE_DIR))

    routes: list[Route | Mount] = [
        Route("/", dashboard, name="dashboard"),
        Route("/search", search_page, name="search"),
        Route("/wares", ware_list, name="wares"),
        Route("/wares/{ware_id:path}", ware_detail, name="ware_detail"),
        Route("/macros", macro_list, name="macros"),
        Route("/macros/{name:path}", macro_detail, name="macro_detail"),
        Route("/components", component_list, name="components"),
        Route("/components/{name:path}", component_detail, name="component_detail"),
        Route("/scripts/datatypes", datatype_list, name="datatypes"),
        Route("/scripts/datatypes/{name:path}", datatype_detail, name="datatype_detail"),
        Route("/scripts/keywords", keyword_list, name="keywords"),
        Route("/scripts/keywords/{name:path}", keyword_detail, name="keyword_detail"),
        Mount("/static", app=StaticFiles(directory=str(_STATIC_DIR)), name="static"),
    ]

    app = Starlette(
        debug=debug,
        routes=routes,
        lifespan=_lifespan,
        middleware=[Middleware(_SecurityHeadersMiddleware)],
    )
    app.state.db_path = db_path
    app.state.templates = templates

    return app
