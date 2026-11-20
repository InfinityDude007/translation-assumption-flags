"""Settings for archiving and scoring explainer runs."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import SettingsConfigDict

from .base import REPO_DIR, EnvSettings


class EvaluationSettings(EnvSettings):
    """Where explainer runs are archived, and how fast samples are sent.

    Each field reads from an `EVALUATION_` variable, e.g. `EVALUATION_RUNS_DIR`.

    Attributes:
        runs_dir: Where each named run is saved (committed, as testing evidence).
        pause_seconds: Wait between Gemini calls, to stay under rate limits.
    """

    model_config = SettingsConfigDict(env_prefix="EVALUATION_")

    runs_dir: Path = REPO_DIR / "data" / "runs"
    pause_seconds: float = 6.0


@lru_cache
def get_evaluation_settings() -> EvaluationSettings:
    """Return the evaluation settings, loading them on first use."""
    return EvaluationSettings()
