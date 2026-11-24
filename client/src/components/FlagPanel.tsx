// The flag list: each flag opens in place, its evidence grouped by where it came from.

import { useEffect, useRef } from "react";
import type { Decision, DecisionKind, Review, ReviewFlag } from "../api";
import {
    CATEGORY_NAMES,
    DECISION_ACTIONS,
    DECISION_NAMES,
    VERDICT_MARKS,
    VERDICT_NAMES,
} from "../labels";
import { Evidence, Fact } from "./Evidence";

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

/** Every flag in source line order, the selected one opened, then dropped sites. */
export function FlagPanel(props: Props) {
    const { review, decisions, selectedId, saving, saveError } = props;
    const { notes, onNote, onSelect, onDecide } = props;
    const decided = review.flags.filter((flag) =>
        decisions.has(flag.id),
    ).length;
    const explainer = [
        review.model ?? "no model",
        `prompt ${review.prompt_version}`,
        review.run ? `run ${review.run}` : "live",
    ].join(", ");

    return (
        <aside className="panel" aria-label="Flags">
            <div className="panel-head">
                <h2>Flags</h2>
                <span>
                    {review.flags.length === 0
                        ? "None for this program"
                        : `${decided} of ${review.flags.length} decided`}
                </span>
            </div>
            <ol className="flags">
                {review.flags.map((flag) => (
                    <FlagItem
                        key={flag.id}
                        flag={flag}
                        explainer={explainer}
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
                <section className="dropped">
                    <h3>Dropped by the checks ({review.dropped.length})</h3>
                    <p>
                        The detector found these sites, but the server's checks
                        rejected Gemini's answer, so they have no flag and are
                        not marked in the code.
                    </p>
                    <ul>
                        {review.dropped.map(({ site, reason }) => (
                            <li key={`${site.category}-${site.line}`}>
                                <code>{site.snippet}</code>, Python line{" "}
                                {site.line}: {reason}
                            </li>
                        ))}
                    </ul>
                </section>
            )}
        </aside>
    );
}

interface ItemProps {
    flag: ReviewFlag;
    explainer: string;
    decision: Decision | undefined;
    open: boolean;
    saving: boolean;
    saveError: string | null;
    note: string;
    onNote: (note: string) => void;
    onSelect: () => void;
    onDecide: (kind: DecisionKind) => void;
}

/** One flag: a summary row, and when open, its evidence and the decision. */
function FlagItem(props: ItemProps) {
    const { flag, explainer, decision, open, saving, saveError } = props;
    const { note, onNote, onSelect, onDecide } = props;
    const item = useRef<HTMLLIElement>(null);
    const openedOnLoad = useRef(open);
    const { site } = flag;
    const pythonLines =
        site.line === site.end_line
            ? `${site.line}`
            : `${site.line}–${site.end_line}`;

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
        >
            <button
                type="button"
                className="flag-row"
                aria-expanded={open}
                aria-controls={`flag-${flag.id}`}
                onClick={onSelect}
            >
                <span className="mark" aria-hidden="true">
                    {VERDICT_MARKS[flag.verdict]}
                </span>
                <span className="flag-snippet">{site.snippet}</span>
                <span className="flag-verdict">
                    {VERDICT_NAMES[flag.verdict]}
                </span>
                <span className="flag-meta">
                    {CATEGORY_NAMES[site.category]}, line {site.line}
                </span>
                <span className="flag-decision" data-kind={decision?.decision}>
                    {decision
                        ? DECISION_NAMES[decision.decision]
                        : "Not decided"}
                </span>
            </button>
            {open && (
                <div className="flag-body" id={`flag-${flag.id}`}>
                    <Evidence
                        source="detector"
                        title="Detector"
                        detail="rule booklet"
                    >
                        <Fact name="Python">
                            line {pythonLines}, <code>{site.snippet}</code>
                        </Fact>
                        <Fact name="Rule">
                            {site.rule.replaceAll("_", " ")} (
                            {CATEGORY_NAMES[site.category].toLowerCase()})
                        </Fact>
                        <p>{site.reason}</p>
                    </Evidence>
                    <Evidence
                        source="explainer"
                        title="Explainer"
                        detail={explainer}
                    >
                        <Fact name="Verdict">
                            <span
                                className="verdict"
                                data-verdict={flag.verdict}
                            >
                                <span className="mark" aria-hidden="true">
                                    {VERDICT_MARKS[flag.verdict]}
                                </span>
                                {VERDICT_NAMES[flag.verdict]}
                            </span>
                        </Fact>
                        <Fact name="Java">
                            {flag.translation_lines.length > 0
                                ? `line${flag.translation_lines.length > 1 ? "s" : ""} ${flag.translation_lines.join(", ")}`
                                : "no line found"}
                        </Fact>
                        <h4>What the translation assumed</h4>
                        <p>{flag.assumption}</p>
                        {flag.suggestion && (
                            <>
                                <h4>Suggested Java</h4>
                                <pre className="suggestion">
                                    {flag.suggestion}
                                </pre>
                            </>
                        )}
                    </Evidence>
                    <Evidence
                        source="you"
                        title="Your decision"
                        detail={
                            decision
                                ? `saved: ${DECISION_NAMES[decision.decision].toLowerCase()}`
                                : "not decided"
                        }
                    >
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
                                    title={`Key ${key}`}
                                    disabled={saving}
                                    onClick={() => onDecide(kind)}
                                >
                                    {label}
                                </button>
                            ))}
                        </div>
                        <label className="note">
                            <span>Note</span>
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
                        <p className="keys">
                            Keys: <kbd>1</kbd> <kbd>2</kbd> <kbd>3</kbd> decide,{" "}
                            <kbd>j</kbd> <kbd>k</kbd> move between flags.
                        </p>
                    </Evidence>
                </div>
            )}
        </li>
    );
}
