"""Persist the report as JSON and serve it (plus the built frontend) over HTTP."""

from __future__ import annotations

import functools
import logging
import os
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from . import DEFAULT_PORT
from .models import Report

logger = logging.getLogger("commit_reviewer")

REPORT_FILENAME = "report.json"


def default_web_root() -> Path:
    """Directory served on the report port (where the built frontend lives)."""
    bundled = Path(__file__).resolve().parent / "web"
    if bundled.is_dir():
        return bundled
    return Path(__file__).resolve().parents[2] / "frontend" / "dist"


def write_report(report: Report, out_dir: Path) -> Path:
    """Write report.json into out_dir (created if needed); return its path."""
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / REPORT_FILENAME
    path.write_text(report.model_dump_json(indent=2), encoding="utf-8")
    return path


class _ReportRequestHandler(SimpleHTTPRequestHandler):
    """Static handler that routes access logs through our logger at debug level."""

    def log_message(self, format: str, *args: Any) -> None:
        logger.debug("%s - %s", self.address_string(), format % args)


def _bind_host() -> str:
    """Host address for the report server (127.0.0.1 locally, 0.0.0.0 in Docker)."""
    return os.environ.get("COMMIT_REVIEWER_HOST", "127.0.0.1")


def create_server(directory: Path, port: int = DEFAULT_PORT) -> ThreadingHTTPServer:
    """Build (but do not start) a static file server bound to the directory."""
    handler = functools.partial(_ReportRequestHandler, directory=str(directory))
    return ThreadingHTTPServer((_bind_host(), port), handler)


def serve(directory: Path, port: int = DEFAULT_PORT) -> None:
    """Serve the directory on the given port until interrupted (Ctrl+C)."""
    server = create_server(directory, port)
    url = f"http://localhost:{port}/"
    logger.info("Serving report at %s (press Ctrl+C to stop)", url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down report server.")
    finally:
        server.server_close()
