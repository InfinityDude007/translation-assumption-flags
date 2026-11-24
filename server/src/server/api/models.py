"""Request and response schemas for the review API."""

from datetime import datetime
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict

from ..baseline.models import LineProbability
from ..dataset.types import Dataset
from ..detection.models import Site
from ..explanation.models import DroppedSite, Explanation, Flag, Verdict

DecisionKind = Literal["confirmed", "intended", "dismissed"]
"""The reviewer's call on a flag: a real bug, a deliberate change, or noise."""


class SampleSummary(BaseModel):
    """A sample in the picker, without its labels or tagged lines.

    Attributes:
        id: Sample folder name.
        dataset: Dataset folder name.
        program: Program file name without extension.
    """

    id: str
    dataset: Dataset
    program: str


class SampleCode(BaseModel):
    """A sample's Python source and Java translation.

    Attributes:
        id: Sample folder name.
        source: The Python program.
        translation: Its Java translation.
    """

    id: str
    source: str
    translation: str


class RunSummary(BaseModel):
    """An archived explainer run that the frontend can show.

    Attributes:
        name: Run name.
        model: Gemini model ID.
        prompt_version: Explainer prompt version.
        created_at: When the run was started.
        samples: Number of samples archived in the run.
    """

    name: str
    model: str
    prompt_version: str
    created_at: datetime
    samples: int


class BaselineSummary(BaseModel):
    """A token-probability baseline that the frontend can show.

    Attributes:
        name: Baseline name.
        model: Hugging Face model ID that scored the tokens.
        prompt_version: Translation prompt version the Java was scored under.
        created_at: When the baseline was started.
        samples: Number of samples scored in the baseline.
    """

    name: str
    model: str
    prompt_version: str
    created_at: datetime
    samples: int


class ProbabilityReview(BaseModel):
    """One program's token probabilities, for the probability view.

    Attributes:
        baseline: The baseline they came from.
        model: Hugging Face model ID that scored the tokens.
        threshold: Tokens below this probability are highlighted.
        lines: Every Java line, in order.
    """

    baseline: str
    model: str
    threshold: float
    lines: list[LineProbability]


class ReviewFlag(BaseModel):
    """A flag as the reviewer sees it: Gemini's working is left out.

    Attributes:
        id: Category and source line, unique within a program because the
            detector keeps at most one site per (category, line).
        site: The mismatch site found by the detector.
        verdict: Whether the Java differs from the Python here.
        translation_lines: Java lines that implement the site.
        assumption: What the translation assumed at this site.
        suggestion: The Java change that would match the Python, mismatch only.
    """

    model_config = ConfigDict(frozen=True)

    id: str
    site: Site
    verdict: Verdict
    translation_lines: tuple[int, ...]
    assumption: str
    suggestion: str | None

    @classmethod
    def from_flag(cls, flag: Flag) -> Self:
        """Build the reviewer's view of a checked flag.

        Args:
            flag: The checked flag.

        Returns:
            The flag without Gemini's reasoning.
        """
        return cls(
            id=f"{flag.site.category}-{flag.site.line}",
            site=flag.site,
            verdict=flag.verdict,
            translation_lines=flag.translation_lines,
            assumption=flag.assumption,
            suggestion=flag.suggestion,
        )


class Review(BaseModel):
    """The flags for one program, archived or freshly analysed.

    Attributes:
        run: The archived run they came from, or None for a live analysis.
        model: Gemini model that answered, or None if no call was made.
        prompt_version: Version of the system prompt that produced the flags.
        flags: Flags in source line order.
        dropped: Sites that produced no flag, with the reason.
    """

    run: str | None
    model: str | None
    prompt_version: str
    flags: list[ReviewFlag]
    dropped: list[DroppedSite]

    @classmethod
    def from_explanation(cls, explanation: Explanation, run: str | None) -> Self:
        """Build the reviewer's view of an explanation.

        Args:
            explanation: The explainer's result.
            run: The archived run it came from, or None for a live analysis.

        Returns:
            The review, without Gemini's reasoning or raw answer.
        """
        return cls(
            run=run,
            model=explanation.model,
            prompt_version=explanation.prompt_version,
            flags=[ReviewFlag.from_flag(flag) for flag in explanation.flags],
            dropped=explanation.dropped,
        )


class AnalyseRequest(BaseModel):
    """A program and its translation to analyse live.

    Attributes:
        source: The Python program.
        translation: Its Java translation.
    """

    source: str
    translation: str


class DecisionRequest(BaseModel):
    """A reviewer's decision on one flag, with what the reviewer was shown.

    Attributes:
        sample_id: The sample reviewed, or None for pasted code.
        run: The archived run shown, or None for a live analysis.
        model: Gemini model that produced the flag.
        prompt_version: Prompt version that produced the flag.
        flag: The flag as the reviewer saw it.
        decision: The reviewer's call.
        note: Optional free-text comment.
    """

    sample_id: str | None
    run: str | None
    model: str | None
    prompt_version: str
    flag: ReviewFlag
    decision: DecisionKind
    note: str = ""


class Decision(DecisionRequest):
    """A logged decision.

    Attributes:
        decided_at: When the server received it.
    """

    decided_at: datetime
