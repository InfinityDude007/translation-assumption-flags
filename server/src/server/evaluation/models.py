"""Records for archived explainer runs and their scores."""

from datetime import datetime

from pydantic import BaseModel

from ..dataset.types import Group
from ..explanation.models import Explanation


class RunConfig(BaseModel):
    """What a named run used; every sample in the run shares it.

    Attributes:
        name: Run name, also its folder name.
        model: Gemini model ID.
        prompt_version: Explainer prompt version.
        created_at: When the run was started.
    """

    name: str
    model: str
    prompt_version: str
    created_at: datetime


class SampleRun(BaseModel):
    """One sample's archived explainer result.

    Attributes:
        sample_id: Sample folder name.
        finished_at: When the call returned.
        seconds: How long the explainer took.
        explanation: Checked flags, dropped sites and Gemini's raw answer.
    """

    sample_id: str
    finished_at: datetime
    seconds: float
    explanation: Explanation


class SampleScore(BaseModel):
    """How one sample's mismatch flags compare with its tagged lines.

    Only flags with the verdict "mismatch" count as flagged. A flag hits when
    any of its Java lines is a tagged line.

    Attributes:
        sample_id: Sample folder name.
        group: "buggy" or "control".
        no_bug: True for buggy samples whose failure is not a translation bug.
        bug_lines: Tagged Java lines of the test-exposed bug.
        latent_lines: Tagged Java lines of latent bugs.
        mismatch_flags: Number of mismatch flags.
        bug_caught: Whether a mismatch flag hit a bug line; None if no bug.
        latent_caught: Whether a mismatch flag hit a latent line; None if none.
        bug_surfaced: Whether a mismatch or unclear flag hit a bug line; None
            if no bug. The review page tints both, so both reach the reviewer.
        latent_surfaced: The same for latent lines; None if none.
        false_alarms: Mismatch flags that hit neither bug nor latent lines.
        handled: Flags with the verdict "handled".
        unclear: Flags with the verdict "unclear".
        dropped: Sites dropped by the server-side checks.
    """

    sample_id: str
    group: Group
    no_bug: bool
    bug_lines: list[int]
    latent_lines: list[int]
    mismatch_flags: int
    bug_caught: bool | None
    latent_caught: bool | None
    bug_surfaced: bool | None
    latent_surfaced: bool | None
    false_alarms: int
    handled: int
    unclear: int
    dropped: int


class RunScore(BaseModel):
    """Totals for a run, over every sample archived so far.

    Attributes:
        config: The run's model and prompt version.
        samples: Per-sample scores.
        bugs: Samples with a test-exposed bug.
        bugs_caught: Of those, how many a mismatch flag hit.
        latent: Samples with a latent bug.
        latent_caught: Of those, how many a mismatch flag hit.
        bugs_surfaced: Bugs a mismatch or unclear flag hit.
        latent_surfaced: Latent bugs a mismatch or unclear flag hit.
        mismatch_flags: All mismatch flags.
        false_alarms: Mismatch flags that hit no tagged line.
        missing: Samples in the dataset that the run has not reached yet.
    """

    config: RunConfig
    samples: list[SampleScore]
    bugs: int
    bugs_caught: int
    latent: int
    latent_caught: int
    bugs_surfaced: int
    latent_surfaced: int
    mismatch_flags: int
    false_alarms: int
    missing: list[str]
