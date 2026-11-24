"""Score each sample's translation and save it, resuming after a stop."""

import time
from collections.abc import Iterable
from datetime import UTC, datetime
from pathlib import Path
from typing import Protocol

from ..evaluation.archive import load_samples
from .models import BaselineConfig, LineProbability, SampleBaseline

CONFIG_FILE = "baseline.json"
"""File in each baseline folder holding its BaselineConfig."""


class Scorer(Protocol):
    """Anything that scores a translation's tokens, e.g. a TokenScorer."""

    model_id: str

    def score(
        self, source: str, translation: str, program: str
    ) -> list[LineProbability]:
        """Score every token of the translation and group them by line."""
        ...


def open_baseline(
    folder: Path, name: str, model: str, prompt_version: str
) -> BaselineConfig:
    """Create a baseline folder, or reopen one made with the same model and prompt.

    Args:
        folder: The baseline's folder.
        name: Baseline name.
        model: Hugging Face model ID.
        prompt_version: Translation prompt version.

    Returns:
        The baseline's configuration.

    Raises:
        ValueError: If the baseline exists with a different model or prompt.
    """
    config_path = folder / CONFIG_FILE
    if config_path.exists():
        config = BaselineConfig.model_validate_json(config_path.read_text())
        if (config.model, config.prompt_version) != (model, prompt_version):
            raise ValueError(
                f"baseline {name!r} used {config.model} with prompt v"
                f"{config.prompt_version}; pick a new name"
            )
        return config

    config = BaselineConfig(
        name=name,
        model=model,
        prompt_version=prompt_version,
        created_at=datetime.now(UTC),
    )
    folder.mkdir(parents=True)
    config_path.write_text(config.model_dump_json(indent=2) + "\n")
    return config


def run_baseline(
    scorer: Scorer,
    name: str,
    prompt_version: str,
    samples_dir: Path,
    baselines_dir: Path,
    sample_ids: Iterable[str] | None = None,
) -> list[str]:
    """Score each sample not yet in the baseline, saving each as it finishes.

    Args:
        scorer: The scoring model; its ID is recorded with the baseline.
        name: Baseline name.
        prompt_version: Version of the prompt the scorer uses.
        samples_dir: The samples folder.
        baselines_dir: Folder holding every baseline.
        sample_ids: Only these samples; every sample if omitted.

    Returns:
        Ids of the samples scored in this call.

    Raises:
        ValueError: If the baseline exists with a different model or prompt.
    """
    folder = baselines_dir / name
    open_baseline(folder, name, scorer.model_id, prompt_version)
    wanted = set(sample_ids) if sample_ids is not None else None
    done: list[str] = []

    for meta in load_samples(samples_dir):
        out = folder / f"{meta.id}.json"
        if out.exists() or (wanted is not None and meta.id not in wanted):
            continue

        sample = samples_dir / meta.id
        start = time.monotonic()
        lines = scorer.score(
            (sample / "source.py").read_text(),
            (sample / "translation.java").read_text(),
            meta.program,
        )
        record = SampleBaseline(
            sample_id=meta.id,
            finished_at=datetime.now(UTC),
            seconds=round(time.monotonic() - start, 2),
            lines=lines,
        )
        out.write_text(record.model_dump_json(indent=2) + "\n")
        done.append(meta.id)

        print(f"{meta.id}: {len(lines)} lines ({record.seconds}s)")

    return done
