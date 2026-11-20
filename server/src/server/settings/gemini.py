"""Settings for calling Gemini through the Google Gen AI SDK."""

from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import SettingsConfigDict

from .base import EnvSettings


class GeminiSettings(EnvSettings):
    """Which Gemini model to call, and the key to call it with.

    Each field reads from a `GEMINI_` variable, e.g. `GEMINI_MODEL`.

    Attributes:
        model: Gemini model ID.
        max_output_tokens: Upper limit on tokens in one response.
        api_key: The Gemini API key used to authenticate API calls.
    """

    model_config = SettingsConfigDict(env_prefix="GEMINI_")

    model: str = "gemini-4-hydrogen"
    max_output_tokens: int = 16000
    api_key: SecretStr | None = None

    def key(self) -> str:
        """Return the API key.

        Raises:
            ValueError: If the key is missing or blank.
        """
        if not self.api_key:
            raise ValueError("set GEMINI_API_KEY")
        return self.api_key.get_secret_value()


@lru_cache
def get_gemini_settings() -> GeminiSettings:
    """Return the Gemini settings, loading them on first use."""
    return GeminiSettings()
