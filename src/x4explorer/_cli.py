"""CLI entry point for x4explorer."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    """Run the x4explorer web server."""
    parser = argparse.ArgumentParser(
        prog="x4explorer",
        description="Web interface for browsing X4: Foundations game data.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_serve = sub.add_parser("serve", help="Start the web server")
    p_serve.add_argument(
        "--db",
        default=None,
        help="Path to x4cat index database (auto-detected if not provided)",
    )
    p_serve.add_argument("--host", default="127.0.0.1", help="Bind address (default: 127.0.0.1)")
    p_serve.add_argument("--port", type=int, default=8000, help="Port (default: 8000)")
    p_serve.add_argument("--debug", action="store_true", help="Enable debug mode")

    args = parser.parse_args(argv)

    if args.command == "serve":
        return _cmd_serve(args)

    return 1


def _cmd_serve(args: argparse.Namespace) -> int:
    from x4explorer._db import find_default_db

    db_path: Path | None = Path(args.db) if args.db else find_default_db()

    if db_path is None or not db_path.exists():
        print(
            "error: no x4cat index found. Run 'x4cat index <game_dir>' first, or pass --db",
            file=sys.stderr,
        )
        return 1

    print(f"Using database: {db_path}")
    print(f"Starting server at http://{args.host}:{args.port}")

    import uvicorn

    from x4explorer._app import create_app

    app = create_app(db_path, debug=args.debug)
    uvicorn.run(app, host=args.host, port=args.port)
    return 0
