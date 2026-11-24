// Types and calls for the review API served by `uv run serve`.

/** Mismatch categories, as named by the detector. */
export type Category =
    "numeric" | "input" | "output" | "api" | "division" | "errors";

/** Gemini's verdict on a site. */
export type Verdict = "mismatch" | "handled" | "unclear";

/** The reviewer's call on a flag. */
export type DecisionKind = "confirmed" | "intended" | "dismissed";

/** A sample in the picker, without its labels. */
export interface SampleSummary {
    id: string;
    dataset: string;
    program: string;
}

/** A sample's Python source and Java translation. */
export interface SampleCode {
    id: string;
    source: string;
    translation: string;
}

/** An archived explainer run. */
export interface RunSummary {
    name: string;
    model: string;
    prompt_version: string;
    created_at: string;
    samples: number;
}

/** A token-probability baseline: a local model's view of the same Java. */
export interface BaselineSummary {
    name: string;
    model: string;
    prompt_version: string;
    created_at: string;
    samples: number;
}

/** One token's share of a Java line, with the local model's probability. */
export interface TokenProbability {
    text: string;
    probability: number;
}

/** One Java line's tokens, and the probability of its least likely token. */
export interface LineProbability {
    line: number;
    lowest: number;
    tokens: TokenProbability[];
}

/** One program's token probabilities, and the threshold the view marks below. */
export interface ProbabilityReview {
    baseline: string;
    model: string;
    threshold: number;
    lines: LineProbability[];
}

/** How one sample's highlighted lines compare with its hand-tagged Java lines. */
export interface BaselineSampleScore {
    sample_id: string;
    group: "buggy" | "control";
    no_bug: boolean;
    bug_lines: number[];
    latent_lines: number[];
    highlighted: number[];
    bug_caught: boolean | null;
    latent_caught: boolean | null;
    false_alarms: number;
    bug_rank: number | null;
}

/** A baseline's totals at the configured threshold. */
export interface BaselineScore {
    config: {
        name: string;
        model: string;
        prompt_version: string;
        created_at: string;
    };
    threshold: number;
    samples: BaselineSampleScore[];
    bugs: number;
    bugs_caught: number;
    latent: number;
    latent_caught: number;
    highlighted: number;
    false_alarms: number;
    missing: string[];
}

/** How one sample's mismatch flags compare with its hand-tagged Java lines. */
export interface SampleScore {
    sample_id: string;
    group: "buggy" | "control";
    no_bug: boolean;
    bug_lines: number[];
    latent_lines: number[];
    mismatch_flags: number;
    bug_caught: boolean | null;
    latent_caught: boolean | null;
    false_alarms: number;
    handled: number;
    unclear: number;
    dropped: number;
}

/** A run's totals over the samples archived so far. */
export interface RunScore {
    config: {
        name: string;
        model: string;
        prompt_version: string;
        created_at: string;
    };
    samples: SampleScore[];
    bugs: number;
    bugs_caught: number;
    latent: number;
    latent_caught: number;
    mismatch_flags: number;
    false_alarms: number;
    missing: string[];
}

/** A place in the source where the translation had to make an assumption. */
export interface Site {
    rule: string;
    category: Category;
    line: number;
    end_line: number;
    snippet: string;
    reason: string;
}

/** A flag as the reviewer sees it, without Gemini's reasoning. */
export interface ReviewFlag {
    id: string;
    site: Site;
    verdict: Verdict;
    translation_lines: number[];
    assumption: string;
    suggestion: string | null;
}

/** A site that produced no flag, with the reason. */
export interface DroppedSite {
    site: Site;
    reason: string;
}

/** The flags for one program, archived or live. */
export interface Review {
    run: string | null;
    model: string | null;
    prompt_version: string;
    flags: ReviewFlag[];
    dropped: DroppedSite[];
}

/** A reviewer's decision, as sent to the API. */
export interface DecisionRequest {
    sample_id: string | null;
    run: string | null;
    model: string | null;
    prompt_version: string;
    flag: ReviewFlag;
    decision: DecisionKind;
    note: string;
}

/** A logged decision. */
export interface Decision extends DecisionRequest {
    decided_at: string;
}

/** A failed API call, with the HTTP status and the server's message. */
export class ApiError extends Error {
    readonly status: number;

    /**
     * @param status HTTP status, or 0 if the server could not be reached.
     * @param message The server's `detail`, or a description of the failure.
     */
    constructor(status: number, message: string) {
        super(message);
        this.status = status;
    }
}

/** Base URL of the API; set VITE_API_URL to override. */
export const API_URL: string =
    import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000";

/**
 * Call the API and parse its JSON reply.
 *
 * @param path Route, starting with a slash.
 * @param init Fetch options, e.g. method and body.
 * @returns The parsed reply.
 * @throws ApiError if the server cannot be reached or replies with an error.
 */
async function call<T>(path: string, init?: RequestInit): Promise<T> {
    let response: Response;
    try {
        response = await fetch(API_URL + path, init);
    } catch {
        throw new ApiError(
            0,
            `Cannot reach the API at ${API_URL}. Start it with uv run serve.`,
        );
    }
    if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        const detail =
            typeof body.detail === "string" ? body.detail : response.statusText;
        throw new ApiError(response.status, detail);
    }
    return response.json() as Promise<T>;
}

/** Send a JSON body with POST. */
function post<T>(path: string, body: unknown): Promise<T> {
    return call<T>(path, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
    });
}

/** List the samples. */
export const listSamples = () => call<SampleSummary[]>("/samples");

/** Fetch a sample's code. */
export const getSample = (id: string) =>
    call<SampleCode>(`/samples/${encodeURIComponent(id)}`);

/** List the archived runs. */
export const listRuns = () => call<RunSummary[]>("/runs");

/** Fetch a sample's archived review from a run, without calling Gemini. */
export const getArchivedReview = (run: string, id: string) =>
    call<Review>(
        `/runs/${encodeURIComponent(run)}/samples/${encodeURIComponent(id)}`,
    );

/** Score a run against the tagged lines; only the Scores page calls this. */
export const getScore = (run: string) =>
    call<RunScore>(`/runs/${encodeURIComponent(run)}/score`);

/** List the token-probability baselines. */
export const listBaselines = () => call<BaselineSummary[]>("/baselines");

/** Fetch a sample's token probabilities from a baseline. */
export const getProbabilities = (baseline: string, id: string) =>
    call<ProbabilityReview>(
        `/baselines/${encodeURIComponent(baseline)}/samples/${encodeURIComponent(id)}`,
    );

/** Score a baseline against the tagged lines; only the Scores page calls this. */
export const getBaselineScore = (baseline: string) =>
    call<BaselineScore>(`/baselines/${encodeURIComponent(baseline)}/score`);

/** Analyse a program now, calling Gemini. */
export const analyse = (source: string, translation: string) =>
    post<Review>("/analyse", { source, translation });

/** List the decisions logged on a sample. */
export const listDecisions = (sampleId: string) =>
    call<Decision[]>(`/decisions?sample_id=${encodeURIComponent(sampleId)}`);

/** Log a decision on a flag. */
export const saveDecision = (request: DecisionRequest) =>
    post<Decision>("/decisions", request);
