// The review screen: pick a program and a source of flags, then decide on each flag.

import { useCallback, useEffect, useMemo, useState } from "react";
import {
    analyse,
    ApiError,
    getArchivedReview,
    getSample,
    listDecisions,
    listRuns,
    listSamples,
    saveDecision,
    type Decision,
    type DecisionKind,
    type Review,
    type ReviewFlag,
    type RunSummary,
    type SampleCode,
    type SampleSummary,
} from "./api";
import { CodeBench } from "./components/CodeBench";
import { FlagPanel } from "./components/FlagPanel";
import { latestByFlag } from "./decisions";
import { describeError } from "./errors";
import { DECISION_ACTIONS } from "./labels";
import { defaultRun, LIVE } from "./runs";

/** The state of the flags for one program and source. */
type Status =
    | { kind: "loading" }
    | { kind: "ready"; review: Review }
    | { kind: "not-analysed" }
    | { kind: "analysing"; since: number }
    | { kind: "failed"; message: string };

/** A program's code and decision log, or why they could not be loaded. */
type Loaded =
    | { id: string; code: SampleCode; log: Decision[] }
    | { id: string; error: string };

/**
 * The review screen.
 *
 * Results are stored with the program and source they belong to, and the
 * shown state is derived from the current choice, so switching never shows
 * another program's flags.
 */
export default function App() {
    const [samples, setSamples] = useState<SampleSummary[]>([]);
    const [runs, setRuns] = useState<RunSummary[]>([]);
    const [startError, setStartError] = useState<string | null>(null);
    const [sampleId, setSampleId] = useState<string | null>(null);
    const [source, setSource] = useState<string>(LIVE);
    const [loaded, setLoaded] = useState<Loaded | null>(null);
    const [archived, setArchived] = useState<{
        key: string;
        status: Status;
    } | null>(null);
    const [live, setLive] = useState<Record<string, Status>>({});
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
        Promise.all([listSamples(), listRuns()])
            .then(([samples, runs]) => {
                setSamples(samples);
                setRuns(runs);
                setSampleId(samples[0]?.id ?? null);
                setSource(defaultRun(runs, samples.length));
            })
            .catch((error) => setStartError(describeError(error)));
    }, []);

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

    if (startError) {
        return (
            <main className="start-error">
                <h1>Assumption flags</h1>
                <p role="alert">{startError}</p>
            </main>
        );
    }

    return (
        <div className="app">
            <header className="bar">
                <h1>Assumption flags</h1>
                <label>
                    <span>Program</span>
                    <select
                        value={sampleId ?? ""}
                        onChange={(event) => setSampleId(event.target.value)}
                    >
                        {samples.map((sample) => (
                            <option key={sample.id} value={sample.id}>
                                {sample.program}
                            </option>
                        ))}
                    </select>
                </label>
                <label>
                    <span>Flags from</span>
                    <select
                        value={source}
                        onChange={(event) => setSource(event.target.value)}
                    >
                        {runs.map((run) => (
                            <option key={run.name} value={run.name}>
                                {run.name} (prompt {run.prompt_version}
                                {run.samples < samples.length
                                    ? `, ${run.samples} of ${samples.length} programs`
                                    : ""}
                                )
                            </option>
                        ))}
                        <option value={LIVE}>Live analysis with Gemini</option>
                    </select>
                </label>
            </header>
            <main className="workspace">
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
                <div className="side">
                    <Provenance review={review} source={source} runs={runs} />
                    <StatusView
                        status={status}
                        onAnalyse={runAnalysis}
                        canAnalyse={code !== null}
                        canRetry={source === LIVE && code !== null}
                    />
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
                    {review && review.flags.length > 0 && (
                        <p className="keys">
                            <kbd>j</kbd> and <kbd>k</kbd> move between flags.{" "}
                            <kbd>1</kbd> confirms a bug, <kbd>2</kbd> marks it
                            intended and <kbd>3</kbd> dismisses it.
                        </p>
                    )}
                </div>
            </main>
        </div>
    );
}

/** Say which model and prompt produced the flags, and whether they were saved earlier. */
function Provenance({
    review,
    source,
    runs,
}: {
    review: Review | null;
    source: string;
    runs: RunSummary[];
}) {
    if (source === LIVE) {
        return (
            <p className="provenance">
                {review
                    ? `Analysed live by ${review.model ?? "no model (no sites found)"} with prompt version ${review.prompt_version}.`
                    : "Live analysis sends this program to Gemini now."}
            </p>
        );
    }
    const run = runs.find((run) => run.name === source);
    if (!run) return null;
    const saved = new Date(run.created_at).toLocaleDateString("en-GB", {
        day: "numeric",
        month: "long",
    });
    return (
        <p className="provenance">
            Saved by {run.model} with prompt version {run.prompt_version}, in
            run {run.name} started {saved}. No Gemini call is made.
        </p>
    );
}

interface StatusProps {
    status: Status;
    onAnalyse: () => void;
    canAnalyse: boolean;
    canRetry: boolean;
}

/** Loading, failure and the live-analysis prompt; nothing once a review is shown. */
function StatusView({ status, onAnalyse, canAnalyse, canRetry }: StatusProps) {
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
                <div className="status">
                    <p className="status-error" role="alert">
                        {status.message}
                    </p>
                    {canRetry && (
                        <button
                            type="button"
                            className="primary"
                            onClick={onAnalyse}
                        >
                            Try again
                        </button>
                    )}
                </div>
            );
        case "not-analysed":
            return (
                <div className="status">
                    <p>
                        Gemini reads the program and its translation and
                        explains each site the rules found. It usually takes
                        under a minute, and uses one of the key's daily
                        requests.
                    </p>
                    <button
                        type="button"
                        className="primary"
                        onClick={onAnalyse}
                        disabled={!canAnalyse}
                    >
                        Analyse with Gemini
                    </button>
                </div>
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
