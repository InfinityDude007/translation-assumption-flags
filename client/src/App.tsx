// The app shell: the name, the page links, and the data both pages share.

import { useEffect, useState } from "react";
import {
    listRuns,
    listSamples,
    type RunSummary,
    type SampleSummary,
} from "./api";
import { ReviewPage, type Status } from "./components/ReviewPage";
import { describeError } from "./errors";
import { APP_NAME } from "./labels";
import { defaultRun, LIVE } from "./runs";

/** The two pages: flags saved in earlier runs, or flags from Gemini now. */
type Page = "archived" | "live";

/** Read the page from the address, e.g. #/live. */
const pageFromHash = (): Page =>
    window.location.hash === "#/live" ? "live" : "archived";

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
                </nav>
            </header>
            {startError ? (
                <main className="start-error">
                    <p role="alert">{startError}</p>
                </main>
            ) : (
                <ReviewPage
                    mode={page}
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
