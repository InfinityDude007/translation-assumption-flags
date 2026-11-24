// The app shell: the name, the page links, and the data both pages share.

import { useEffect, useState } from "react";
import {
    listRuns,
    listSamples,
    type RunSummary,
    type SampleSummary,
} from "./api";
import { ReviewPage, type Status } from "./components/ReviewPage";
import { ScoresPage } from "./components/ScoresPage";
import { describeError } from "./errors";
import { APP_NAME } from "./labels";
import { defaultRun, LIVE } from "./runs";

/** The pages: saved flags, flags from Gemini now, and how each run scored. */
type Page = "archived" | "live" | "scores";

/** Read the page from the address, e.g. #/live. */
const pageFromHash = (): Page => {
    if (window.location.hash === "#/live") return "live";
    if (window.location.hash === "#/scores") return "scores";
    return "archived";
};

/**
 * The app shell.
 *
 * The program, the chosen run and any live results live here, so switching
 * pages keeps them.
 */
export default function App() {
    const [page, setPage] = useState<Page>(pageFromHash);
    const [samples, setSamples] = useState<SampleSummary[]>([]);
    const [runs, setRuns] = useState<RunSummary[]>([]);
    const [startError, setStartError] = useState<string | null>(null);
    const [sampleId, setSampleId] = useState<string | null>(null);
    const [runName, setRunName] = useState<string>(LIVE);
    const [live, setLive] = useState<Record<string, Status>>({});

    useEffect(() => {
        const onHash = () => setPage(pageFromHash());
        window.addEventListener("hashchange", onHash);
        return () => window.removeEventListener("hashchange", onHash);
    }, []);

    useEffect(() => {
        Promise.all([listSamples(), listRuns()])
            .then(([samples, runs]) => {
                setSamples(samples);
                setRuns(runs);
                setSampleId(samples[0]?.id ?? null);
                setRunName(defaultRun(runs, samples.length));
            })
            .catch((error) => setStartError(describeError(error)));
    }, []);

    return (
        <div className="app">
            <header className="bar">
                <h1>{APP_NAME}</h1>
                <nav aria-label="Pages">
                    <a
                        href="#/"
                        aria-current={page === "archived" ? "page" : undefined}
                    >
                        Archived runs
                    </a>
                    <a
                        href="#/live"
                        aria-current={page === "live" ? "page" : undefined}
                    >
                        Live analysis
                    </a>
                    <a
                        href="#/scores"
                        aria-current={page === "scores" ? "page" : undefined}
                    >
                        Scores
                    </a>
                </nav>
            </header>
            {startError ? (
                <main className="start-error">
                    <p role="alert">{startError}</p>
                </main>
            ) : page === "scores" ? (
                <ScoresPage
                    runs={runs}
                    samples={samples}
                    runName={runName}
                    onRun={setRunName}
                    onReview={(id, run) => {
                        setSampleId(id);
                        setRunName(run);
                        window.location.hash = "#/";
                    }}
                />
            ) : (
                <ReviewPage
                    mode={page === "live" ? "live" : "archived"}
                    samples={samples}
                    runs={runs}
                    sampleId={sampleId}
                    onSample={setSampleId}
                    runName={runName}
                    onRun={setRunName}
                    live={live}
                    setLive={setLive}
                />
            )}
        </div>
    );
}
