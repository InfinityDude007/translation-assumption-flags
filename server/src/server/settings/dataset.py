"""Settings for fetching the dataset."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import SettingsConfigDict

from .base import REPO_DIR, EnvSettings


class DatasetSettings(EnvSettings):
    """Settings for fetching dataset from Zenodo.

    Each field can be overridden with a `DATASET_` variable, e.g. `DATASET_RAW_DIR`.

    Attributes:
        record_url: Zenodo record holding the archives (CC BY 4.0).
        chunk_size: Bytes read per step when downloading and hashing.
        raw_dir: Where the extracted dataset goes (git-ignored).
    """

    model_config = SettingsConfigDict(env_prefix="DATASET_")

    record_url: str = "https://zenodo.org/api/records/10447705/files"
    chunk_size: int = 1 << 20
    raw_dir: Path = REPO_DIR / "data" / "raw"


@lru_cache
def get_dataset_settings() -> DatasetSettings:
    """Return the dataset settings, loading them on first use."""
    return DatasetSettings()
