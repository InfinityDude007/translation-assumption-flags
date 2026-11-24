"""Records for token-probability baselines and their scores."""

from datetime import datetime

from pydantic import BaseModel

from ..dataset.types import Group


class TokenProbability(BaseModel):
    """One token's share of a Java line, with the model's probability for it.

    Attributes:
        text: The token's characters on this line; a token that spans a line
            break is split, and each piece keeps the token's probability.
        probability: The model's probability for the token, given everything
            before it.
    """

    text: str
    probability: float


class LineProbability(BaseModel):
    """One Java line's tokens and its least likely token.

    Attributes:
        line: 1-based Java line number.
        lowest: Probability of the line's least likely token; 1.0 for a blank
            line, which has nothing to doubt.
        tokens: The line's tokens in order; their texts join to the line.
    """

    line: int
    lowest: float
    tokens: list[TokenProbability]


class BaselineConfig(BaseModel):
    """What a named baseline used; every sample in it shares it.

    Attributes:
        name: Baseline name, also its folder name.
        model: Hugging Face model ID that scored the tokens.
        prompt_version: Version of the translation prompt the Java was scored
            under.
        created_at: When the baseline was started.
    """

    name: str
    model: str
    prompt_version: str
    created_at: datetime


class SampleBaseline(BaseModel):
    """One sample's token probabilities.

    Attributes:
        sample_id: Sample folder name.
        finished_at: When scoring finished.
        seconds: How long scoring took.
        lines: Every Java line, in order.
    """

    sample_id: str
    finished_at: datetime
    seconds: float
    lines: list[LineProbability]


class BaselineSampleScore(BaseModel):
    """How one sample's highlighted lines compare with its tagged lines.

    A line is highlighted when its least likely token is below the threshold.

    Attributes:
        sample_id: Sample folder name.
        group: "buggy" or "control".
        no_bug: True for buggy samples whose failure is not a translation bug.
        bug_lines: Tagged Java lines of the test-exposed bug.
        latent_lines: Tagged Java lines of latent bugs.
        highlighted: Highlighted Java lines.
        bug_caught: Whether a highlighted line is a bug line; None if no bug.
        latent_caught: Whether a highlighted line is a latent line; None if none.
        false_alarms: Highlighted lines that are neither bug nor latent lines.
        bug_rank: Where the first bug line comes when every line is sorted from
            least to most likely (1 is the least likely); None if no bug.
            Unlike the other counts, it does not depend on the threshold.
    """

    sample_id: str
    group: Group
    no_bug: bool
    bug_lines: list[int]
    latent_lines: list[int]
    highlighted: list[int]
    bug_caught: bool | None
    latent_caught: bool | None
    false_alarms: int
    bug_rank: int | None


class BaselineScore(BaseModel):
    """Totals for a baseline at one threshold, over every sample scored so far.

    Attributes:
        config: The baseline's model and prompt version.
        threshold: Lines whose least likely token is below this are highlighted.
        samples: Per-sample scores.
        bugs: Samples with a test-exposed bug.
        bugs_caught: Of those, how many had a bug line highlighted.
        latent: Samples with a latent bug.
        latent_caught: Of those, how many had a latent line highlighted.
        highlighted: All highlighted lines.
        false_alarms: Highlighted lines on no tagged line.
        missing: Samples in the dataset not scored yet.
    """

    config: BaselineConfig
    threshold: float
    samples: list[BaselineSampleScore]
    bugs: int
    bugs_caught: int
    latent: int
    latent_caught: int
    highlighted: int
    false_alarms: int
    missing: list[str]
