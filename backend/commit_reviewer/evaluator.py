"""Evaluate commit messages with an LLM and validate the structured result."""

from __future__ import annotations

import logging
import time
from typing import Any

from pydantic import ValidationError

from .errors import EvaluatorError
from .models import Commit, Evaluation, Rating
from .openrouter import ChatClient

logger = logging.getLogger("commit_reviewer")

#: Structured-output contract: the model MUST return exactly this JSON shape.
RESPONSE_FORMAT: dict[str, Any] = {
    "type": "json_schema",
    "json_schema": {
        "name": "commit_evaluation",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "rating": {
                    "type": "string",
                    "enum": [r.value for r in Rating],
                },
                "reasoning": {"type": "string"},
            },
            "required": ["rating", "reasoning"],
            "additionalProperties": False,
        },
    },
}

SYSTEM_PROMPT = """\
You are a senior engineer reviewing git commit messages. Rate the quality of a \
single commit message using exactly one of these ratings:

- "excellent": Clear, concise subject in the imperative mood; explains WHAT changed \
and WHY when useful; well-structured; follows good conventions.
- "good": Understandable and reasonable, but with minor issues (vague wording, \
missing context, or style nits).
- "bad": Unclear, uninformative, or unhelpful (e.g. "fix", "wip", "update stuff", \
empty, or noise).

Judge only the commit MESSAGE quality, not the code. Respond with a brief, specific \
reasoning (1-2 sentences). You must respond with JSON only, matching the required \
schema: {"rating": <excellent|good|bad>, "reasoning": <string>}."""


class LLMCommitEvaluator:
    """Calls the LLM per commit and returns validated evaluations."""

    def __init__(
        self,
        client: ChatClient,
        *,
        max_retries: int = 2,
        backoff_base: float = 0.5,
        sleep: Any = time.sleep,
    ) -> None:
        self._client = client
        self._max_retries = max_retries
        self._backoff_base = backoff_base
        self._sleep = sleep

    def evaluate(self, commits: list[Commit]) -> list[Evaluation]:
        """Evaluate each commit, logging results to the terminal."""
        evaluations: list[Evaluation] = []
        total = len(commits)
        for index, commit in enumerate(commits, start=1):
            evaluation = self._evaluate_one(commit)
            evaluations.append(evaluation)
            logger.info(
                "[%d/%d] %s  %-9s  %s",
                index,
                total,
                commit.short_sha,
                evaluation.rating.value.upper(),
                evaluation.reasoning,
            )
        return evaluations

    def _evaluate_one(self, commit: Commit) -> Evaluation:
        user_prompt = self._build_user_prompt(commit)
        last_error: Exception | None = None

        for attempt in range(self._max_retries + 1):
            try:
                content = self._client.complete(
                    SYSTEM_PROMPT, user_prompt, response_format=RESPONSE_FORMAT
                )
                return Evaluation.model_validate_json(content)
            except (EvaluatorError, ValidationError, ValueError) as exc:
                last_error = exc
                if attempt < self._max_retries:
                    delay = self._backoff_base * (2**attempt)
                    logger.warning(
                        "Evaluation attempt %d for %s failed (%s); retrying in %.1fs",
                        attempt + 1,
                        commit.short_sha,
                        exc,
                        delay,
                    )
                    self._sleep(delay)

        logger.error(
            "Giving up on %s after %d attempts: %s",
            commit.short_sha,
            self._max_retries + 1,
            last_error,
        )
        return Evaluation(
            rating=Rating.BAD,
            reasoning=f"Could not evaluate this commit (LLM error: {last_error}).",
        )

    @staticmethod
    def _build_user_prompt(commit: Commit) -> str:
        return f"Evaluate this commit message:\n\n{commit.message}"
