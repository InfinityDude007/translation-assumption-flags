"""Settings for the token-probability baseline."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import SettingsConfigDict

from .base import REPO_DIR, EnvSettings


class BaselineSettings(EnvSettings):
    """Which local model scores the tokens, where results go, and what is highlighted.

    Each field reads from a `BASELINE_` variable, e.g. `BASELINE_MODEL`.

    Attributes:
        baselines_dir: Where each named baseline is saved (committed, as evidence).
        model: Hugging Face model ID of the local scoring model.
        threshold: Lines whose least likely token is below this are highlighted.
    """

    model_config = SettingsConfigDict(env_prefix="BASELINE_")

    baselines_dir: Path = REPO_DIR / "data" / "baselines"
    model: str = "Qwen/Qwen2.5-Coder-1.5B-Instruct"
    threshold: float = 0.05


@lru_cache
def get_baseline_settings() -> BaselineSettings:
    """Return the baseline settings, loading them on first use."""
    return BaselineSettings()
