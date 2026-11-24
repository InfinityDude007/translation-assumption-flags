"""Commands to score the translations with a local model, and to score the result."""

import argparse
import sys

from ..settings import get_baseline_settings, get_dataset_settings
from .archive import run_baseline
from .scoring import format_baseline_score, score_baseline


def baseline() -> None:
    """Score every sample's Java tokens with a local model, saving each result.

    Usage: baseline --name NAME [--model MODEL] [--samples ID ...]
    """
    parser = argparse.ArgumentParser(prog="baseline", description=baseline.__doc__)
    parser.add_argument("--name", required=True, help="baseline name, e.g. qwen-1.5b")
    parser.add_argument(
        "--model", help="Hugging Face model ID; BASELINE_MODEL if omitted"
    )
    parser.add_argument("--samples", nargs="+", help="only these sample ids")
    args = parser.parse_args()

    from .scorer import (  # torch is slow to import, so done at runtime
        PROMPT_VERSION,
        TokenScorer,
    )

    settings = get_baseline_settings()
    scorer = TokenScorer(args.model or settings.model)
    try:
        done = run_baseline(
            scorer,
            args.name,
            PROMPT_VERSION,
            get_dataset_settings().samples_dir,
            settings.baselines_dir,
            args.samples,
        )
    except ValueError as error:
        sys.exit(f"baseline: {error}")

    print(f"{len(done)} samples scored in baseline {args.name!r}")


def score_baseline_command() -> None:
    """Score a named baseline, print the table and save it as score.json in it.

    Usage: score-baseline NAME [--threshold P]
    """
    parser = argparse.ArgumentParser(
        prog="score-baseline", description=score_baseline_command.__doc__
    )
    parser.add_argument("name", help="baseline name, e.g. qwen-1.5b")
    parser.add_argument(
        "--threshold",
        type=float,
        help="highlight below this; BASELINE_THRESHOLD if omitted",
    )
    args = parser.parse_args()

    settings = get_baseline_settings()
    folder = settings.baselines_dir / args.name
    if not folder.is_dir():
        sys.exit(f"score-baseline: no baseline named {args.name!r} in {folder.parent}")

    threshold = settings.threshold if args.threshold is None else args.threshold
    result = score_baseline(folder, get_dataset_settings().samples_dir, threshold)
    (folder / "score.json").write_text(result.model_dump_json(indent=2) + "\n")
    print(format_baseline_score(result))
