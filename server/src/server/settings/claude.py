"""Settings for calling Claude through the Anthropic SDK."""

from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import SettingsConfigDict

from .base import EnvSettings


class ClaudeSettings(EnvSettings):
    """Which Claude model to call, and the credential to call it with.

    Each field reads from a `CLAUDE_` variable, e.g. `CLAUDE_MODEL`.

    Attributes:
        model: Claude model ID.
        max_output_tokens: Upper limit on tokens in one response.
        api_key: When set, the credential used to authenticate API calls.
        auth_token: When set, the credential used to authenticate API calls.

    Warning:
        Exactly one of the credentials should be set, never both.
    """

    model_config = SettingsConfigDict(env_prefix="CLAUDE_")

    model: str = "claude-opus-5-5"
    max_output_tokens: int = 16000
    api_key: SecretStr | None = None
    auth_token: SecretStr | None = None

    def credentials(self) -> tuple[str | None, str | None]:
        """Return the API key or auth token.

        Returns:
            `(api_key, auth_token)`, with the unused one as None.

        Raises:
            ValueError: If neither or both credentials are set.
        """
        api_key = self.api_key.get_secret_value() if self.api_key else None
        auth_token = self.auth_token.get_secret_value() if self.auth_token else None
        if (api_key is None) == (auth_token is None):
            raise ValueError("set exactly one of CLAUDE_API_KEY or CLAUDE_AUTH_TOKEN")
        return api_key, auth_token


@lru_cache
def get_claude_settings() -> ClaudeSettings:
    """Return the Claude settings, loading them on first use."""
    return ClaudeSettings()
