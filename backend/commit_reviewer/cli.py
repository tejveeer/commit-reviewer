"""Command-line entrypoint for ``review-commits``."""

from __future__ import annotations

import argparse
from dataclasses import dataclass

from . import DEFAULT_COMMIT_COUNT, DEFAULT_PORT, OPENROUTER_MODEL, __version__
from .models import Mode


@dataclass(frozen=True)
class CliConfig:
    """Resolved options for a single run."""

    mode: Mode
    target: str
    count: int
    port: int
    model: str
    serve: bool

    @property
    def url(self) -> str | None:
        return self.target if self.mode is Mode.REMOTE else None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="review-commits",
        description=(
            "Review the most recent git commit messages with an LLM and serve an "
            "HTML report on port 3546."
        ),
    )
    parser.add_argument(
        "--url",
        metavar="URL",
        default=None,
        help="Review a remote repository at this URL (default: current directory).",
    )
    parser.add_argument(
        "-n",
        "--count",
        type=int,
        default=DEFAULT_COMMIT_COUNT,
        help=f"Number of recent commits to review (default: {DEFAULT_COMMIT_COUNT}).",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help=f"Port for the report server (default: {DEFAULT_PORT}).",
    )
    parser.add_argument(
        "--model",
        default=OPENROUTER_MODEL,
        help=f"OpenRouter model id (default: {OPENROUTER_MODEL}).",
    )
    parser.add_argument(
        "--no-serve",
        action="store_true",
        help="Write the JSON report but do not start the report server.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    return parser


def parse_args(argv: list[str] | None = None) -> CliConfig:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.count < 1:
        parser.error("--count must be a positive integer")

    mode = Mode.REMOTE if args.url else Mode.LOCAL
    target = args.url if args.url else "."

    return CliConfig(
        mode=mode,
        target=target,
        count=args.count,
        port=args.port,
        model=args.model,
        serve=not args.no_serve,
    )


def run(config: CliConfig) -> int:
    """Execute the pipeline. Wired up fully in a later ticket."""
    raise NotImplementedError(
        "The review pipeline is implemented in a subsequent ticket."
    )


def main(argv: list[str] | None = None) -> int:
    config = parse_args(argv)
    return run(config)


if __name__ == "__main__":
    raise SystemExit(main())
