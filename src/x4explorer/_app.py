"""Starlette application factory."""

from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING

from starlette.applications import Starlette
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates

from x4explorer._db import close_db, init_db
from x4explorer._routes.dashboard import dashboard, search_page
from x4explorer._routes.wares import ware_detail, ware_list

if TYPE_CHECKING:
    from collections.abc import AsyncIterator
    from pathlib import Path

_BASE_DIR = __import__("pathlib").Path(__file__).resolve().parent.parent.parent
_TEMPLATE_DIR = _BASE_DIR / "templates"
_STATIC_DIR = _BASE_DIR / "static"


@contextlib.asynccontextmanager
async def _lifespan(app: Starlette) -> AsyncIterator[None]:
    init_db(app.state.db_path)
    yield
    close_db()


def create_app(db_path: Path) -> Starlette:
    """Create the Starlette application."""
    templates = Jinja2Templates(directory=str(_TEMPLATE_DIR))

    routes: list[Route | Mount] = [
        Route("/", dashboard, name="dashboard"),
        Route("/search", search_page, name="search"),
        Route("/wares", ware_list, name="wares"),
        Route("/wares/{ware_id:path}", ware_detail, name="ware_detail"),
        Mount("/static", app=StaticFiles(directory=str(_STATIC_DIR)), name="static"),
    ]

    app = Starlette(
        debug=True,
        routes=routes,
        lifespan=_lifespan,
    )
    app.state.db_path = db_path
    app.state.templates = templates

    return app
