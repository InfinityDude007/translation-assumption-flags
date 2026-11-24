"""Settings for the token-probability baseline."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import SettingsConfigDict

from .base import REPO_DIR, EnvSettings


class BaselineSettings(EnvSettings):
    """Which local model scores the tokens, where results go, and how much is marked.

    Each field reads from a `BASELINE_` variable, e.g. `BASELINE_MODEL`.

    Attributes:
        baselines_dir: Where each named baseline is saved (committed, as evidence).
        model: Hugging Face model ID of the local scoring model.
        line_budget: How many Java lines each baseline marks, over every sample.
    """

    model_config = SettingsConfigDict(env_prefix="BASELINE_")

    baselines_dir: Path = REPO_DIR / "data" / "baselines"
    model: str = "Qwen/Qwen2.5-Coder-1.5B-Instruct"
    line_budget: int = 70


@lru_cache
def get_baseline_settings() -> BaselineSettings:
    """Return the baseline settings, loading them on first use."""
    return BaselineSettings()
