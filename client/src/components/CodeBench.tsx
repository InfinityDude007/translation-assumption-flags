// Python and Java side by side, with each flag's lines joined across a bridge.

import { useEffect, useMemo, useRef } from "react";
import type { ReviewFlag, SampleCode, Verdict } from "../api";
import { highlightLines } from "../highlight";
import { KeyGuide } from "./KeyGuide";
import {
    VERDICT_MARKS,
    VERDICT_MEANINGS,
    VERDICT_NAMES,
    VERDICTS,
} from "../labels";

/** Height of one code line, in pixels; the CSS uses the same value. */
const LINE = 24;
/** Height of a column's heading row, in pixels; the CSS uses the same value. */
const HEAD = 40;
/** Width of the bridge between the columns, in pixels. */
const BRIDGE = 72;

/** Vertical centre of a line inside the bench. */
const middle = (line: number) => HEAD + (line - 1) * LINE + LINE / 2;

interface Props {
    code: SampleCode;
    flags: ReviewFlag[];
    selectedId: string | null;
    onSelect: (id: string) => void;
}

/**
 * The key, then the two code columns and the bridge between them.
 *
 * Both columns share a line height, so a flag's lines sit at known heights and
 * the bridge can draw them without measuring the page.
 */
export function CodeBench({ code, flags, selectedId, onSelect }: Props) {
    const scroller = useRef<HTMLDivElement>(null);
    const source = useMemo(
        () => highlightLines(code.source, "python"),
        [code.source],
    );
    const translation = useMemo(
        () => highlightLines(code.translation, "java"),
        [code.translation],
    );
    const rows = Math.max(source.length, translation.length);
    const height = HEAD + rows * LINE + LINE;

    const sourceFlags = useMemo(
        () =>
            flagsByLine(flags, (flag) =>
                range(flag.site.line, flag.site.end_line),
            ),
        [flags],
    );
    const translationFlags = useMemo(
        () => flagsByLine(flags, (flag) => flag.translation_lines),
        [flags],
    );
    const selected = flags.find((flag) => flag.id === selectedId) ?? null;

    useEffect(() => {
        const box = scroller.current;
        if (!box || !selected) return;
        const lines = [selected.site.line, ...selected.translation_lines];
        const top = middle(Math.min(...lines)) - LINE;
        const bottom = middle(Math.max(...lines)) + LINE;
        if (top >= box.scrollTop && bottom <= box.scrollTop + box.clientHeight)
            return;
        const reduce = window.matchMedia?.(
            "(prefers-reduced-motion: reduce)",
        ).matches;
        box.scrollTo?.({
            top: Math.max(top - box.clientHeight / 3, 0),
            behavior: reduce ? "auto" : "smooth",
        });
    }, [selected]);

    /** Select the next flag on a clicked line, cycling if the line has several. */
    const pick = (onLine: ReviewFlag[]) => {
        if (onLine.length === 0) return;
        const at = onLine.findIndex((flag) => flag.id === selectedId);
        onSelect(onLine[(at + 1) % onLine.length].id);
    };

    return (
        <div className="bench-wrap">
            <Key flags={flags} />
            <div className="bench" ref={scroller}>
                <div className="bench-grid" style={{ minHeight: height }}>
                    <Column
                        title="Python source"
                        lines={source}
                        flagsOnLine={sourceFlags}
                        selectedId={selectedId}
                        onPick={pick}
                    />
                    <svg
                        className="bridge"
                        width={BRIDGE}
                        height={height}
                        aria-hidden="true"
                    >
                        {flags.flatMap((flag) =>
                            flag.translation_lines.map((line) => (
                                <path
                                    key={`${flag.id}-${line}`}
                                    className="link"
                                    data-verdict={flag.verdict}
                                    data-selected={
                                        flag.id === selectedId || undefined
                                    }
                                    d={curve(
                                        middle(flag.site.line),
                                        middle(line),
                                    )}
                                />
                            )),
                        )}
                    </svg>
                    <Column
                        title="Java translation by GPT-4"
                        lines={translation}
                        flagsOnLine={translationFlags}
                        selectedId={selectedId}
                        onPick={pick}
                    />
                </div>
            </div>
        </div>
    );
}

/** What the line marks mean, with how many flags have each verdict. */
function Key({ flags }: { flags: ReviewFlag[] }) {
    return (
        <div className="key">
            <span className="key-title">
                Gemini's verdict on each flagged line:
            </span>
            {VERDICTS.map((verdict) => (
                <span
                    key={verdict}
                    className="key-item"
                    data-verdict={verdict}
                    title={VERDICT_MEANINGS[verdict]}
                >
                    <span className="mark" aria-hidden="true">
                        {VERDICT_MARKS[verdict]}
                    </span>
                    {VERDICT_NAMES[verdict]} (
                    {flags.filter((flag) => flag.verdict === verdict).length})
                </span>
            ))}
            <KeyGuide />
        </div>
    );
}

interface ColumnProps {
    title: string;
    lines: string[];
    flagsOnLine: Map<number, ReviewFlag[]>;
    selectedId: string | null;
    onPick: (onLine: ReviewFlag[]) => void;
}

/** One file, a line per row, with flagged lines marked by verdict. */
function Column({
    title,
    lines,
    flagsOnLine,
    selectedId,
    onPick,
}: ColumnProps) {
    return (
        <section className="column" aria-label={title}>
            <h2 className="column-title">{title}</h2>
            <div className="column-lines">
                <div className="column-inner">
                    {lines.map((html, index) => {
                        const number = index + 1;
                        const onLine = flagsOnLine.get(number) ?? [];
                        const chosen = onLine.find(
                            (flag) => flag.id === selectedId,
                        );
                        const verdict = chosen?.verdict ?? strongest(onLine);
                        return (
                            <div
                                key={number}
                                className="line"
                                data-verdict={verdict}
                                data-selected={chosen ? true : undefined}
                                onClick={() => onPick(onLine)}
                            >
                                <span className="line-number">{number}</span>
                                <span className="mark" aria-hidden="true">
                                    {verdict ? VERDICT_MARKS[verdict] : ""}
                                </span>
                                <code
                                    dangerouslySetInnerHTML={{
                                        __html: html || " ",
                                    }}
                                />
                            </div>
                        );
                    })}
                </div>
            </div>
        </section>
    );
}

/** Index flags by each line they cover. */
function flagsByLine(
    flags: ReviewFlag[],
    linesOf: (flag: ReviewFlag) => number[],
) {
    const map = new Map<number, ReviewFlag[]>();
    for (const flag of flags) {
        for (const line of linesOf(flag))
            map.set(line, [...(map.get(line) ?? []), flag]);
    }
    return map;
}

/** The most serious verdict among a line's flags, if it has any. */
function strongest(flags: ReviewFlag[]): Verdict | undefined {
    return VERDICTS.find((verdict) =>
        flags.some((flag) => flag.verdict === verdict),
    );
}

/** Whole numbers from first to last, inclusive. */
function range(first: number, last: number): number[] {
    return Array.from({ length: last - first + 1 }, (_, i) => first + i);
}

/** An S-curve across the bridge from a Python line to a Java line. */
function curve(from: number, to: number): string {
    const half = BRIDGE / 2;
    return `M0 ${from} C${half} ${from} ${half} ${to} ${BRIDGE} ${to}`;
}
