"""Score a baseline's highlighted lines against the hand-tagged lines."""

from pathlib import Path

from ..dataset import SampleMeta
from ..evaluation.archive import load_samples
from .archive import CONFIG_FILE
from .models import BaselineConfig, BaselineSampleScore, BaselineScore, SampleBaseline


def score_baseline_sample(
    meta: SampleMeta, baseline: SampleBaseline, threshold: float
) -> BaselineSampleScore:
    """Compare one sample's highlighted lines with its tagged Java lines.

    Args:
        meta: The sample's metadata and tags.
        baseline: Its token probabilities.
        threshold: Lines whose least likely token is below this are highlighted.

    Returns:
        The sample's score.
    """
    bug = set(meta.bug_lines.translation)
    latent = set(meta.latent.translation)
    highlighted = [line.line for line in baseline.lines if line.lowest < threshold]
    ranked = [
        line.line for line in sorted(baseline.lines, key=lambda line: line.lowest)
    ]

    return BaselineSampleScore(
        sample_id=meta.id,
        group=meta.group,
        no_bug=meta.group == "buggy" and not bug,
        bug_lines=sorted(bug),
        latent_lines=sorted(latent),
        highlighted=highlighted,
        bug_caught=bool(bug.intersection(highlighted)) if bug else None,
        latent_caught=bool(latent.intersection(highlighted)) if latent else None,
        false_alarms=sum(1 for line in highlighted if line not in bug | latent),
        bug_rank=(
            next(rank for rank, line in enumerate(ranked, 1) if line in bug)
            if bug
            else None
        ),
    )


def score_baseline(folder: Path, samples_dir: Path, threshold: float) -> BaselineScore:
    """Score every sample in a baseline at one threshold and total them.

    Args:
        folder: The baseline's folder.
        samples_dir: The samples folder.
        threshold: Lines whose least likely token is below this are highlighted.

    Returns:
        Per-sample scores and totals.
    """
    config = BaselineConfig.model_validate_json((folder / CONFIG_FILE).read_text())
    scores: list[BaselineSampleScore] = []
    missing: list[str] = []

    for meta in load_samples(samples_dir):
        path = folder / f"{meta.id}.json"
        if not path.exists():
            missing.append(meta.id)
            continue
        baseline = SampleBaseline.model_validate_json(path.read_text())
        scores.append(score_baseline_sample(meta, baseline, threshold))

    return BaselineScore(
        config=config,
        threshold=threshold,
        samples=scores,
        bugs=sum(1 for score in scores if score.bug_caught is not None),
        bugs_caught=sum(1 for score in scores if score.bug_caught),
        latent=sum(1 for score in scores if score.latent_caught is not None),
        latent_caught=sum(1 for score in scores if score.latent_caught),
        highlighted=sum(len(score.highlighted) for score in scores),
        false_alarms=sum(score.false_alarms for score in scores),
        missing=missing,
    )


def format_baseline_score(score: BaselineScore) -> str:
    """Render a baseline's score as a plain-text table with totals.

    Args:
        score: The baseline's score.

    Returns:
        One row per sample, then the totals.
    """

    def mark(value: bool | None) -> str:
        """Show caught, missed or not applicable."""
        return "-" if value is None else ("yes" if value else "no")

    rows = [
        f"Baseline {score.config.name}: {score.config.model}, prompt v"
        f"{score.config.prompt_version}, threshold {score.threshold}",
        "",
        f"{'sample':32} {'group':8} {'bug':4} {'latent':6} {'lines':5} "
        f"{'false':5} {'rank':4}",
    ]
    for s in score.samples:
        rank = "-" if s.bug_rank is None else str(s.bug_rank)
        rows.append(
            f"{s.sample_id:32} {s.group:8} {mark(s.bug_caught):4} "
            f"{mark(s.latent_caught):6} {len(s.highlighted):5} {s.false_alarms:5} "
            f"{rank:4}" + ("  (no translation bug)" if s.no_bug else "")
        )

    rows += [
        "",
        f"Test-exposed bugs caught: {score.bugs_caught}/{score.bugs}",
        f"Latent bugs caught:       {score.latent_caught}/{score.latent}",
        f"Highlighted lines:        {score.highlighted}, "
        f"of which false alarms: {score.false_alarms}",
    ]
    if score.missing:
        rows.append(f"Not yet scored:           {len(score.missing)} samples")
    return "\n".join(rows)
