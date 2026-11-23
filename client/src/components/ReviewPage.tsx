// One review page: archived flags from a run, or live flags from Gemini.

import {
    useCallback,
    useEffect,
    useMemo,
    useState,
    type Dispatch,
    type SetStateAction,
} from "react";
import {
    analyse,
    ApiError,
    getArchivedReview,
    getSample,
    listDecisions,
    saveDecision,
    type Decision,
    type DecisionKind,
    type Review,
    type ReviewFlag,
    type RunSummary,
    type SampleCode,
    type SampleSummary,
} from "../api";
import { latestByFlag } from "../decisions";
import { describeError } from "../errors";
import { DECISION_ACTIONS } from "../labels";
import { LIVE } from "../runs";
import { CodeBench } from "./CodeBench";
import { FlagPanel } from "./FlagPanel";
import { useSideWidth } from "./useSideWidth";

/** The state of the flags for one program and source. */
export type Status =
    | { kind: "loading" }
    | { kind: "ready"; review: Review }
    | { kind: "not-analysed" }
    | { kind: "analysing"; since: number }
    | { kind: "failed"; message: string };

/** A program's code and decision log, or why they could not be loaded. */
type Loaded =
    | { id: string; code: SampleCode; log: Decision[] }
    | { id: string; error: string };

interface Props {
    mode: "archived" | "live";
    samples: SampleSummary[];
    runs: RunSummary[];
    sampleId: string | null;
    onSample: (id: string) => void;
    runName: string;
    onRun: (name: string) => void;
    live: Record<string, Status>;
    setLive: Dispatch<SetStateAction<Record<string, Status>>>;
}

/**
 * A toolbar, the code bench and the flag panel for one source of flags.
 *
 * Results are stored with the program and source they belong to, and the
 * shown state is derived from the current choice, so switching never shows
 * another program's flags.
 */
export function ReviewPage(props: Props) {
    const { mode, samples, runs, sampleId, onSample, runName, onRun } = props;
    const { live, setLive } = props;
    const source = mode === "live" ? LIVE : runName;
    const [loaded, setLoaded] = useState<Loaded | null>(null);
    const [archived, setArchived] = useState<{
        key: string;
        status: Status;
    } | null>(null);
    const [selection, setSelection] = useState<{
        key: string;
        id: string;
    } | null>(null);
    const [notes, setNotes] = useState<Record<string, string>>({});
    const [saving, setSaving] = useState(false);
    const [saveError, setSaveError] = useState<{
        flagId: string;
        message: string;
    } | null>(null);
    const side = useSideWidth();

    const key = `${sampleId}|${source}`;
    const current = loaded?.id === sampleId ? loaded : null;
    const code = current && "code" in current ? current.code : null;

    let status: Status;
    if (current && "error" in current)
        status = { kind: "failed", message: current.error };
    else if (source === LIVE)
        status = (sampleId && live[sampleId]) || { kind: "not-analysed" };
    else status = archived?.key === key ? archived.status : { kind: "loading" };

    const review = status.kind === "ready" ? status.review : null;
    const run = source === LIVE ? null : source;
    const log = useMemo(
        () => (current && "log" in current ? current.log : []),
        [current],
    );
    const decisions = useMemo(() => latestByFlag(log, run), [log, run]);
    const selectedId =
        selection?.key === key
            ? selection.id
            : ((
                  review?.flags.find((flag) => !decisions.has(flag.id)) ??
                  review?.flags[0]
              )?.id ?? null);

    const select = useCallback(
        (id: string) => setSelection({ key, id }),
        [key],
    );

    useEffect(() => {
        if (!sampleId) return;
        Promise.all([getSample(sampleId), listDecisions(sampleId)])
            .then(([code, log]) => setLoaded({ id: sampleId, code, log }))
            .catch((error) =>
                setLoaded({ id: sampleId, error: describeError(error) }),
            );
    }, [sampleId]);

    useEffect(() => {
        if (!sampleId || source === LIVE) return;
        const key = `${sampleId}|${source}`;
        getArchivedReview(source, sampleId)
            .then((review) =>
                setArchived({ key, status: { kind: "ready", review } }),
            )
            .catch((error) => {
                const missing =
                    error instanceof ApiError && error.status === 404;
                const message = missing
                    ? `Run ${source} has no saved review of this program. Pick another run.`
                    : describeError(error);
                setArchived({ key, status: { kind: "failed", message } });
            });
    }, [sampleId, source]);

    const runAnalysis = async () => {
        if (!code || !sampleId) return;
        const id = sampleId;
        setLive((live) => ({
            ...live,
            [id]: { kind: "analysing", since: Date.now() },
        }));
        try {
            const review = await analyse(code.source, code.translation);
            setLive((live) => ({ ...live, [id]: { kind: "ready", review } }));
        } catch (error) {
            setLive((live) => ({
                ...live,
                [id]: { kind: "failed", message: describeError(error) },
            }));
        }
    };

    const decide = useCallback(
        async (flag: ReviewFlag, kind: DecisionKind) => {
            if (!review || !sampleId) return;
            setSaving(true);
            setSaveError(null);
            try {
                const saved = await saveDecision({
                    sample_id: sampleId,
                    run: review.run,
                    model: review.model,
                    prompt_version: review.prompt_version,
                    flag,
                    decision: kind,
                    note: notes[flag.id] ?? decisions.get(flag.id)?.note ?? "",
                });
                setLoaded((loaded) =>
                    loaded && "log" in loaded && loaded.id === sampleId
                        ? { ...loaded, log: [...loaded.log, saved] }
                        : loaded,
                );
                const after = review.flags.slice(
                    review.flags.indexOf(flag) + 1,
                );
                select(
                    (after.find((other) => !decisions.has(other.id)) ?? flag)
                        .id,
                );
            } catch (error) {
                setSaveError({
                    flagId: flag.id,
                    message: describeError(error),
                });
            } finally {
                setSaving(false);
            }
        },
        [review, sampleId, decisions, notes, select],
    );

    // Keys: j and k move between flags; 1, 2 and 3 decide on the open one.
    useEffect(() => {
        const onKey = (event: KeyboardEvent) => {
            const target = event.target as HTMLElement;
            if (!review || event.metaKey || event.ctrlKey || event.altKey)
                return;
            if (["INPUT", "TEXTAREA", "SELECT"].includes(target.tagName))
                return;
            const at = review.flags.findIndex((flag) => flag.id === selectedId);
            if (event.key === "j" || event.key === "k") {
                const step = event.key === "j" ? 1 : -1;
                const next =
                    review.flags[
                        Math.min(
                            Math.max(at + step, 0),
                            review.flags.length - 1,
                        )
                    ];
                if (next) select(next.id);
                return;
            }
            const action = DECISION_ACTIONS.find(
                (action) => action.key === event.key,
            );
            if (action && at >= 0 && !saving)
                decide(review.flags[at], action.kind);
        };
        window.addEventListener("keydown", onKey);
        return () => window.removeEventListener("keydown", onKey);
    }, [review, selectedId, saving, decide, select]);

    const analysing = status.kind === "analysing";

    return (
        <>
            <div className="toolbar">
                <label>
                    <span>Program</span>
                    <select
                        value={sampleId ?? ""}
                        onChange={(event) => onSample(event.target.value)}
                    >
                        {samples.map((sample) => (
                            <option key={sample.id} value={sample.id}>
                                {sample.program}
                            </option>
                        ))}
                    </select>
                </label>
                {mode === "archived" ? (
                    <label>
                        <span>Run</span>
                        <select
                            value={source}
                            onChange={(event) => onRun(event.target.value)}
                        >
                            {runs.map((run) => (
                                <option key={run.name} value={run.name}>
                                    {run.name} ({run.model}, prompt{" "}
                                    {run.prompt_version}
                                    {run.samples < samples.length
                                        ? `, ${run.samples} of ${samples.length} programs`
                                        : ""}
                                    )
                                </option>
                            ))}
                        </select>
                    </label>
                ) : (
                    <div className="toolbar-action">
                        <button
                            type="button"
                            className="primary"
                            onClick={runAnalysis}
                            disabled={!code || analysing}
                        >
                            {review ? "Analyse again" : "Analyse with Gemini"}
                        </button>
                    </div>
                )}
            </div>
            <main
                className="workspace"
                style={{ ["--side" as string]: `${side.width}px` }}
            >
                {code ? (
                    <CodeBench
                        code={code}
                        flags={review?.flags ?? []}
                        selectedId={selectedId}
                        onSelect={select}
                    />
                ) : (
                    <div className="bench bench-empty">
                        {current
                            ? "The program could not be loaded."
                            : "Loading the program…"}
                    </div>
                )}
                <div
                    className="resize"
                    role="separator"
                    aria-orientation="vertical"
                    aria-label="Resize the flag panel"
                    aria-valuenow={side.width}
                    aria-valuemin={side.min}
                    aria-valuemax={side.max}
                    tabIndex={0}
                    {...side.handlers}
                />
                <div className="side">
                    <StatusView status={status} />
                    {review && (
                        <FlagPanel
                            review={review}
                            decisions={decisions}
                            selectedId={selectedId}
                            saving={saving}
                            saveError={
                                saveError?.flagId === selectedId
                                    ? saveError.message
                                    : null
                            }
                            notes={notes}
                            onNote={(id, note) =>
                                setNotes((notes) => ({ ...notes, [id]: note }))
                            }
                            onSelect={select}
                            onDecide={decide}
                        />
                    )}
                </div>
            </main>
        </>
    );
}

/** Loading, failure and live-analysis progress; nothing once flags are shown. */
function StatusView({ status }: { status: Status }) {
    const [now, setNow] = useState(() => Date.now());
    const analysing = status.kind === "analysing";
    useEffect(() => {
        if (!analysing) return;
        const timer = window.setInterval(() => setNow(Date.now()), 1000);
        return () => window.clearInterval(timer);
    }, [analysing]);

    switch (status.kind) {
        case "ready":
            return null;
        case "loading":
            return <p className="status">Loading flags…</p>;
        case "failed":
            return (
                <p className="status status-error" role="alert">
                    {status.message}
                </p>
            );
        case "not-analysed":
            return (
                <p className="status">
                    No flags yet. Analyse the program to ask Gemini about each
                    site the detector found.
                </p>
            );
        case "analysing":
            return (
                <p className="status" role="status">
                    Waiting for Gemini,{" "}
                    {Math.max(0, Math.round((now - status.since) / 1000))}{" "}
                    seconds so far…
                </p>
            );
    }
}
