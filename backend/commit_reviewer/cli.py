"""Command-line entrypoint for review-commits."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from dotenv import load_dotenv

from . import DEFAULT_COMMIT_COUNT, DEFAULT_PORT, OPENROUTER_MODEL, __version__, console
from .collector import CommitCollector
from .config import CliConfig
from .errors import CommitReviewerError
from .evaluator import LLMCommitEvaluator
from .models import Commit, Evaluation, Mode, Report, ReviewedCommit
from .openrouter import OpenRouterClient
from .report import default_web_root, serve, write_report

logger = logging.getLogger("commit_reviewer")

DEFAULT_LOG_FILENAME = "commit-reviewer.log"


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
        "--log-file",
        metavar="PATH",
        default=None,
        help=(
            "Where to write developer logs "
            f"(default: ./{DEFAULT_LOG_FILENAME} in the current directory)."
        ),
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

    log_file = (
        Path(args.log_file).resolve()
        if args.log_file
        else Path.cwd() / DEFAULT_LOG_FILENAME
    )

    return CliConfig(
        mode=mode,
        target=target,
        count=args.count,
        port=args.port,
        model=args.model,
        serve=not args.no_serve,
        log_file=log_file,
    )


def _repo_label(config: CliConfig) -> str:
    if config.mode is Mode.REMOTE and config.url is not None:
        return config.url
    return str(Path(config.target).resolve())


def run(
    config: CliConfig,
    *,
    collector: CommitCollector | None = None,
    evaluator: LLMCommitEvaluator | None = None,
) -> int:
    """Collect commits, evaluate them, write the JSON report, and serve it.

    collector and evaluator can be injected for testing; by default the
    real git collector and OpenRouter-backed evaluator are used.
    """
    repo = _repo_label(config)
    logger.info(
        "Reviewing up to %d commit(s) from %s [%s]",
        config.count,
        repo,
        config.mode.value,
    )
    console.print_header(repo, config.mode, config.count)

    collector = collector or CommitCollector()
    commits = collector.collect(config)

    reviewed: list[ReviewedCommit] = []
    if not commits:
        logger.warning("No commits found to review.")
        console.print_note("No commits found to review.")
    else:
        if evaluator is None:
            evaluator = LLMCommitEvaluator(
                OpenRouterClient(model=config.model),
                on_result=_print_result,
            )
        evaluations = evaluator.evaluate(commits)
        reviewed = [
            ReviewedCommit.from_parts(commit, evaluation)
            for commit, evaluation in zip(commits, evaluations, strict=True)
        ]

    report = Report.build(
        repo=repo, mode=config.mode, model=config.model, commits=reviewed
    )

    out_dir = default_web_root()
    path = write_report(report, out_dir)
    summary = report.summary
    logger.info(
        "Wrote %s (excellent=%d, good=%d, bad=%d)",
        path,
        summary.excellent,
        summary.good,
        summary.bad,
    )

    served_url = f"http://localhost:{config.port}/" if config.serve else None
    console.print_summary(summary, path, served_url, config.log_file)

    if config.serve:
        serve(out_dir, config.port)
    return 0


def _print_result(
    index: int, total: int, commit: Commit, evaluation: Evaluation
) -> None:
    console.print_result(index, total, commit.short_sha, commit.subject, evaluation)


def _configure_logging(log_file: Path) -> None:
    """Send all logging (ours plus httpx) to a file, keeping the terminal clean."""
    log_file.parent.mkdir(parents=True, exist_ok=True)
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    for handler in list(root.handlers):
        root.removeHandler(handler)
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    )
    root.addHandler(file_handler)


def _load_env(project_root: Path | None = None) -> None:
    """Load the API key from .env regardless of the directory being reviewed.

    An already-exported OPENROUTER_API_KEY always takes precedence (load_dotenv
    does not override existing environment variables). project_root is exposed
    for testing; in normal use it defaults to the repository root.
    """
    if project_root is None:
        project_root = Path(__file__).resolve().parents[2]
    project_env = project_root / ".env"
    if project_env.is_file():
        load_dotenv(project_env)
    load_dotenv()


def main(argv: list[str] | None = None) -> int:
    _load_env()
    config = parse_args(argv)
    if config.log_file is not None:
        _configure_logging(config.log_file)
    try:
        return run(config)
    except CommitReviewerError as exc:
        logger.error("Error: %s", exc)
        console.print_error(f"Error: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
