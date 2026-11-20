"""Tests for the Gemini settings and client, using fake HTTP responses."""

import json
from collections.abc import Iterator
from typing import Any

import httpx2
import pytest
from google import genai
from google.genai import types
from pydantic import BaseModel
from pydantic_settings import SettingsConfigDict

from server.gemini import GeminiClient, GeminiError, get_client
from server.settings import GeminiSettings

ANSWER = {"category": "division", "line": 3}


class Answer(BaseModel):
    """A small structured answer for the client to parse."""

    category: str
    line: int


class IsolatedSettings(GeminiSettings):
    """Gemini settings that skip the developer's .env file."""

    model_config = SettingsConfigDict(env_file=None)


@pytest.fixture(autouse=True)
def clean_environment(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Remove Gemini variables the developer may have exported, and reset the cache."""
    for name in ("GEMINI_MODEL", "GEMINI_MAX_OUTPUT_TOKENS", "GEMINI_API_KEY"):
        monkeypatch.delenv(name, raising=False)
    get_client.cache_clear()
    yield
    get_client.cache_clear()


def settings(**values: Any) -> GeminiSettings:
    """Build Gemini settings from the given values only."""
    return IsolatedSettings(**values)


def reply(finish_reason: str = "STOP") -> dict[str, Any]:
    """Build a generate_content response holding the answer as JSON text."""
    return {
        "candidates": [
            {
                "content": {"role": "model", "parts": [{"text": json.dumps(ANSWER)}]},
                "finishReason": finish_reason,
            }
        ]
    }


def fake_client(
    status: int, body: dict[str, Any], seen: list[httpx2.Request] | None = None
) -> GeminiClient:
    """Build a Gemini client whose requests get one fixed JSON response.

    Args:
        status: HTTP status to answer with.
        body: JSON body to answer with.
        seen: If given, every request sent is appended to it.

    Returns:
        A client that never touches the network.
    """

    def handle(request: httpx2.Request) -> httpx2.Response:
        """Record the request and reply with the fixed response."""
        if seen is not None:
            seen.append(request)
        return httpx2.Response(status, json=body)

    client = GeminiClient("gemini-test", 100, "key")
    client._sdk = genai.Client(
        api_key="key",
        http_options=types.HttpOptions(
            httpx_client=httpx2.Client(transport=httpx2.MockTransport(handle))
        ),
    )
    return client


def test_model_has_a_default() -> None:
    """Without GEMINI_MODEL the default model is used."""
    assert settings().model == "gemini-4-hydrogen"


@pytest.mark.parametrize("values", [{}, {"api_key": ""}], ids=["missing", "blank"])
def test_key_is_required(values: dict[str, str]) -> None:
    """A missing or blank key is reported clearly."""
    with pytest.raises(ValueError, match="GEMINI_API_KEY"):
        settings(**values).key()


def test_key_comes_from_gemini_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """The key is read from GEMINI_API_KEY, the name the Google SDK uses."""
    monkeypatch.setenv("GEMINI_API_KEY", "key")
    assert settings().key() == "key"


def test_key_is_hidden_when_printed() -> None:
    """The settings never show the key in their text form."""
    assert "secret" not in repr(settings(api_key="secret"))


def test_get_client_is_built_once(monkeypatch: pytest.MonkeyPatch) -> None:
    """The client is built from the settings once and then reused."""
    monkeypatch.setattr(
        "server.gemini.get_gemini_settings", lambda: settings(api_key="key")
    )
    assert get_client() is get_client()


def test_client_parses_structured_output() -> None:
    """The reply comes back as a validated model, and the key and schema are sent."""
    seen: list[httpx2.Request] = []
    client = fake_client(200, reply(), seen)
    assert client.complete("sys", "prompt", Answer) == Answer(**ANSWER)
    assert seen[0].headers["x-goog-api-key"] == "key"
    body = json.loads(seen[0].content)
    assert body["systemInstruction"]["parts"][0]["text"] == "sys"
    assert "category" in json.dumps(body["generationConfig"])


def test_client_wraps_api_errors() -> None:
    """An HTTP error surfaces as a GeminiError."""
    error = {"error": {"code": 400, "message": "x", "status": "INVALID_ARGUMENT"}}
    with pytest.raises(GeminiError):
        fake_client(400, error).complete("sys", "prompt", Answer)


@pytest.mark.parametrize("finish_reason", ["MAX_TOKENS", "SAFETY"])
def test_early_stop_is_an_error(finish_reason: str) -> None:
    """A cut-off or blocked reply is not treated as an answer."""
    client = fake_client(200, reply(finish_reason))
    with pytest.raises(GeminiError, match=finish_reason):
        client.complete("sys", "prompt", Answer)
