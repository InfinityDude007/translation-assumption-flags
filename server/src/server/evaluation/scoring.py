"""Score an archived run's mismatch flags against the hand-tagged lines."""

from pathlib import Path

from ..dataset import SampleMeta
from .archive import CONFIG_FILE, load_samples
from .models import RunConfig, RunScore, SampleRun, SampleScore


def score_sample(meta: SampleMeta, run: SampleRun) -> SampleScore:
    """Compare one sample's mismatch flags with its tagged Java lines.

    Args:
        meta: The sample's metadata and tags.
        run: The archived explainer result for it.

    Returns:
        The sample's score.
    """
    bug = set(meta.bug_lines.translation)
    latent = set(meta.latent.translation)
    flags = run.explanation.flags
    mismatch = [
        set(flag.translation_lines) for flag in flags if flag.verdict == "mismatch"
    ]

    return SampleScore(
        sample_id=meta.id,
        group=meta.group,
        no_bug=meta.group == "buggy" and not bug,
        bug_lines=sorted(bug),
        latent_lines=sorted(latent),
        mismatch_flags=len(mismatch),
        bug_caught=any(lines & bug for lines in mismatch) if bug else None,
        latent_caught=any(lines & latent for lines in mismatch) if latent else None,
        false_alarms=sum(1 for lines in mismatch if not lines & (bug | latent)),
        handled=sum(1 for flag in flags if flag.verdict == "handled"),
        unclear=sum(1 for flag in flags if flag.verdict == "unclear"),
        dropped=len(run.explanation.dropped),
    )


def score_run(run_dir: Path, samples_dir: Path) -> RunScore:
    """Score every archived sample in a run and total them.

    Args:
        run_dir: The run's folder.
        samples_dir: The samples folder.

    Returns:
        Per-sample scores and run totals.
    """
    config = RunConfig.model_validate_json((run_dir / CONFIG_FILE).read_text())
    scores: list[SampleScore] = []
    missing: list[str] = []

    for meta in load_samples(samples_dir):
        path = run_dir / f"{meta.id}.json"
        if not path.exists():
            missing.append(meta.id)
            continue
        scores.append(
            score_sample(meta, SampleRun.model_validate_json(path.read_text()))
        )

    return RunScore(
        config=config,
        samples=scores,
        bugs=sum(1 for score in scores if score.bug_caught is not None),
        bugs_caught=sum(1 for score in scores if score.bug_caught),
        latent=sum(1 for score in scores if score.latent_caught is not None),
        latent_caught=sum(1 for score in scores if score.latent_caught),
        mismatch_flags=sum(score.mismatch_flags for score in scores),
        false_alarms=sum(score.false_alarms for score in scores),
        missing=missing,
    )


def format_score(score: RunScore) -> str:
    """Render a run's score as a plain-text table with totals.

    Args:
        score: The run's score.

    Returns:
        One row per sample, then the totals.
    """

    def mark(value: bool | None) -> str:
        """Show caught, missed or not applicable."""
        return "-" if value is None else ("yes" if value else "no")

    rows = [
        f"Run {score.config.name}: {score.config.model}, prompt v"
        f"{score.config.prompt_version}",
        "",
        f"{'sample':32} {'group':8} {'bug':4} {'latent':6} {'flags':5} "
        f"{'false':5} {'handled':7} {'unclear':7} {'dropped':7}",
    ]

    for s in score.samples:
        rows.append(
            f"{s.sample_id:32} {s.group:8} {mark(s.bug_caught):4} "
            f"{mark(s.latent_caught):6} {s.mismatch_flags:5} {s.false_alarms:5} "
            f"{s.handled:7} {s.unclear:7} {s.dropped:7}"
            + ("  (no translation bug)" if s.no_bug else "")
        )

    rows += [
        "",
        f"Test-exposed bugs caught: {score.bugs_caught}/{score.bugs}",
        f"Latent bugs caught:       {score.latent_caught}/{score.latent}",
        f"Mismatch flags:           {score.mismatch_flags}, "
        f"of which false alarms: {score.false_alarms}",
    ]

    if score.missing:
        rows.append(f"Not yet run:              {len(score.missing)} samples")

    return "\n".join(rows)
