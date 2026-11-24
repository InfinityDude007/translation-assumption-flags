// How each run's flags compare with the hand-tagged bug lines.

import { useEffect, useMemo, useState } from "react";
import {
    getBaselineScore,
    getScore,
    type BaselineScore,
    type BaselineSummary,
    type RunScore,
    type RunSummary,
    type SampleScore,
    type SampleSummary,
} from "../api";
import { describeError } from "../errors";
import { percent } from "../labels";

interface Props {
    runs: RunSummary[];
    baselines: BaselineSummary[];
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
export function ScoresPage(props: Props) {
    const { runs, baselines, samples, runName, onRun, onReview } = props;
    const [scores, setScores] = useState<Record<string, RunScore>>({});
    const [baselineScores, setBaselineScores] = useState<BaselineScore[]>([]);
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

    useEffect(() => {
        Promise.all(
            baselines.map((baseline) => getBaselineScore(baseline.name)),
        )
            .then(setBaselineScores)
            .catch((error) => setError(describeError(error)));
    }, [baselines]);

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
                <h2 id="runs-compared">Runs compared</h2>
                <p className="scores-lead">
                    Only flags Gemini marked “behaves differently” count. A flag
                    catches a bug when one of its Java lines is a hand-tagged
                    bug line; a false alarm hits no tagged line at all. The
                    review page also tints “can't tell” lines, so the columns
                    counting can't tell show what reached the reviewer either
                    way.
                </p>
                <div className="table-wrap">
                    <table
                        className="scores-table"
                        aria-labelledby="runs-compared"
                    >
                        <thead>
                            <tr>
                                <th scope="col">Run</th>
                                <th scope="col">Model</th>
                                <th scope="col">Prompt</th>
                                <th scope="col">Bugs caught</th>
                                <th scope="col">Latent bugs caught</th>
                                <th scope="col">Bugs, counting can't tell</th>
                                <th scope="col">Latent, counting can't tell</th>
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
                                                        score.bugs_surfaced,
                                                        score.bugs,
                                                    )}
                                                </td>
                                                <td className="number">
                                                    {share(
                                                        score.latent_surfaced,
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
                                            <td colSpan={6} className="muted">
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

            {baselineScores.length > 0 && (
                <section className="scores-section">
                    <h2 id="baseline-scores">Token-probability baseline</h2>
                    <p className="scores-lead">
                        The same Java, scored token by token by a local model:
                        the usual way to highlight generated code. It marks
                        lines, not flags, so its counts are per line. Each
                        model's threshold is set from its own probabilities so
                        that it marks the same number of lines in total, about
                        as many as the flags mark; the tagged lines play no
                        part. The rank ignores the threshold: it is where the
                        first bug line comes when a program's lines are sorted
                        from least to most likely, as a median over the programs
                        with a bug.
                    </p>
                    <div className="table-wrap">
                        <table
                            className="scores-table"
                            aria-labelledby="baseline-scores"
                        >
                            <thead>
                                <tr>
                                    <th scope="col">Baseline</th>
                                    <th scope="col">Model</th>
                                    <th scope="col">Marks lines below</th>
                                    <th scope="col">Bugs caught</th>
                                    <th scope="col">Latent bugs caught</th>
                                    <th scope="col">
                                        Marked lines on a tagged line
                                    </th>
                                    <th scope="col">False-alarm lines</th>
                                    <th scope="col">Median rank of the bug</th>
                                </tr>
                            </thead>
                            <tbody>
                                {baselineScores.map((score) => (
                                    <tr key={score.config.name}>
                                        <th scope="row">{score.config.name}</th>
                                        <td>{score.config.model}</td>
                                        <td className="number">
                                            {percent(score.threshold)}
                                        </td>
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
                                                score.highlighted -
                                                    score.false_alarms,
                                                score.highlighted,
                                            )}
                                        </td>
                                        <td className="number">
                                            {score.false_alarms}
                                        </td>
                                        <td className="number">
                                            {medianRank(score)}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </section>
            )}

            <section className="scores-section">
                <div className="scores-head">
                    <h2 id="by-program">Program by program</h2>
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
                        <table
                            className="scores-table"
                            aria-labelledby="by-program"
                        >
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

/** The median rank of the first bug line, over programs with a bug. */
function medianRank(score: BaselineScore): string {
    const ranks = score.samples
        .map((sample) => sample.bug_rank)
        .filter((rank): rank is number => rank !== null)
        .sort((a, b) => a - b);
    if (ranks.length === 0) return "none";
    const middle = Math.floor(ranks.length / 2);
    const median =
        ranks.length % 2
            ? ranks[middle]
            : (ranks[middle - 1] + ranks[middle]) / 2;
    return `${median} (${ranks.length} program${ranks.length === 1 ? "" : "s"})`;
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
