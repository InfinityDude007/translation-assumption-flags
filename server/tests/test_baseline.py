"""Tests for the token-probability baseline, with a fake scorer in place of the model."""

from pathlib import Path

import pytest

from server.baseline import (
    CONFIG_FILE,
    BaselineConfig,
    LineProbability,
    SampleBaseline,
    budget_threshold,
    format_baseline_score,
    line_probabilities,
    run_baseline,
    score_baseline,
)
from server.dataset import SampleMeta

TRANSLATION = "int n = in.nextInt();\nSystem.out.println(n / 2);\n"
"""Two lines and a final newline, so three lines when split."""

SAMPLE = "avatar-atcoder_ABC000_A"


def test_lines_split_tokens_at_line_breaks() -> None:
    """A token spanning a break is split, and each line rejoins exactly."""
    first = TRANSLATION.index("\n")
    spans = [
        (0, 4, 0.9),  # "int "
        (4, 20, 0.6),  # "n = in.nextInt()"
        (20, first + 7, 0.02),  # ";\nSystem" spans the break
        (first + 7, len(TRANSLATION), 0.8),
    ]
    lines = line_probabilities(TRANSLATION, spans)

    assert ["".join(t.text for t in line.tokens) for line in lines] == (
        TRANSLATION.split("\n")
    )
    assert lines[0].tokens[-1].text == ";"
    assert lines[1].tokens[0].text == "System"
    assert (lines[0].lowest, lines[1].lowest) == (0.02, 0.02)


def test_whitespace_and_blank_lines_are_not_doubted() -> None:
    """Indentation never sets a line's lowest; a blank line scores 1.0."""
    lines = line_probabilities("  x;\n\n", [(0, 2, 0.01), (2, 4, 0.7), (4, 6, 0.5)])

    assert lines[0].lowest == 0.7
    assert lines[1].lowest == 1.0
    assert lines[1].tokens == []


class FakeScorer:
    """Scores every token 0.5, except 0.01 on the second Java line."""

    model_id = "fake/model"

    def __init__(self) -> None:
        """Count calls, so tests can check resuming."""
        self.calls = 0

    def score(
        self, source: str, translation: str, program: str
    ) -> list[LineProbability]:
        """Give line 2 a low probability and every other line 0.5."""
        self.calls += 1
        lines = line_probabilities(translation, [(0, len(translation), 0.5)])
        lines[1] = lines[1].model_copy(update={"lowest": 0.01})
        return lines


@pytest.fixture
def samples(tmp_path: Path) -> Path:
    """Write one buggy sample whose bug is on Java line 2."""
    folder = tmp_path / "samples" / SAMPLE
    folder.mkdir(parents=True)
    meta = SampleMeta.model_validate(
        {
            "id": SAMPLE,
            "dataset": "avatar",
            "program": "atcoder_ABC000_A",
            "group": "buggy",
            "pan_labels": [],
            "tests": [],
            "bug_lines": {"source": [2], "translation": [2]},
        }
    )
    (folder / "meta.json").write_text(meta.model_dump_json())
    (folder / "source.py").write_text("n = int(input())\nprint(n // 2)\n")
    (folder / "translation.java").write_text(TRANSLATION)
    return tmp_path / "samples"


def test_run_saves_each_sample_and_resumes(samples: Path, tmp_path: Path) -> None:
    """Each sample is saved once; a second run skips it."""
    scorer = FakeScorer()
    baselines = tmp_path / "baselines"

    assert run_baseline(scorer, "fake", "1", samples, baselines) == [SAMPLE]
    assert run_baseline(scorer, "fake", "1", samples, baselines) == []
    assert scorer.calls == 1

    config = BaselineConfig.model_validate_json(
        (baselines / "fake" / CONFIG_FILE).read_text()
    )
    assert (config.model, config.prompt_version) == ("fake/model", "1")
    saved = SampleBaseline.model_validate_json(
        (baselines / "fake" / f"{SAMPLE}.json").read_text()
    )
    assert saved.lines[1].lowest == 0.01


def test_reopening_with_another_prompt_is_refused(
    samples: Path, tmp_path: Path
) -> None:
    """A baseline keeps one model and prompt version."""
    baselines = tmp_path / "baselines"
    run_baseline(FakeScorer(), "fake", "1", samples, baselines)

    with pytest.raises(ValueError, match="pick a new name"):
        run_baseline(FakeScorer(), "fake", "2", samples, baselines)


def test_score_counts_highlighted_lines(samples: Path, tmp_path: Path) -> None:
    """Below the threshold a line is highlighted; the bug's rank ignores it."""
    baselines = tmp_path / "baselines"
    run_baseline(FakeScorer(), "fake", "1", samples, baselines)

    caught = score_baseline(baselines / "fake", samples, threshold=0.05)
    assert (caught.bugs, caught.bugs_caught) == (1, 1)
    assert (caught.highlighted, caught.false_alarms) == (1, 0)
    [sample] = caught.samples
    assert (sample.highlighted, sample.bug_rank) == ([2], 1)

    everything = score_baseline(baselines / "fake", samples, threshold=0.6)
    assert (everything.highlighted, everything.false_alarms) == (2, 1)
    assert everything.samples[0].bug_rank == 1

    assert "Test-exposed bugs caught: 1/1" in format_baseline_score(caught)


def test_budget_threshold_marks_that_many_lines(samples: Path, tmp_path: Path) -> None:
    """The threshold marks the budgeted lines; blank lines never count."""
    baselines = tmp_path / "baselines"
    run_baseline(FakeScorer(), "fake", "1", samples, baselines)
    folder = baselines / "fake"

    assert budget_threshold(folder, 1) == 0.5
    assert score_baseline(folder, samples, 0.5).highlighted == 1
    assert budget_threshold(folder, 2) == 1.0
