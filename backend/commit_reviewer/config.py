"""Resolved run configuration shared across the pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

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
    log_file: Path | None = None

    @property
    def url(self) -> str | None:
        return self.target if self.mode is Mode.REMOTE else None
