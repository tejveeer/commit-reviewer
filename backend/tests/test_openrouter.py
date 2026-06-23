"""Tests for the OpenRouter HTTP client.

    All tests use httpx.MockTransport to simulate the API without any
    real network. Each category below is delimited in the code with
    banner comments  "CATEGORY: <name>" ... "end: <name>".

    Happy path
        a successful completion returns the message content, and the
        outgoing request carries the expected model, messages,
        response_format, and Authorization header.

    Configuration errors
        a missing API key raises EvaluatorError at construction time.

    Transport errors
        a non-2xx HTTP status is surfaced as EvaluatorError.

    Response validation
        malformed JSON shapes (missing keys, non-string content) raise
        EvaluatorError instead of leaking KeyError or type bugs, and an
        embedded error object (HTTP 200 body) is surfaced cleanly.

    Tuning
        the outgoing payload carries the configured temperature,
        max_tokens, and reasoning effort.
"""

from __future__ import annotations

import json

import httpx
import pytest
from commit_reviewer.errors import EvaluatorError
from commit_reviewer.openrouter import OpenRouterClient


def _client(handler: httpx.MockTransport) -> OpenRouterClient:
    return OpenRouterClient(
        api_key="test-key",
        model="test-model",
        client=httpx.Client(transport=handler),
    )


# ======================================================================
# CATEGORY: Happy path
# ======================================================================


def test_complete_returns_content_and_sends_payload() -> None:
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["payload"] = json.loads(request.content)
        captured["auth"] = request.headers.get("Authorization")
        return httpx.Response(200, json={"choices": [{"message": {"content": "hello"}}]})

    client = _client(httpx.MockTransport(handler))
    result = client.complete("sys", "usr", response_format={"type": "json_object"})

    assert result == "hello"
    payload = captured["payload"]
    assert isinstance(payload, dict)
    assert payload["model"] == "test-model"
    assert payload["response_format"] == {"type": "json_object"}
    assert payload["messages"][0]["role"] == "system"
    assert payload["messages"][1]["content"] == "usr"
    assert captured["auth"] == "Bearer test-key"


# end: Happy path


# ======================================================================
# CATEGORY: Configuration errors
# ======================================================================


def test_missing_api_key_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    with pytest.raises(EvaluatorError, match="OPENROUTER_API_KEY"):
        OpenRouterClient(api_key=None)


# end: Configuration errors


# ======================================================================
# CATEGORY: Transport errors
# ======================================================================


def test_http_error_raises_evaluator_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="boom")

    client = _client(httpx.MockTransport(handler))
    with pytest.raises(EvaluatorError, match="500"):
        client.complete("sys", "usr")


# end: Transport errors


# ======================================================================
# CATEGORY: Response validation
# ======================================================================


def test_malformed_response_shape_raises() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"unexpected": True})

    client = _client(httpx.MockTransport(handler))
    with pytest.raises(EvaluatorError, match="Unexpected"):
        client.complete("sys", "usr")


def test_non_string_content_raises() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"choices": [{"message": {"content": 123}}]})

    client = _client(httpx.MockTransport(handler))
    with pytest.raises(EvaluatorError, match="not text"):
        client.complete("sys", "usr")


def test_embedded_error_object_is_surfaced() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200, json={"error": {"code": 502, "message": "Upstream error"}}
        )

    client = _client(httpx.MockTransport(handler))
    with pytest.raises(EvaluatorError, match="OpenRouter error 502: Upstream error"):
        client.complete("sys", "usr")


# end: Response validation


# ======================================================================
# CATEGORY: Tuning
# ======================================================================


def test_payload_carries_tuning_parameters() -> None:
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["payload"] = json.loads(request.content)
        return httpx.Response(200, json={"choices": [{"message": {"content": "ok"}}]})

    client = OpenRouterClient(
        api_key="test-key",
        model="test-model",
        temperature=0.2,
        max_tokens=512,
        reasoning_effort="low",
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    client.complete("sys", "usr")

    payload = captured["payload"]
    assert isinstance(payload, dict)
    assert payload["temperature"] == 0.2
    assert payload["max_tokens"] == 512
    assert payload["reasoning"] == {"effort": "low"}


# end: Tuning
