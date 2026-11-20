"""Run the explainer over the samples and archive each result, resuming after a stop."""

import time
from collections.abc import Callable, Iterable
from datetime import UTC, datetime
from pathlib import Path

from ..dataset import SampleMeta
from ..explanation import explain
from ..explanation.prompts import PROMPT_VERSION
from ..gemini import GeminiClient
from .models import RunConfig, SampleRun

CONFIG_FILE = "run.json"
"""File in each run folder holding its RunConfig."""


def load_samples(samples_dir: Path) -> list[SampleMeta]:
    """Read every sample's meta.json, sorted by sample id.

    Args:
        samples_dir: The samples folder.

    Returns:
        The samples' metadata.
    """
    return [
        SampleMeta.model_validate_json(path.read_text())
        for path in sorted(samples_dir.glob("*/meta.json"))
    ]


def open_run(run_dir: Path, name: str, model: str) -> RunConfig:
    """Create a run folder, or reopen one made with the same model and prompt.

    Args:
        run_dir: The run's folder.
        name: Run name.
        model: Gemini model ID for this run.

    Returns:
        The run's configuration.

    Raises:
        ValueError: If the run exists with a different model or prompt version.
    """
    config_path = run_dir / CONFIG_FILE
    if config_path.exists():
        config = RunConfig.model_validate_json(config_path.read_text())

        if (config.model, config.prompt_version) != (model, PROMPT_VERSION):
            raise ValueError(
                f"run {name!r} used {config.model} with prompt v"
                f"{config.prompt_version}; pick a new run name"
            )
        return config

    config = RunConfig(
        name=name,
        model=model,
        prompt_version=PROMPT_VERSION,
        created_at=datetime.now(UTC),
    )

    run_dir.mkdir(parents=True)
    config_path.write_text(config.model_dump_json(indent=2) + "\n")

    return config


def run_samples(
    client: GeminiClient,
    name: str,
    samples_dir: Path,
    runs_dir: Path,
    pause_seconds: float,
    sample_ids: Iterable[str] | None = None,
    sleep: Callable[[float], None] = time.sleep,
) -> list[str]:
    """Explain each sample not yet archived in the run, saving each as it finishes.

    A failed call stops the run with nothing saved for that sample, so running
    the same command again carries on from it.

    Args:
        client: Gemini client; its model is recorded with the run.
        name: Run name.
        samples_dir: The samples folder.
        runs_dir: Folder holding every run.
        pause_seconds: Wait between calls.
        sample_ids: Only these samples; every sample if omitted.
        sleep: Pause function, replaceable in tests.

    Returns:
        Ids of the samples explained in this call.

    Raises:
        ValueError: If the run exists with a different model or prompt version.
        GeminiError: If a call fails; earlier samples stay saved.
    """
    run_dir = runs_dir / name
    open_run(run_dir, name, client.model)
    wanted = set(sample_ids) if sample_ids is not None else None
    done: list[str] = []

    for meta in load_samples(samples_dir):
        out = run_dir / f"{meta.id}.json"
        if out.exists() or (wanted is not None and meta.id not in wanted):
            continue
        if done:
            sleep(pause_seconds)

        folder = samples_dir / meta.id
        start = time.monotonic()

        explanation = explain(
            (folder / "source.py").read_text(),
            (folder / "translation.java").read_text(),
            client,
        )

        record = SampleRun(
            sample_id=meta.id,
            finished_at=datetime.now(UTC),
            seconds=round(time.monotonic() - start, 2),
            explanation=explanation,
        )

        out.write_text(record.model_dump_json(indent=2) + "\n")
        done.append(meta.id)

        print(f"{meta.id}: {len(explanation.flags)} flags ({record.seconds}s)")

    return done
