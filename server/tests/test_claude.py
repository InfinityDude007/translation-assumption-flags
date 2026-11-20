"""Tests for the Claude settings and client, using fake HTTP responses."""

import json
from collections.abc import Iterator
from typing import Any

import anthropic
import httpx2
import pytest
from pydantic import BaseModel
from pydantic_settings import SettingsConfigDict

from server.claude import ClaudeClient, ClaudeError, get_client
from server.settings import ClaudeSettings

ANSWER = {"category": "division", "line": 3}


class Answer(BaseModel):
    """A small structured answer for the client to parse."""

    category: str
    line: int


class IsolatedSettings(ClaudeSettings):
    """Claude settings that skip the developer's .env file."""

    model_config = SettingsConfigDict(env_file=None)


@pytest.fixture(autouse=True)
def clean_environment(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Remove Claude variables the developer may have exported, and reset the cache."""
    for name in (
        "CLAUDE_MODEL",
        "CLAUDE_MAX_OUTPUT_TOKENS",
        "CLAUDE_API_KEY",
        "CLAUDE_AUTH_TOKEN",
    ):
        monkeypatch.delenv(name, raising=False)
    get_client.cache_clear()
    yield
    get_client.cache_clear()


def settings(**values: Any) -> ClaudeSettings:
    """Build Claude settings from the given values only."""
    return IsolatedSettings(**values)


def message(stop_reason: str = "end_turn") -> dict[str, Any]:
    """Build a Messages API response holding the answer as JSON text."""
    return {
        "id": "msg_1",
        "type": "message",
        "role": "assistant",
        "model": "claude-opus-5-5",
        "content": [{"type": "text", "text": json.dumps(ANSWER)}],
        "stop_reason": stop_reason,
        "stop_sequence": None,
        "usage": {"input_tokens": 1, "output_tokens": 1},
    }


def fake_client(
    status: int,
    body: dict[str, Any],
    seen: list[httpx2.Request] | None = None,
    **credential: str,
) -> ClaudeClient:
    """Build a Claude client whose requests get one fixed JSON response.

    Args:
        status: HTTP status to answer with.
        body: JSON body to answer with.
        seen: If given, every request sent is appended to it.
        **credential: `api_key=...` or `auth_token=...`.

    Returns:
        A client that never touches the network.
    """

    def handle(request: httpx2.Request) -> httpx2.Response:
        """Record the request and reply with the fixed response."""
        if seen is not None:
            seen.append(request)
        return httpx2.Response(status, json=body)

    client = ClaudeClient("claude-opus-5-5", 100, **credential)
    client._sdk = anthropic.Anthropic(
        api_key=credential.get("api_key"),
        auth_token=credential.get("auth_token"),
        http_client=httpx2.Client(transport=httpx2.MockTransport(handle)),
        max_retries=0,
    )
    return client


def test_model_has_a_default() -> None:
    """Without CLAUDE_MODEL the default model is used."""
    assert settings().model == "claude-opus-5-5"


@pytest.mark.parametrize(
    "values",
    [
        {},
        {"api_key": "key", "auth_token": "token"},
        {"api_key": ""},
    ],
    ids=["neither", "both", "blank"],
)
def test_exactly_one_credential_is_required(values: dict[str, str]) -> None:
    """Neither credential, both, or a blank one is reported clearly."""
    with pytest.raises(ValueError, match="exactly one"):
        settings(**values).credentials()


def test_credentials_come_from_the_claude_variables(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The token is read from CLAUDE_AUTH_TOKEN."""
    monkeypatch.setenv("CLAUDE_AUTH_TOKEN", "token")
    assert settings().credentials() == (None, "token")


def test_credentials_are_hidden_when_printed() -> None:
    """The settings never show a credential in their text form."""
    assert "secret" not in repr(settings(api_key="secret"))


def test_get_client_is_built_once(monkeypatch: pytest.MonkeyPatch) -> None:
    """The client is built from the settings once and then reused."""
    monkeypatch.setattr(
        "server.claude.get_claude_settings",
        lambda: settings(api_key="key"),
    )
    assert get_client() is get_client()


@pytest.mark.parametrize(
    ("credential", "header"),
    [
        ({"api_key": "key"}, "Bearer key"),
        ({"auth_token": "token"}, "Bearer token"),
    ],
    ids=["api_key", "auth_token"],
)
def test_client_parses_structured_output(
    credential: dict[str, str], header: str
) -> None:
    """The reply comes back as a validated model, and the credential is sent."""
    seen: list[httpx2.Request] = []
    client = fake_client(200, message(), seen, **credential)
    assert client.complete("sys", "prompt", Answer) == Answer(**ANSWER)
    assert seen[0].headers["authorization"] == header


def test_client_wraps_api_errors() -> None:
    """An HTTP error surfaces as a ClaudeError."""
    error = {
        "type": "error",
        "error": {"type": "invalid_request_error", "message": "x"},
    }
    client = fake_client(400, error, api_key="key")
    with pytest.raises(ClaudeError):
        client.complete("sys", "prompt", Answer)


@pytest.mark.parametrize("stop_reason", ["refusal", "max_tokens"])
def test_early_stop_is_an_error(stop_reason: str) -> None:
    """A refused or cut-off reply is not treated as an answer."""
    client = fake_client(200, message(stop_reason), api_key="key")
    with pytest.raises(ClaudeError, match=stop_reason):
        client.complete("sys", "prompt", Answer)
