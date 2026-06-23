"""Pretty, frontend-like terminal output, kept separate from developer logging.

Developer logs (HTTP traffic, retries, validation errors) are written to a log
file via the logging module. Everything printed here is the clean, human-facing
output the user sees while a review runs: a header, one styled line per commit,
and a closing summary.
"""

from __future__ import annotations

import os
import sys

from .models import Evaluation, Mode, Rating, Summary

_RESET = "\033[0m"
_BOLD = "\033[1m"
_DIM = "\033[2m"

# Rating colors mirror the frontend's warm, intensity-based scale:
# strong amber for excellent, plain amber for good, faded grey for bad.
_RATING_COLOR: dict[Rating, str] = {
    Rating.EXCELLENT: "\033[1;93m",
    Rating.GOOD: "\033[33m",
    Rating.BAD: "\033[90m",
}

_ERROR_COLOR = "\033[31m"


def _color_enabled() -> bool:
    return sys.stdout.isatty() and "NO_COLOR" not in os.environ


def _paint(text: str, code: str) -> str:
    if not _color_enabled():
        return text
    return f"{code}{text}{_RESET}"


def print_header(repo: str, mode: Mode, count: int) -> None:
    print()
    print(_paint("  Commit Reviewer", _BOLD))
    print(_paint(f"  {repo}  ·  {mode.value}  ·  up to {count} commit(s)", _DIM))
    print()


def print_result(
    index: int, total: int, short_sha: str, subject: str, evaluation: Evaluation
) -> None:
    color = _RATING_COLOR[evaluation.rating]
    counter = _paint(f"[{index:>2}/{total}]", _DIM)
    sha = _paint(short_sha, _BOLD)
    label = _paint(evaluation.rating.value.upper().ljust(9), color)
    print(f"  {counter} {sha}  {label}  {subject}")
    print(f"           {_paint(evaluation.reasoning, _DIM)}")


def print_note(message: str) -> None:
    print(_paint(f"  {message}", _DIM))


def print_error(message: str) -> None:
    print(_paint(f"  {message}", _ERROR_COLOR), file=sys.stderr)


def print_summary(
    summary: Summary,
    report_path: object,
    served_url: str | None,
    log_path: object | None,
) -> None:
    print()
    parts = [
        _paint(f"{summary.excellent} excellent", _RATING_COLOR[Rating.EXCELLENT]),
        _paint(f"{summary.good} good", _RATING_COLOR[Rating.GOOD]),
        _paint(f"{summary.bad} bad", _RATING_COLOR[Rating.BAD]),
    ]
    print("  " + "  ·  ".join(parts))
    print(_paint(f"  Report  {report_path}", _DIM))
    if served_url:
        print(_paint(f"  Serving {served_url}  (Ctrl+C to stop)", _DIM))
    if log_path is not None:
        print(_paint(f"  Logs    {log_path}", _DIM))
    print()
