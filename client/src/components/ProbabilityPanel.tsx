// The side panel for the token-probability view: what it shows, and its least likely lines.

import type { ProbabilityReview } from "../api";
import { percent } from "../labels";
import { Evidence, Fact } from "./Evidence";

interface Props {
    review: ProbabilityReview;
    selectedLine: number | null;
    onSelectLine: (line: number) => void;
}

/**
 * How the probability view was made, then its marked lines, least likely first.
 *
 * It says plainly that the probabilities come from a stand-in model and mean
 * "surprising", not "wrong", because a reviewer cannot tell that from the
 * shading alone.
 */
export function ProbabilityPanel({
    review,
    selectedLine,
    onSelectLine,
}: Props) {
    const below = percent(review.threshold);
    const marked = review.lines
        .filter((line) => line.lowest < review.threshold)
        .sort((a, b) => a.lowest - b.lowest);

    return (
        <aside className="panel" aria-label="Token probabilities">
            <div className="panel-head">
                <h2>Unlikely lines</h2>
                <span>
                    {marked.length} of {review.lines.length} lines below {below}
                </span>
            </div>
            <Evidence source="model" title="Local model" detail={review.model}>
                <Fact name="Marks">
                    lines whose least likely token is below {below}
                </Fact>
                <p>
                    The model read the Python, then GPT-4's Java one token at a
                    time. Each token is shaded by how likely the model found it
                    at that point: the darker, the less likely.
                </p>
                <p>
                    This is the usual way to highlight generated code, and the
                    view the flags are compared against. GPT-4's own
                    probabilities were not published with these translations, so
                    a smaller local model stands in for it.
                </p>
                <p>
                    Unlikely means surprising, not wrong. The model does not
                    check what the Java does, so a bug it also expects is not
                    marked, and an unusual but correct line is.
                </p>
            </Evidence>
            {marked.length === 0 ? (
                <p className="status">
                    No line in this program is below {below}.
                </p>
            ) : (
                <ol className="unlikely">
                    {marked.map((line) => (
                        <li key={line.line}>
                            <button
                                type="button"
                                className="unlikely-row"
                                aria-pressed={line.line === selectedLine}
                                onClick={() => onSelectLine(line.line)}
                            >
                                <span className="unlikely-line">
                                    Java line {line.line}
                                </span>
                                <span className="unlikely-share">
                                    {percent(line.lowest)}
                                </span>
                                <code>
                                    {line.tokens
                                        .map((token) => token.text)
                                        .join("")
                                        .trim()}
                                </code>
                            </button>
                        </li>
                    ))}
                </ol>
            )}
        </aside>
    );
}
