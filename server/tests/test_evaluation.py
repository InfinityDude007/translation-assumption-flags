"""Tests for archiving explainer runs and scoring them against the tags."""

from pathlib import Path

import pytest
from pydantic import BaseModel

from server.dataset import SampleMeta
from server.dataset.models import BugLines
from server.evaluation.archive import CONFIG_FILE, run_samples
from server.evaluation.models import RunConfig, SampleRun
from server.evaluation.scoring import format_score, score_run
from server.explanation.models import GeminiAnswer, SiteAnswer
from server.explanation.prompts import PROMPT_VERSION
from server.gemini import GeminiClient, GeminiError

SOURCE = "n = int(input())\nprint(n // 2)\n"
"""Three sites: ids 0 and 1 on line 1, id 2 on line 2."""

TRANSLATION = "\n".join(
    [
        "import java.util.Scanner;",
        "public class Main {",
        "    public static void main(String[] args) {",
        "        int n = new Scanner(System.in).nextInt();",
        "        System.out.println(n / 2);",
        "    }",
        "}",
    ]
)

ANSWER = GeminiAnswer(
    answers=[
        SiteAnswer.model_validate(
            {
                "site_id": site_id,
                "verdict": verdict,
                "translation_lines": [line],
                "assumption": "assumes something",
                "suggestion": None,
                "reasoning": "working",
            }
        )
        for site_id, verdict, line in [
            (0, "mismatch", 4),
            (1, "handled", 4),
            (2, "mismatch", 5),
        ]
    ]
)
"""Every sample gets mismatch flags on Java lines 4 and 5, and one handled flag."""


class FakeClient(GeminiClient):
    """A Gemini client that returns ANSWER, and can fail on chosen calls."""

    def __init__(self, fail_on: int | None = None) -> None:
        """Set the model name and, optionally, which call (1-based) should fail."""
        self._model = "gemini-test"
        self.calls = 0
        self.fail_on = fail_on

    def complete[T: BaseModel](self, system: str, prompt: str, schema: type[T]) -> T:
        """Count the call, fail if asked, and return ANSWER validated as `schema`."""
        self.calls += 1
        if self.calls == self.fail_on:
            raise GeminiError("Gemini request failed: 429")
        return schema.model_validate(ANSWER.model_dump())


def add_sample(
    samples: Path,
    sample_id: str,
    group: str = "buggy",
    bug: list[int] | None = None,
    latent: list[int] | None = None,
) -> None:
    """Write a sample folder with the shared program and the given tags."""
    folder = samples / sample_id
    folder.mkdir(parents=True)
    (folder / "source.py").write_text(SOURCE)
    (folder / "translation.java").write_text(TRANSLATION)
    meta = SampleMeta.model_validate(
        {
            "id": sample_id,
            "dataset": "avatar",
            "program": sample_id,
            "group": group,
            "pan_labels": [],
            "tests": [],
            "bug_lines": BugLines(translation=bug or []),
            "latent": BugLines(translation=latent or []),
        }
    )
    (folder / "meta.json").write_text(meta.model_dump_json())


@pytest.fixture
def samples(tmp_path: Path) -> Path:
    """Four samples: a bug, a control with a latent bug, a no-bug, and one more."""
    folder = tmp_path / "samples"
    add_sample(folder, "a", bug=[5])
    add_sample(folder, "b", group="control", latent=[4])
    add_sample(folder, "c")
    add_sample(folder, "d", bug=[2])
    return folder


def run(
    client: FakeClient, samples: Path, runs: Path, ids: list[str] | None = None
) -> tuple[list[str], list[float]]:
    """Run the archive into `runs`, recording the pauses instead of sleeping."""
    pauses: list[float] = []
    done = run_samples(client, "test", samples, runs, 1.5, ids, sleep=pauses.append)
    return done, pauses


def test_each_sample_is_archived_with_the_run_config(
    samples: Path, tmp_path: Path
) -> None:
    """Every sample is saved, the run records its model and prompt, and calls are paced."""
    runs = tmp_path / "runs"
    done, pauses = run(FakeClient(), samples, runs)
    assert done == ["a", "b", "c", "d"]
    assert pauses == [1.5, 1.5, 1.5]
    config = RunConfig.model_validate_json((runs / "test" / CONFIG_FILE).read_text())
    assert (config.model, config.prompt_version) == ("gemini-test", PROMPT_VERSION)
    saved = SampleRun.model_validate_json((runs / "test" / "a.json").read_text())
    assert saved.explanation.answer == ANSWER


def test_a_rerun_skips_saved_samples(samples: Path, tmp_path: Path) -> None:
    """Only samples missing from the run are sent again."""
    runs = tmp_path / "runs"
    run(FakeClient(), samples, runs, ["a", "c"])
    client = FakeClient()
    done, _ = run(client, samples, runs)
    assert done == ["b", "d"] and client.calls == 2


def test_a_failed_call_stops_and_the_next_run_resumes(
    samples: Path, tmp_path: Path
) -> None:
    """Samples before a failure stay saved, and the failed one is retried next time."""
    runs = tmp_path / "runs"
    with pytest.raises(GeminiError):
        run(FakeClient(fail_on=2), samples, runs)
    assert sorted(p.name for p in (runs / "test").glob("?.json")) == ["a.json"]
    done, _ = run(FakeClient(), samples, runs)
    assert done == ["b", "c", "d"]


def test_a_run_name_cannot_mix_models(samples: Path, tmp_path: Path) -> None:
    """Reusing a run name with another model is refused."""
    runs = tmp_path / "runs"
    run(FakeClient(), samples, runs, ["a"])
    other = FakeClient()
    other._model = "gemini-other"
    with pytest.raises(ValueError, match="new run name"):
        run(other, samples, runs)


def test_scoring_counts_mismatch_flags_against_the_tags(
    samples: Path, tmp_path: Path
) -> None:
    """Hits, latent hits, false alarms and gaps are counted correctly."""
    runs = tmp_path / "runs"
    run(FakeClient(), samples, runs, ["a", "b", "c"])
    score = score_run(runs / "test", samples)

    by_id = {s.sample_id: s for s in score.samples}
    assert (by_id["a"].bug_caught, by_id["a"].false_alarms) == (True, 1)
    assert (by_id["b"].latent_caught, by_id["b"].false_alarms) == (True, 1)
    assert by_id["b"].bug_caught is None and by_id["c"].no_bug
    assert by_id["a"].handled == 1 and by_id["a"].dropped == 0

    assert (score.bugs, score.bugs_caught) == (1, 1)
    assert (score.latent, score.latent_caught) == (1, 1)
    assert (score.mismatch_flags, score.false_alarms) == (6, 4)
    assert score.missing == ["d"]


def test_a_missed_bug_is_reported(samples: Path, tmp_path: Path) -> None:
    """A bug whose line no mismatch flag touches counts as missed."""
    runs = tmp_path / "runs"
    run(FakeClient(), samples, runs, ["d"])
    score = score_run(runs / "test", samples)
    assert score.samples[0].bug_caught is False
    assert (score.bugs, score.bugs_caught, score.false_alarms) == (1, 0, 2)
    assert "Test-exposed bugs caught: 0/1" in format_score(score)
