"""Tests for report writing and the static server.

    Each category below is delimited in the code with banner comments
    "CATEGORY: <name>" ... "end: <name>".

    Persistence
        write_report creates the output directory and writes
        report.json, which round-trips back through
        Report.model_validate_json with the correct summary and ratings.

    Static serving
        create_server is started on an ephemeral port in a background
        thread, and real HTTP GETs confirm it serves both report.json
        and index.html before being shut down.
"""

from __future__ import annotations

import threading
from datetime import datetime
from pathlib import Path

import httpx
from commit_reviewer.models import (
    Commit,
    Evaluation,
    Mode,
    Rating,
    Report,
    ReviewedCommit,
)
from commit_reviewer.report import REPORT_FILENAME, create_server, write_report


def _report() -> Report:
    commit = Commit(
        sha="abc1234", author="Jane", date=datetime(2024, 1, 1), message="feat: x"
    )
    reviewed = ReviewedCommit.from_parts(
        commit, Evaluation(rating=Rating.EXCELLENT, reasoning="Clear.")
    )
    return Report.build(repo="/tmp/x", mode=Mode.LOCAL, model="m", commits=[reviewed])


# ======================================================================
# CATEGORY: Persistence
# ======================================================================


def test_write_report_roundtrips(tmp_path: Path) -> None:
    out = tmp_path / "dist"
    path = write_report(_report(), out)

    assert path == out / REPORT_FILENAME
    assert path.is_file()

    loaded = Report.model_validate_json(path.read_text())
    assert loaded.summary.excellent == 1
    assert loaded.commits[0].rating is Rating.EXCELLENT
    assert loaded.mode is Mode.LOCAL


# end: Persistence


# ======================================================================
# CATEGORY: Static serving
# ======================================================================


def test_create_server_serves_files(tmp_path: Path) -> None:
    write_report(_report(), tmp_path)
    (tmp_path / "index.html").write_text("<h1>report</h1>")

    server = create_server(tmp_path, port=0)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        base = f"http://127.0.0.1:{port}"
        json_resp = httpx.get(f"{base}/{REPORT_FILENAME}", timeout=5)
        index_resp = httpx.get(f"{base}/", timeout=5)

        assert json_resp.status_code == 200
        assert json_resp.json()["summary"]["excellent"] == 1
        assert index_resp.status_code == 200
        assert "report" in index_resp.text
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


# end: Static serving
