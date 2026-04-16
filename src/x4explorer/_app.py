"""Starlette application factory."""

from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING

from starlette.applications import Starlette
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates

from x4explorer._db import close_db, init_db

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


async def _index(request: object) -> object:
    """Placeholder index page."""
    from starlette.requests import Request

    req = request if isinstance(request, Request) else Request(scope={}, receive=None)  # type: ignore[arg-type]
    templates: Jinja2Templates = req.app.state.templates
    return templates.TemplateResponse(req, "index.html")


def create_app(db_path: Path) -> Starlette:
    """Create the Starlette application."""
    templates = Jinja2Templates(directory=str(_TEMPLATE_DIR))

    routes: list[Route | Mount] = [
        Route("/", _index, name="index"),
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
