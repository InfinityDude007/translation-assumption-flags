"""Base settings class and project paths."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

SERVER_DIR = Path(__file__).resolve().parents[3]
"""The server project folder, which holds pyproject.toml and .env."""

REPO_DIR = SERVER_DIR.parent
"""The repository root."""


class EnvSettings(BaseSettings):
    """Base for settings sections; reads `server/.env` as well as process variables."""

    model_config = SettingsConfigDict(
        env_file=SERVER_DIR / ".env", env_file_encoding="utf-8", extra="ignore"
    )
