"""Commands to archive explainer runs over the samples and to score them."""

import argparse
import sys

from ..gemini import GeminiClient, GeminiError, get_client
from ..settings import (
    get_dataset_settings,
    get_evaluation_settings,
    get_gemini_settings,
)
from .archive import run_samples
from .scoring import format_score, score_run


def evaluate() -> None:
    """Explain every sample not yet in the named run, archiving each result.

    Usage: evaluate --name RUN [--model MODEL] [--samples ID ...]
    """
    parser = argparse.ArgumentParser(prog="evaluate", description=evaluate.__doc__)
    parser.add_argument("--name", required=True, help="run name, e.g. hydrogen-v1")
    parser.add_argument("--model", help="Gemini model ID; GEMINI_MODEL if omitted")
    parser.add_argument("--samples", nargs="+", help="only these sample ids")
    args = parser.parse_args()

    try:
        if args.model:
            gemini = get_gemini_settings()
            client = GeminiClient(args.model, gemini.max_output_tokens, gemini.key())
        else:
            client = get_client()

        evaluation = get_evaluation_settings()
        done = run_samples(
            client,
            args.name,
            get_dataset_settings().samples_dir,
            evaluation.runs_dir,
            evaluation.pause_seconds,
            args.samples,
        )

    except (GeminiError, ValueError) as error:
        sys.exit(f"evaluate: {error}\nRun the same command again to resume.")

    print(f"{len(done)} samples explained in run {args.name!r}")


def score() -> None:
    """Score a named run, print the table and save it as score.json in the run.

    Usage: score RUN
    """
    parser = argparse.ArgumentParser(prog="score", description=score.__doc__)
    parser.add_argument("name", help="run name, e.g. hydrogen-v1")
    args = parser.parse_args()

    run_dir = get_evaluation_settings().runs_dir / args.name
    if not run_dir.is_dir():
        sys.exit(f"score: no run named {args.name!r} in {run_dir.parent}")

    result = score_run(run_dir, get_dataset_settings().samples_dir)
    (run_dir / "score.json").write_text(result.model_dump_json(indent=2) + "\n")
    print(format_score(result))
