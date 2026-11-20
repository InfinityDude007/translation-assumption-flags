"""Schemas for Claude's answer and for the checked flags built from it."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from ..detection.models import Site

Verdict = Literal["mismatch", "handled", "unclear"]
"""Whether the Java differs from the Python at a site, handles it, or cannot be judged."""


class SiteAnswer(BaseModel):
    """Claude's answer for one site: a proposal, checked before it becomes a flag.

    Attributes:
        site_id: The id the prompt gave the site.
        verdict: Whether the Java differs from the Python here.
        translation_lines: Java lines that implement the site; empty if not found.
        assumption: What the translation assumed at this site.
        suggestion: The Java change that would match the Python, for a mismatch.
        reasoning: Claude's working, kept for logs and not shown to reviewers.
    """

    site_id: int = Field(description="The id of the site, exactly as given.")
    verdict: Verdict = Field(
        description="mismatch: the Java behaves differently for some input; "
        "handled: the Java deals with the difference correctly; "
        "unclear: cannot tell, or the Java lines cannot be found."
    )
    translation_lines: list[int] = Field(
        description="Numbers of the Java lines that implement this site, taken "
        "from the numbered Java code; empty if they cannot be found."
    )
    assumption: str = Field(
        description="One or two sentences naming the Java code and what it "
        "assumes here that the Python did not need to."
    )
    suggestion: str | None = Field(
        description="For a mismatch, the smallest Java change that matches the "
        "Python; null otherwise."
    )
    reasoning: str = Field(
        description="Working notes for logs; not shown to the reviewer."
    )


class ClaudeAnswer(BaseModel):
    """Claude's full reply: one answer per site.

    Attributes:
        answers: The answers, in any order.
    """

    answers: list[SiteAnswer]


class Flag(BaseModel):
    """A checked flag: the detector's site with Claude's explanation attached.

    The site, its category and its reason come from the rule booklet; the
    other fields are Claude's claims, kept only after the server-side checks.

    Attributes:
        site: The mismatch site found by the detector.
        verdict: Whether the Java differs from the Python here.
        translation_lines: Java lines that implement the site, all in range.
        assumption: What the translation assumed at this site.
        suggestion: The Java change that would match the Python, mismatch only.
        reasoning: Claude's working, kept for logs and not shown to reviewers.
    """

    model_config = ConfigDict(frozen=True)

    site: Site
    verdict: Verdict
    translation_lines: tuple[int, ...]
    assumption: str
    suggestion: str | None
    reasoning: str


class DroppedSite(BaseModel):
    """A site that produced no flag, and why.

    Attributes:
        site: The mismatch site found by the detector.
        reason: Why no flag was kept.
    """

    model_config = ConfigDict(frozen=True)

    site: Site
    reason: str


class Explanation(BaseModel):
    """The explainer's result for one program.

    Attributes:
        flags: Checked flags, in source line order.
        dropped: Sites that produced no flag, with the reason.
        prompt_version: Version of the system prompt that produced the flags.
    """

    flags: list[Flag]
    dropped: list[DroppedSite]
    prompt_version: str
