"""Settings for serving the review API."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import SettingsConfigDict

from .base import REPO_DIR, EnvSettings


class ApiSettings(EnvSettings):
    """Where the API listens, who may call it, and where decisions are logged.

    Each field reads from an `API_` variable, e.g. `API_PORT`.

    Attributes:
        host: Address to listen on.
        port: Port to listen on.
        cors_origins: Browser origins allowed to call the API (the frontend).
        decisions_file: JSON Lines file that reviewer decisions are appended to.
    """

    model_config = SettingsConfigDict(env_prefix="API_")

    host: str = "127.0.0.1"
    port: int = 8000
    cors_origins: list[str] = ["http://localhost:5173"]
    decisions_file: Path = REPO_DIR / "data" / "decisions.jsonl"


@lru_cache
def get_api_settings() -> ApiSettings:
    """Return the API settings, loading them on first use."""
    return ApiSettings()
