"""FastAPI app serving samples, flags, token probabilities and reviewer decisions."""

from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from ..baseline.archive import CONFIG_FILE as BASELINE_CONFIG
from ..baseline.models import BaselineConfig, BaselineScore, SampleBaseline
from ..baseline.scoring import score_baseline
from ..dataset import SampleMeta
from ..evaluation.archive import CONFIG_FILE, load_samples
from ..evaluation.models import RunConfig, RunScore, SampleRun
from ..evaluation.scoring import score_run
from ..explanation import explain
from ..gemini import GeminiClient, GeminiError, get_client
from .decisions import load_decisions, save_decision
from .models import (
    AnalyseRequest,
    BaselineSummary,
    Decision,
    DecisionRequest,
    ProbabilityReview,
    Review,
    RunSummary,
    SampleCode,
    SampleSummary,
)

PASSED_ON = {status.HTTP_429_TOO_MANY_REQUESTS, status.HTTP_503_SERVICE_UNAVAILABLE}
"""Gemini statuses passed to the frontend as they are; others become 502."""


def gemini_client() -> GeminiClient:
    """Return the shared Gemini client for live analysis.

    Raises:
        HTTPException: 503 if no Gemini API key is set.
    """
    try:
        return get_client()
    except ValueError as error:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(error)) from error


def create_app(
    samples_dir: Path,
    runs_dir: Path,
    decisions_file: Path,
    cors_origins: list[str],
    baselines_dir: Path | None = None,
    threshold: float = 0.05,
) -> FastAPI:
    """Build the API over the given folders.

    Args:
        samples_dir: The samples folder.
        runs_dir: The archived runs folder.
        decisions_file: JSON Lines file for reviewer decisions.
        cors_origins: Browser origins allowed to call the API.
        baselines_dir: The token-probability baselines folder; none if omitted.
        threshold: Lines whose least likely token is below this are highlighted.

    Returns:
        The app.
    """
    app = FastAPI(title="Translation assumption flags")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )

    def find_sample(sample_id: str) -> SampleMeta:
        """Look a sample up by id, so ids never become paths unchecked."""
        for meta in load_samples(samples_dir):
            if meta.id == sample_id:
                return meta
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"no sample {sample_id!r}")

    def find_runs() -> dict[str, RunConfig]:
        """Read every archived run's config, by run name."""
        if not runs_dir.is_dir():
            return {}
        configs = (
            RunConfig.model_validate_json(path.read_text())
            for path in sorted(runs_dir.glob(f"*/{CONFIG_FILE}"))
        )
        return {config.name: config for config in configs}

    def find_baselines() -> dict[str, BaselineConfig]:
        """Read every baseline's config, by baseline name."""
        if baselines_dir is None or not baselines_dir.is_dir():
            return {}
        configs = (
            BaselineConfig.model_validate_json(path.read_text())
            for path in sorted(baselines_dir.glob(f"*/{BASELINE_CONFIG}"))
        )
        return {config.name: config for config in configs}

    def baseline_folder(name: str) -> Path:
        """Return a baseline's folder, after checking the name is a real baseline."""
        if baselines_dir is None or name not in find_baselines():
            raise HTTPException(status.HTTP_404_NOT_FOUND, f"no baseline {name!r}")
        return baselines_dir / name

    @app.get("/samples")
    def list_samples() -> list[SampleSummary]:
        """List the samples, leaving out their labels and tagged lines."""
        return [
            SampleSummary(id=meta.id, dataset=meta.dataset, program=meta.program)
            for meta in load_samples(samples_dir)
        ]

    @app.get("/samples/{sample_id}")
    def get_sample(sample_id: str) -> SampleCode:
        """Return a sample's Python source and Java translation."""
        folder = samples_dir / find_sample(sample_id).id
        return SampleCode(
            id=sample_id,
            source=(folder / "source.py").read_text(),
            translation=(folder / "translation.java").read_text(),
        )

    @app.get("/runs")
    def list_runs() -> list[RunSummary]:
        """List the archived runs and how many samples each holds."""
        return [
            RunSummary(
                **config.model_dump(),
                samples=sum(
                    1
                    for path in (runs_dir / name).glob("*.json")
                    if path.name not in (CONFIG_FILE, "score.json")
                ),
            )
            for name, config in find_runs().items()
        ]

    @app.get("/runs/{run}/samples/{sample_id}")
    def get_archived_review(run: str, sample_id: str) -> Review:
        """Return a sample's archived flags from a run, without calling Gemini."""
        if run not in find_runs():
            raise HTTPException(status.HTTP_404_NOT_FOUND, f"no run {run!r}")
        path = runs_dir / run / f"{find_sample(sample_id).id}.json"
        if not path.exists():
            raise HTTPException(
                status.HTTP_404_NOT_FOUND, f"run {run!r} has no {sample_id!r}"
            )
        archived = SampleRun.model_validate_json(path.read_text())
        return Review.from_explanation(archived.explanation, run)

    @app.get("/runs/{run}/score")
    def get_score(run: str) -> RunScore:
        """Score a run against the tagged lines, over the samples archived so far.

        This route shows the ground truth, so the review pages never call it.
        """
        if run not in find_runs():
            raise HTTPException(status.HTTP_404_NOT_FOUND, f"no run {run!r}")
        return score_run(runs_dir / run, samples_dir)

    @app.get("/baselines")
    def list_baselines() -> list[BaselineSummary]:
        """List the token-probability baselines and how many samples each holds."""
        return [
            BaselineSummary(
                **config.model_dump(),
                samples=sum(
                    1
                    for path in baseline_folder(name).glob("*.json")
                    if path.name not in (BASELINE_CONFIG, "score.json")
                ),
            )
            for name, config in find_baselines().items()
        ]

    @app.get("/baselines/{name}/samples/{sample_id}")
    def get_probabilities(name: str, sample_id: str) -> ProbabilityReview:
        """Return a sample's token probabilities from a baseline."""
        folder = baseline_folder(name)
        path = folder / f"{find_sample(sample_id).id}.json"
        if not path.exists():
            raise HTTPException(
                status.HTTP_404_NOT_FOUND, f"baseline {name!r} has no {sample_id!r}"
            )
        scored = SampleBaseline.model_validate_json(path.read_text())
        return ProbabilityReview(
            baseline=name,
            model=find_baselines()[name].model,
            threshold=threshold,
            lines=scored.lines,
        )

    @app.get("/baselines/{name}/score")
    def get_baseline_score(name: str) -> BaselineScore:
        """Score a baseline against the tagged lines at the configured threshold.

        Like the run scores, this shows the ground truth, so the review pages
        never call it.
        """
        return score_baseline(baseline_folder(name), samples_dir, threshold)

    @app.post("/analyse")
    def analyse(
        request: AnalyseRequest,
        client: Annotated[GeminiClient, Depends(gemini_client)],
    ) -> Review:
        """Detect and explain the sites in a program now, calling Gemini."""
        try:
            explanation = explain(request.source, request.translation, client)
        except ValueError as error:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_CONTENT, str(error)
            ) from error
        except GeminiError as error:
            code = error.status if error.status in PASSED_ON else None
            raise HTTPException(
                code or status.HTTP_502_BAD_GATEWAY, str(error)
            ) from error
        return Review.from_explanation(explanation, None)

    @app.post("/decisions", status_code=status.HTTP_201_CREATED)
    def add_decision(request: DecisionRequest) -> Decision:
        """Log a reviewer's decision on a flag."""
        return save_decision(decisions_file, request)

    @app.get("/decisions")
    def list_decisions(
        sample_id: str | None = None, run: str | None = None
    ) -> list[Decision]:
        """List logged decisions, oldest first, for one sample or run if given."""
        return load_decisions(decisions_file, sample_id, run)

    return app
