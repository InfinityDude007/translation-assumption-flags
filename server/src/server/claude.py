"""Claude client, cached on first use."""

from functools import lru_cache

import anthropic
from pydantic import BaseModel

from .settings import get_claude_settings


class ClaudeError(RuntimeError):
    """A Claude call failed or returned no usable structured output."""


class ClaudeClient:
    """Calls the Messages API and parses the reply with structured output.

    Args:
        model: Claude model ID.
        max_output_tokens: Upper limit on tokens in one response.
        api_key: Claude API key, or None when using `auth_token`.
        auth_token: Bearer token, or None when using `api_key`.
    """

    def __init__(
        self,
        model: str,
        max_output_tokens: int,
        api_key: str | None = None,
        auth_token: str | None = None,
    ) -> None:
        """Create the SDK client with whichever credential is given."""
        self._sdk = anthropic.Anthropic(api_key=api_key, auth_token=auth_token)
        self._model = model
        self._max_output_tokens = max_output_tokens

    def complete[T: BaseModel](self, system: str, prompt: str, schema: type[T]) -> T:
        """Send one request and return the response parsed into `schema`.

        Args:
            system: Instructions that frame the task.
            prompt: The task input.
            schema: Pydantic model the response must match.

        Returns:
            The validated response.

        Raises:
            ClaudeError: If the request fails, is refused, is cut off or
                cannot be parsed.
        """
        try:
            response = self._sdk.messages.parse(
                model=self._model,
                max_tokens=self._max_output_tokens,
                system=system,
                messages=[{"role": "user", "content": prompt}],
                output_format=schema,
            )

        except anthropic.APIError as error:
            raise ClaudeError(f"Claude request failed: {error}") from error

        if response.stop_reason in ("refusal", "max_tokens"):
            raise ClaudeError(f"Claude stopped early: {response.stop_reason}")

        if response.parsed_output is None:
            raise ClaudeError("Claude returned no parsable output")

        return response.parsed_output


@lru_cache
def get_client() -> ClaudeClient:
    """Return the shared Claude client, built from the settings on first use.

    Raises:
        ValueError: If neither or both Claude credentials are set.
    """
    settings = get_claude_settings()
    api_key, auth_token = settings.credentials()

    return ClaudeClient(
        settings.model,
        settings.max_output_tokens,
        api_key=api_key,
        auth_token=auth_token,
    )
