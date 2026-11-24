"""Group token probabilities into Java lines."""

from bisect import bisect_right

from .models import LineProbability, TokenProbability


def line_probabilities(
    translation: str, spans: list[tuple[int, int, float]]
) -> list[LineProbability]:
    """Split scored tokens over the Java lines they cover.

    A token that spans a line break is split at the break, and each piece keeps
    the token's probability. Whitespace pieces are kept, so a line's token texts
    join to the line, but they never set its lowest probability.

    Args:
        translation: The Java program.
        spans: Each token's start and end offsets in `translation`, with its
            probability, in order.

    Returns:
        One entry per Java line, in order.
    """
    lines = translation.split("\n")
    starts = [0]
    for line in lines:
        starts.append(starts[-1] + len(line) + 1)

    tokens: list[list[TokenProbability]] = [[] for _ in lines]
    for start, end, probability in spans:
        while start < end:
            index = bisect_right(starts, start) - 1
            line_end = starts[index] + len(lines[index])
            stop = min(end, line_end)
            if stop > start:
                piece = TokenProbability(
                    text=translation[start:stop], probability=probability
                )
                tokens[index].append(piece)
            start = line_end + 1 if stop < end else end

    return [
        LineProbability(
            line=number,
            lowest=min(
                (token.probability for token in pieces if token.text.strip()),
                default=1.0,
            ),
            tokens=pieces,
        )
        for number, pieces in enumerate(tokens, start=1)
    ]
