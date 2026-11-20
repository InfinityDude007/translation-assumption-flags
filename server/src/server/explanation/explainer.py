"""Explain detector sites with Gemini, then check its answer before keeping any flag."""

from ..detection import detect
from ..detection.models import Site
from ..gemini import GeminiClient, get_client
from .models import DroppedSite, Explanation, Flag, GeminiAnswer, SiteAnswer
from .prompts import PROMPT_VERSION, SYSTEM_PROMPT, build_prompt


def explain(
    source: str, translation: str, client: GeminiClient | None = None
) -> Explanation:
    """Find the mismatch sites in a program and explain each against its translation.

    Makes no call when the detector finds no sites.

    Args:
        source: The Python program.
        translation: Its Java translation.
        client: Gemini client to use, the shared client if omitted.

    Returns:
        Checked flags, and the sites that produced none.

    Raises:
        ValueError: If the source is not valid Python, or no credential is set.
        GeminiError: If the Gemini call fails.
    """
    sites = detect(source)
    if not sites:
        return Explanation(flags=[], dropped=[], prompt_version=PROMPT_VERSION)

    client = client or get_client()
    answer = client.complete(
        SYSTEM_PROMPT, build_prompt(source, translation, sites), GeminiAnswer
    )

    return check(answer, client.model, sites, len(translation.splitlines()))


def check(
    answer: GeminiAnswer, model: str, sites: list[Site], java_lines: int
) -> Explanation:
    """Keep only what the program can verify in Gemini's answer.

    Answers for unknown or repeated site ids are ignored, line numbers outside
    the Java file are removed, and a suggestion is kept only for a mismatch.
    A site with no answer, or no valid Java line left, is dropped with a reason.

    Args:
        answer: Gemini's structured reply.
        model: Gemini model that gave the answer, recorded with the flags.
        sites: The sites the prompt listed, indexed by site id.
        java_lines: Number of lines in the Java translation.

    Returns:
        Flags in source line order, the dropped sites, the model, and the unchecked answer.
    """
    by_id: dict[int, SiteAnswer] = {}
    for candidate in answer.answers:
        if 0 <= candidate.site_id < len(sites):
            by_id.setdefault(candidate.site_id, candidate)

    flags: list[Flag] = []
    dropped: list[DroppedSite] = []
    for site_id, site in enumerate(sites):
        site_answer = by_id.get(site_id)
        if site_answer is None:
            dropped.append(DroppedSite(site=site, reason="no answer for this site"))
            continue

        lines = sorted(
            {n for n in site_answer.translation_lines if 1 <= n <= java_lines}
        )
        if not lines:
            dropped.append(DroppedSite(site=site, reason="no valid Java line"))
            continue

        flags.append(
            Flag(
                site=site,
                verdict=site_answer.verdict,
                translation_lines=tuple(lines),
                assumption=site_answer.assumption,
                suggestion=(
                    site_answer.suggestion
                    if site_answer.verdict == "mismatch"
                    else None
                ),
                reasoning=site_answer.reasoning,
            )
        )

    return Explanation(
        flags=flags,
        dropped=dropped,
        model=model,
        prompt_version=PROMPT_VERSION,
        answer=answer,
    )
