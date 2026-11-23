"""Append-only log of reviewer decisions, one JSON object per line."""

from datetime import UTC, datetime
from pathlib import Path

from .models import Decision, DecisionRequest


def save_decision(path: Path, request: DecisionRequest) -> Decision:
    """Timestamp a decision and append it to the log.

    Earlier decisions on the same flag are kept, so the log is a full history.

    Args:
        path: The JSON Lines log file, created if missing.
        request: The reviewer's decision.

    Returns:
        The logged decision.
    """
    decision = Decision(**request.model_dump(), decided_at=datetime.now(UTC))
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as log:
        log.write(decision.model_dump_json() + "\n")
    return decision


def load_decisions(
    path: Path, sample_id: str | None = None, run: str | None = None
) -> list[Decision]:
    """Read logged decisions, oldest first, optionally for one sample or run.

    Args:
        path: The JSON Lines log file.
        sample_id: If given, only decisions on this sample.
        run: If given, only decisions made on this archived run.

    Returns:
        The matching decisions.
    """
    if not path.exists():
        return []
    decisions = [
        Decision.model_validate_json(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    return [
        d
        for d in decisions
        if (sample_id is None or d.sample_id == sample_id)
        and (run is None or d.run == run)
    ]
