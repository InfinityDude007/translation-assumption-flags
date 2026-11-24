"""Gemini client, cached on first use."""

from functools import lru_cache

from google import genai
from google.genai import errors, types
from pydantic import BaseModel

from .settings import get_gemini_settings

RETRY = types.HttpRetryOptions(
    attempts=11,
    initial_delay=1,
    max_delay=10,
    exp_base=1,
    jitter=0,
    http_status_codes=[503],
)
"""Resend up to 10 times (+1st try), 30 s apart, while the model is unavailable (503).

Rate limits (429) are not retried, so a run stops and can be resumed later.
"""


class GeminiError(RuntimeError):
    """A Gemini call failed or returned no usable structured output.

    Attributes:
        status: HTTP status of a failed request, or None if the request succeeded.
    """

    def __init__(self, message: str, status: int | None = None) -> None:
        """Store the message and the HTTP status."""
        super().__init__(message)
        self.status = status


class GeminiClient:
    """Calls generate_content and parses the reply with a response schema.

    Args:
        model: Gemini model ID.
        max_output_tokens: Upper limit on tokens in one response.
        api_key: Gemini API key.
    """

    def __init__(self, model: str, max_output_tokens: int, api_key: str) -> None:
        """Create the SDK client."""
        self._sdk = genai.Client(
            api_key=api_key, http_options=types.HttpOptions(retry_options=RETRY)
        )
        self._model = model
        self._max_output_tokens = max_output_tokens

    @property
    def model(self) -> str:
        """The Gemini model ID this client calls."""
        return self._model

    def complete[T: BaseModel](self, system: str, prompt: str, schema: type[T]) -> T:
        """Send one request and return the response parsed into `schema`.

        Args:
            system: Instructions that frame the task.
            prompt: The task input.
            schema: Pydantic model the response must match.

        Returns:
            The validated response.

        Raises:
            GeminiError: If the request fails, stops early or cannot be parsed.
        """
        try:
            response = self._sdk.models.generate_content(
                model=self._model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system,
                    response_mime_type="application/json",
                    response_schema=schema,
                    max_output_tokens=self._max_output_tokens,
                ),
            )

        except errors.APIError as error:
            raise GeminiError(f"Gemini request failed: {error}", error.code) from error

        reason = response.candidates[0].finish_reason if response.candidates else None
        if reason is not None and reason != types.FinishReason.STOP:
            raise GeminiError(f"Gemini stopped early: {reason}")

        if not isinstance(response.parsed, schema):
            raise GeminiError("Gemini returned no parsable output")

        return response.parsed


@lru_cache
def get_client() -> GeminiClient:
    """Return the shared Gemini client, built from the settings on first use.

    Raises:
        ValueError: If the Gemini API key is not set.
    """
    settings = get_gemini_settings()

    return GeminiClient(settings.model, settings.max_output_tokens, settings.key())
