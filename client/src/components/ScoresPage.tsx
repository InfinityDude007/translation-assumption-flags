// How each run's flags compare with the hand-tagged bug lines.

import { useEffect, useMemo, useState } from "react";
import {
    getScore,
    type RunScore,
    type RunSummary,
    type SampleScore,
    type SampleSummary,
} from "../api";
import { describeError } from "../errors";

interface Props {
    runs: RunSummary[];
    samples: SampleSummary[];
    runName: string;
    onRun: (name: string) => void;
    onReview: (sampleId: string, run: string) => void;
}

/** Which programs the breakdown shows. */
type Filter = "all" | "missed" | "false-alarms";

/** A count out of a total, with the percentage when the total is not zero. */
function share(part: number, whole: number): string {
    if (whole === 0) return "none";
    return `${part} of ${whole} (${Math.round((part / whole) * 100)}%)`;
}

/**
 * The scores page: every run side by side, then one run program by program.
 *
 * It shows the ground truth, which the review pages hide, so it sits on its
 * own tab and is meant for evaluation, not for reviewing.
 */
export function ScoresPage({ runs, samples, runName, onRun, onReview }: Props) {
    const [scores, setScores] = useState<Record<string, RunScore>>({});
    const [error, setError] = useState<string | null>(null);
    const [filter, setFilter] = useState<Filter>("all");

    useEffect(() => {
        Promise.all(runs.map((run) => getScore(run.name)))
            .then((all) =>
                setScores(
                    Object.fromEntries(
                        all.map((score) => [score.config.name, score]),
                    ),
                ),
            )
            .catch((error) => setError(describeError(error)));
    }, [runs]);

    const programs = useMemo(
        () => new Map(samples.map((sample) => [sample.id, sample.program])),
        [samples],
    );
    const ordered = [...runs].sort(
        (a, b) =>
            a.prompt_version.localeCompare(b.prompt_version, undefined, {
                numeric: true,
            }) ||
            a.model.localeCompare(b.model) ||
            a.created_at.localeCompare(b.created_at),
    );
    const chosen = scores[runName];
    const shown = (chosen?.samples ?? []).filter(
        (sample) =>
            filter === "all" ||
            (filter === "missed" && sample.bug_caught === false) ||
            (filter === "false-alarms" && sample.false_alarms > 0),
    );

    if (error)
        return (
            <main className="scores">
                <p className="status status-error" role="alert">
                    {error}
                </p>
            </main>
        );

    return (
        <main className="scores">
            <section className="scores-section">
                <h2>Runs compared</h2>
                <p className="scores-lead">
                    Only flags Gemini marked “behaves differently” count. A flag
                    catches a bug when one of its Java lines is a hand-tagged
                    bug line; a false alarm hits no tagged line at all.
                </p>
                <div className="table-wrap">
                    <table className="scores-table">
                        <thead>
                            <tr>
                                <th scope="col">Run</th>
                                <th scope="col">Model</th>
                                <th scope="col">Prompt</th>
                                <th scope="col">Bugs caught</th>
                                <th scope="col">Latent bugs caught</th>
                                <th scope="col">Flags on a tagged line</th>
                                <th scope="col">False alarms</th>
                                <th scope="col">Programs scored</th>
                            </tr>
                        </thead>
                        <tbody>
                            {ordered.map((run) => {
                                const score = scores[run.name];
                                const scored = score
                                    ? score.samples.length
                                    : run.samples;
                                const total =
                                    scored + (score?.missing.length ?? 0);
                                return (
                                    <tr
                                        key={run.name}
                                        data-current={
                                            run.name === runName || undefined
                                        }
                                    >
                                        <th scope="row">
                                            <button
                                                type="button"
                                                className="link-button"
                                                onClick={() => onRun(run.name)}
                                            >
                                                {run.name}
                                            </button>
                                        </th>
                                        <td>{run.model}</td>
                                        <td>{run.prompt_version}</td>
                                        {score ? (
                                            <>
                                                <td className="number">
                                                    {share(
                                                        score.bugs_caught,
                                                        score.bugs,
                                                    )}
                                                </td>
                                                <td className="number">
                                                    {share(
                                                        score.latent_caught,
                                                        score.latent,
                                                    )}
                                                </td>
                                                <td className="number">
                                                    {share(
                                                        score.mismatch_flags -
                                                            score.false_alarms,
                                                        score.mismatch_flags,
                                                    )}
                                                </td>
                                                <td className="number">
                                                    {score.false_alarms}
                                                </td>
                                            </>
                                        ) : (
                                            <td colSpan={4} className="muted">
                                                Scoring…
                                            </td>
                                        )}
                                        <td className="number">
                                            {scored === total
                                                ? scored
                                                : `${scored} of ${total}, in progress`}
                                        </td>
                                    </tr>
                                );
                            })}
                        </tbody>
                    </table>
                </div>
            </section>

            <section className="scores-section">
                <div className="scores-head">
                    <h2>Program by program</h2>
                    <label>
                        <span>Run</span>
                        <select
                            value={runName}
                            onChange={(event) => onRun(event.target.value)}
                        >
                            {ordered.map((run) => (
                                <option key={run.name} value={run.name}>
                                    {run.name}
                                </option>
                            ))}
                        </select>
                    </label>
                    <div className="segmented" role="group" aria-label="Show">
                        {(
                            [
                                ["all", "All programs"],
                                ["missed", "Missed bugs"],
                                ["false-alarms", "With false alarms"],
                            ] as [Filter, string][]
                        ).map(([value, label]) => (
                            <button
                                key={value}
                                type="button"
                                aria-pressed={filter === value}
                                onClick={() => setFilter(value)}
                            >
                                {label}
                            </button>
                        ))}
                    </div>
                </div>
                {!chosen ? (
                    <p className="status">Scoring…</p>
                ) : (
                    <div className="table-wrap">
                        <table className="scores-table">
                            <thead>
                                <tr>
                                    <th scope="col">Program</th>
                                    <th scope="col">Kind</th>
                                    <th scope="col">Bug</th>
                                    <th scope="col">Latent bug</th>
                                    <th scope="col">Behaves differently</th>
                                    <th scope="col">False alarms</th>
                                    <th scope="col">Can't tell</th>
                                    <th scope="col">Handled</th>
                                    <th scope="col">Dropped</th>
                                    <th scope="col">
                                        <span className="visually-hidden">
                                            Open
                                        </span>
                                    </th>
                                </tr>
                            </thead>
                            <tbody>
                                {shown.map((sample) => (
                                    <tr key={sample.sample_id}>
                                        <th scope="row">
                                            {programs.get(sample.sample_id) ??
                                                sample.sample_id}
                                        </th>
                                        <td>{kind(sample)}</td>
                                        <Outcome value={sample.bug_caught} />
                                        <Outcome value={sample.latent_caught} />
                                        <td className="number">
                                            {sample.mismatch_flags}
                                        </td>
                                        <td className="number">
                                            {sample.false_alarms || ""}
                                        </td>
                                        <td className="number">
                                            {sample.unclear || ""}
                                        </td>
                                        <td className="number">
                                            {sample.handled || ""}
                                        </td>
                                        <td className="number">
                                            {sample.dropped || ""}
                                        </td>
                                        <td>
                                            <button
                                                type="button"
                                                className="link-button"
                                                onClick={() =>
                                                    onReview(
                                                        sample.sample_id,
                                                        runName,
                                                    )
                                                }
                                            >
                                                Review
                                            </button>
                                        </td>
                                    </tr>
                                ))}
                                {shown.length === 0 && (
                                    <tr>
                                        <td colSpan={10} className="muted">
                                            No programs match.
                                        </td>
                                    </tr>
                                )}
                            </tbody>
                        </table>
                    </div>
                )}
            </section>
        </main>
    );
}

/** Name the kind of program: a translation bug, a control, or a non-translation failure. */
function kind(sample: SampleScore): string {
    if (sample.group === "control") return "Control (correct)";
    return sample.no_bug ? "Fails, not a translation bug" : "Translation bug";
}

/** A caught, missed or not-applicable cell. */
function Outcome({ value }: { value: boolean | null }) {
    if (value === null) return <td className="muted">none</td>;
    return (
        <td className="outcome" data-caught={value}>
            {value ? "Caught" : "Missed"}
        </td>
    );
}
