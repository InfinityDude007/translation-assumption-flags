// The flag list: each flag opens in place to show why it was raised and take a decision.

import { useEffect, useRef } from "react";
import type { Decision, DecisionKind, Review, ReviewFlag } from "../api";
import {
    CATEGORY_NAMES,
    DECISION_ACTIONS,
    DECISION_NAMES,
    VERDICT_NAMES,
} from "../labels";

interface Props {
    review: Review;
    decisions: Map<string, Decision>;
    selectedId: string | null;
    saving: boolean;
    saveError: string | null;
    notes: Record<string, string>;
    onNote: (id: string, note: string) => void;
    onSelect: (id: string) => void;
    onDecide: (flag: ReviewFlag, kind: DecisionKind) => void;
}

/** Every flag in source line order, with the selected one opened. */
export function FlagPanel(props: Props) {
    const {
        review,
        decisions,
        selectedId,
        saving,
        saveError,
        notes,
        onNote,
        onSelect,
        onDecide,
    } = props;
    const decided = review.flags.filter((flag) =>
        decisions.has(flag.id),
    ).length;
    return (
        <aside className="panel" aria-label="Flags">
            <p className="panel-summary">
                {review.flags.length === 0
                    ? "No flags for this program."
                    : `${decided} of ${review.flags.length} flags decided`}
            </p>
            <ol className="flags">
                {review.flags.map((flag) => (
                    <FlagItem
                        key={flag.id}
                        flag={flag}
                        decision={decisions.get(flag.id)}
                        open={flag.id === selectedId}
                        saving={saving}
                        saveError={flag.id === selectedId ? saveError : null}
                        note={
                            notes[flag.id] ?? decisions.get(flag.id)?.note ?? ""
                        }
                        onNote={(note) => onNote(flag.id, note)}
                        onSelect={() => onSelect(flag.id)}
                        onDecide={(kind) => onDecide(flag, kind)}
                    />
                ))}
            </ol>
            {review.dropped.length > 0 && (
                <details className="dropped">
                    <summary>
                        {review.dropped.length === 1
                            ? "1 site gave no flag"
                            : `${review.dropped.length} sites gave no flag`}
                    </summary>
                    <ul>
                        {review.dropped.map(({ site, reason }) => (
                            <li key={`${site.category}-${site.line}`}>
                                <code>{site.snippet}</code> on Python line{" "}
                                {site.line}: {reason}
                            </li>
                        ))}
                    </ul>
                </details>
            )}
        </aside>
    );
}

interface ItemProps {
    flag: ReviewFlag;
    decision: Decision | undefined;
    open: boolean;
    saving: boolean;
    saveError: string | null;
    note: string;
    onNote: (note: string) => void;
    onSelect: () => void;
    onDecide: (kind: DecisionKind) => void;
}

/** One flag: a summary row, and when open, the evidence and the decision buttons. */
function FlagItem({
    flag,
    decision,
    open,
    saving,
    saveError,
    note,
    onNote,
    onSelect,
    onDecide,
}: ItemProps) {
    const item = useRef<HTMLLIElement>(null);
    const openedOnLoad = useRef(open);
    const { site } = flag;
    const javaLines = flag.translation_lines.join(", ");

    // Keep the flag in view when it is opened from the code or the keyboard, but
    // not on load, where scrolling would carry a phone's page past the code.
    useEffect(() => {
        if (open && !openedOnLoad.current)
            item.current?.scrollIntoView?.({ block: "nearest" });
        if (!open) openedOnLoad.current = false;
    }, [open]);

    return (
        <li
            ref={item}
            className="flag"
            data-open={open || undefined}
            data-verdict={flag.verdict}
            style={{ ["--cat" as string]: `var(--cat-${site.category})` }}
        >
            <button
                type="button"
                className="flag-row"
                aria-expanded={open}
                aria-controls={`flag-${flag.id}`}
                onClick={onSelect}
            >
                <span className="flag-snippet">{site.snippet}</span>
                <span className="flag-meta">
                    {CATEGORY_NAMES[site.category]}, line {site.line}
                </span>
                <span className="flag-verdict">
                    {VERDICT_NAMES[flag.verdict]}
                </span>
                <span className="flag-decision" data-kind={decision?.decision}>
                    {decision
                        ? DECISION_NAMES[decision.decision]
                        : "Not decided"}
                </span>
            </button>
            {open && (
                <div className="flag-body" id={`flag-${flag.id}`}>
                    <p className="flag-lines">
                        Python line{" "}
                        {site.line === site.end_line
                            ? site.line
                            : `${site.line}–${site.end_line}`}
                        {javaLines
                            ? `, Java line${flag.translation_lines.length > 1 ? "s" : ""} ${javaLines}`
                            : ", no Java lines found"}
                    </p>
                    <section>
                        <h3>What the translation assumed</h3>
                        <p className="source-note">
                            Gemini's reading of the Java
                        </p>
                        <p>{flag.assumption}</p>
                    </section>
                    {flag.suggestion && (
                        <section>
                            <h3>Suggested Java</h3>
                            <p className="source-note">From Gemini</p>
                            <pre className="suggestion">{flag.suggestion}</pre>
                        </section>
                    )}
                    <section>
                        <h3>Why this construct can differ</h3>
                        <p className="source-note">
                            From the rule booklet (
                            {site.rule.replaceAll("_", " ")})
                        </p>
                        <p>{site.reason}</p>
                    </section>
                    <div
                        className="decide"
                        role="group"
                        aria-label="Your decision"
                    >
                        {DECISION_ACTIONS.map(({ kind, label, key }) => (
                            <button
                                key={kind}
                                type="button"
                                className="decide-button"
                                data-kind={kind}
                                aria-pressed={decision?.decision === kind}
                                aria-keyshortcuts={key}
                                disabled={saving}
                                onClick={() => onDecide(kind)}
                            >
                                {label}
                            </button>
                        ))}
                    </div>
                    <label className="note">
                        <span>Note (optional)</span>
                        <input
                            value={note}
                            onChange={(event) => onNote(event.target.value)}
                        />
                    </label>
                    {saveError && (
                        <p className="error" role="alert">
                            Not saved: {saveError}
                        </p>
                    )}
                </div>
            )}
        </li>
    );
}
