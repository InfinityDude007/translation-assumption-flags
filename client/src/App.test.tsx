// Tests for the app, over a fake API.

import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import App from "./App";
import type { Review, ReviewFlag } from "./api";

const SAMPLE = "avatar-atcoder_ABC000_A";

/** A flag on a Python line, implemented by a Java line. */
function flag(
    category: ReviewFlag["site"]["category"],
    line: number,
    java: number,
    verdict: ReviewFlag["verdict"],
): ReviewFlag {
    return {
        id: `${category}-${line}`,
        site: {
            rule: "rule",
            category,
            line,
            end_line: line,
            snippet: `snippet ${line}`,
            reason: `reason ${line}`,
        },
        verdict,
        translation_lines: [java],
        assumption: `assumption ${line}`,
        suggestion: verdict === "mismatch" ? "Math.floorDiv(n, 2)" : null,
    };
}

const REVIEW: Review = {
    run: "test-v2",
    model: "gemini-test",
    prompt_version: "2",
    flags: [flag("input", 1, 4, "handled"), flag("division", 2, 5, "mismatch")],
    dropped: [],
};

/** An error reply from the fake server. */
interface Failure {
    status: number;
    detail: string;
}

/** The fake server's replies, by method and path. */
type Routes = Record<string, unknown>;

let routes: Routes;
let posted: { path: string; body: unknown }[];

beforeEach(() => {
    window.location.hash = "";
    window.localStorage.clear();
    posted = [];
    routes = {
        "GET /samples": [
            { id: SAMPLE, dataset: "avatar", program: "atcoder_ABC000_A" },
        ],
        "GET /runs": [
            {
                name: "test-v2",
                model: "gemini-test",
                prompt_version: "2",
                created_at: "2026-11-22T06:00:00Z",
                samples: 1,
            },
        ],
        [`GET /samples/${SAMPLE}`]: {
            id: SAMPLE,
            source: "n = int(input())\nprint(n // 2)\n",
            translation: "a\nb\nc\nd\ne\n",
        },
        [`GET /decisions?sample_id=${SAMPLE}`]: [],
        "GET /baselines": [
            {
                name: "test-model",
                model: "fake/coder",
                prompt_version: "1",
                created_at: "2026-11-24T18:00:00Z",
                samples: 1,
            },
        ],
        [`GET /baselines/test-model/samples/${SAMPLE}`]: {
            baseline: "test-model",
            model: "fake/coder",
            threshold: 0.05,
            lines: ["a", "b", "c", "d", "e", ""].map((text, index) => ({
                line: index + 1,
                lowest: text ? (index === 4 ? 0.01 : 0.9) : 1,
                tokens: text
                    ? [{ text, probability: index === 4 ? 0.01 : 0.9 }]
                    : [],
            })),
        },
        "GET /baselines/test-model/score": {
            config: {
                name: "test-model",
                model: "fake/coder",
                prompt_version: "1",
                created_at: "2026-11-24T18:00:00Z",
            },
            threshold: 0.05,
            samples: [
                {
                    sample_id: SAMPLE,
                    group: "buggy",
                    no_bug: false,
                    bug_lines: [5],
                    latent_lines: [],
                    highlighted: [5],
                    bug_caught: true,
                    latent_caught: null,
                    false_alarms: 0,
                    bug_rank: 1,
                },
            ],
            bugs: 1,
            bugs_caught: 1,
            latent: 0,
            latent_caught: 0,
            highlighted: 1,
            false_alarms: 0,
            missing: [],
        },
        [`GET /runs/test-v2/samples/${SAMPLE}`]: REVIEW,
        "GET /runs/test-v2/score": {
            config: {
                name: "test-v2",
                model: "gemini-test",
                prompt_version: "2",
                created_at: "2026-11-22T06:00:00Z",
            },
            samples: [
                {
                    sample_id: SAMPLE,
                    group: "buggy",
                    no_bug: false,
                    bug_lines: [5],
                    latent_lines: [],
                    mismatch_flags: 3,
                    bug_caught: false,
                    latent_caught: null,
                    false_alarms: 3,
                    handled: 1,
                    unclear: 0,
                    dropped: 0,
                },
            ],
            bugs: 1,
            bugs_caught: 0,
            latent: 0,
            latent_caught: 0,
            mismatch_flags: 3,
            false_alarms: 3,
            missing: [],
        },
    };
    vi.stubGlobal(
        "fetch",
        vi.fn(async (url: string, init?: RequestInit) => {
            const path = url.replace(/^https?:\/\/[^/]+/, "");
            const method = init?.method ?? "GET";
            if (method === "POST")
                posted.push({ path, body: JSON.parse(String(init?.body)) });
            const reply = routes[`${method} ${path}`];
            if (reply && typeof reply === "object" && "status" in reply) {
                const { status, detail } = reply as Failure;
                return new Response(JSON.stringify({ detail }), { status });
            }
            if (method === "POST" && path === "/decisions") {
                const body = posted.at(-1)!.body as object;
                return new Response(
                    JSON.stringify({
                        ...body,
                        decided_at: "2026-11-23T22:00:00Z",
                    }),
                    { status: 201 },
                );
            }
            return new Response(
                JSON.stringify(reply ?? { detail: "not found" }),
                {
                    status: reply ? 200 : 404,
                },
            );
        }),
    );
});

afterEach(() => {
    vi.unstubAllGlobals();
});

/** The open flag's evidence block from one part of the system. */
const evidence = (title: string) =>
    screen
        .getByRole("heading", { name: new RegExp(`^${title}`) })
        .closest("section")!;

describe("App", () => {
    it("is named after the repository", async () => {
        render(<App />);
        expect(
            screen.getByRole("heading", {
                name: "Translation assumption flags",
            }),
        ).toBeInTheDocument();
        await screen.findByText("0 of 2 decided");
    });

    it("shows archived flags without calling Gemini or offering to", async () => {
        render(<App />);
        expect(await screen.findByText("0 of 2 decided")).toBeInTheDocument();
        expect(screen.getByLabelText("Run")).toHaveValue("test-v2");
        expect(
            screen.queryByRole("button", { name: /Analyse/ }),
        ).not.toBeInTheDocument();
        expect(posted).toEqual([]);
    });

    it("counts each verdict in the key above the code", async () => {
        render(<App />);
        await screen.findByText("0 of 2 decided");
        expect(
            screen.getByText(/Behaves differently \(1\)/),
        ).toBeInTheDocument();
        expect(screen.getByText(/Can't tell \(0\)/)).toBeInTheDocument();
        expect(screen.getByText(/Handled \(1\)/)).toBeInTheDocument();
    });

    it("explains every mark in a guide opened from the key", async () => {
        const user = userEvent.setup();
        render(<App />);
        await screen.findByText("0 of 2 decided");
        await user.click(
            screen.getByRole("button", { name: "What do these mean?" }),
        );
        const guide = screen.getByRole("dialog", {
            name: "How to read this page",
        });
        for (const text of [
            "Line marks",
            "Detector",
            "Explainer",
            "Checks",
            "Mark intended",
        ])
            expect(within(guide).getAllByText(text).length).toBeGreaterThan(0);
        await user.click(within(guide).getByRole("button", { name: "Close" }));
        expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    });

    it("labels each piece of evidence with where it came from", async () => {
        render(<App />);
        await screen.findByText("assumption 1");
        expect(evidence("Detector")).toHaveTextContent("reason 1");
        expect(evidence("Detector")).not.toHaveTextContent("assumption 1");
        expect(evidence("Explainer")).toHaveTextContent(
            "gemini-test, prompt 2, run test-v2",
        );
        expect(evidence("Explainer")).toHaveTextContent("assumption 1");
        expect(evidence("Your decision")).toHaveTextContent("not decided");
        expect(screen.queryByText("assumption 2")).not.toBeInTheDocument();
    });

    it("logs a decision with the flag as shown, then moves to the next flag", async () => {
        const user = userEvent.setup();
        render(<App />);
        await screen.findByText("assumption 1");
        await user.click(screen.getByRole("button", { name: /Mark intended/ }));

        expect(posted).toHaveLength(1);
        expect(posted[0].body).toMatchObject({
            sample_id: SAMPLE,
            run: "test-v2",
            model: "gemini-test",
            prompt_version: "2",
            flag: REVIEW.flags[0],
            decision: "intended",
        });
        expect(await screen.findByText("1 of 2 decided")).toBeInTheDocument();
        expect(screen.getByText("assumption 2")).toBeInTheDocument();
    });

    it("decides with the number keys", async () => {
        const user = userEvent.setup();
        render(<App />);
        await screen.findByText("assumption 1");
        await user.keyboard("j1");
        expect(posted[0].body).toMatchObject({
            flag: { id: "division-2" },
            decision: "confirmed",
        });
        const row = await screen.findByRole("button", { name: /snippet 2/ });
        expect(within(row).getByText("Confirmed bug")).toBeInTheDocument();
    });

    it("restores earlier decisions on the same run", async () => {
        routes[`GET /decisions?sample_id=${SAMPLE}`] = [
            {
                sample_id: SAMPLE,
                run: "test-v2",
                model: "gemini-test",
                prompt_version: "2",
                flag: REVIEW.flags[0],
                decision: "dismissed",
                note: "",
                decided_at: "",
            },
        ];
        render(<App />);
        expect(await screen.findByText("1 of 2 decided")).toBeInTheDocument();
        expect(screen.getByText("assumption 2")).toBeInTheDocument();
    });

    it("runs live analysis on its own page, explains a used-up limit and allows a retry", async () => {
        const user = userEvent.setup();
        routes["POST /analyse"] = {
            status: 429,
            detail: "RESOURCE_EXHAUSTED",
        } satisfies Failure;
        render(<App />);
        await screen.findByText("assumption 1");
        await user.click(screen.getByRole("link", { name: "Live analysis" }));
        expect(await screen.findByText(/No flags yet/)).toBeInTheDocument();
        expect(screen.queryByLabelText("Run")).not.toBeInTheDocument();
        expect(posted).toEqual([]);

        await user.click(
            screen.getByRole("button", { name: "Analyse with Gemini" }),
        );
        expect(await screen.findByRole("alert")).toHaveTextContent(
            "Gemini's daily request limit for this key is used up",
        );

        routes["POST /analyse"] = { ...REVIEW, run: null };
        await user.click(
            screen.getByRole("button", { name: "Analyse with Gemini" }),
        );
        expect(await screen.findByText("0 of 2 decided")).toBeInTheDocument();
        expect(evidence("Explainer")).toHaveTextContent(
            "gemini-test, prompt 2, live",
        );
        expect(posted.map((call) => call.path)).toEqual([
            "/analyse",
            "/analyse",
        ]);
    });

    it("widens the flag panel from the keyboard and remembers it", async () => {
        const user = userEvent.setup();
        render(<App />);
        await screen.findByText("assumption 1");
        const grip = screen.getByRole("separator", {
            name: "Resize the flag panel",
        });
        const before = Number(grip.getAttribute("aria-valuenow"));
        grip.focus();
        await user.keyboard("{ArrowLeft}");
        const after = Number(grip.getAttribute("aria-valuenow"));
        expect(after).toBeGreaterThan(before);
        expect(
            window.localStorage.getItem(
                "translation-assumption-flags.side-width",
            ),
        ).toBe(String(after));
    });

    it("shows each run's scores on their own page, and never on the review page", async () => {
        const user = userEvent.setup();
        render(<App />);
        await screen.findByText("0 of 2 decided");
        expect(screen.queryByText(/Bugs caught/)).not.toBeInTheDocument();

        await user.click(screen.getByRole("link", { name: "Scores" }));
        const runs = await screen.findByRole("table", {
            name: "Runs compared",
        });
        const row = within(runs).getByRole("row", { name: /test-v2/ });
        expect(row).toHaveTextContent("0 of 1 (0%)");
        expect(row).toHaveTextContent("0 of 3 (0%)");
        expect(screen.getByText("Missed")).toBeInTheDocument();
    });

    it("opens a missed program on the review page from the scores", async () => {
        const user = userEvent.setup();
        render(<App />);
        await screen.findByText("0 of 2 decided");
        await user.click(screen.getByRole("link", { name: "Scores" }));
        await user.click(
            await screen.findByRole("button", { name: "Missed bugs" }),
        );
        await user.click(screen.getByRole("button", { name: "Review" }));
        expect(await screen.findByLabelText("Run")).toHaveValue("test-v2");
        expect(window.location.hash).toBe("#/");
    });

    it("swaps the flags for token probabilities, and explains where they come from", async () => {
        const user = userEvent.setup();
        render(<App />);
        await screen.findByText("0 of 2 decided");
        await user.click(
            screen.getByRole("button", { name: "Token probabilities" }),
        );

        const panel = await screen.findByRole("complementary", {
            name: "Token probabilities",
        });
        expect(panel).toHaveTextContent("1 of 6 lines below 5%");
        expect(evidence("Local model")).toHaveTextContent("fake/coder");
        expect(evidence("Local model")).toHaveTextContent("not wrong");
        expect(screen.queryByText("0 of 2 decided")).not.toBeInTheDocument();
        expect(screen.queryByLabelText("Run")).not.toBeInTheDocument();

        const java = screen.getByRole("region", {
            name: "Java translation by GPT-4",
        });
        const low = within(java).getByTitle("1%");
        expect(low).toHaveTextContent("e");
        expect(low.closest(".line")).toHaveAttribute("data-doubt", "true");

        await user.click(within(panel).getByRole("button", { name: /line 5/ }));
        expect(low.closest(".line")).toHaveAttribute("data-selected", "true");

        await user.click(screen.getByRole("button", { name: "Flags" }));
        expect(await screen.findByText("0 of 2 decided")).toBeInTheDocument();
    });

    it("does not offer the probability view when there are no baselines", async () => {
        routes["GET /baselines"] = [];
        render(<App />);
        await screen.findByText("0 of 2 decided");
        expect(
            screen.queryByRole("button", { name: "Token probabilities" }),
        ).not.toBeInTheDocument();
    });

    it("scores the baseline beside the runs", async () => {
        const user = userEvent.setup();
        render(<App />);
        await screen.findByText("0 of 2 decided");
        await user.click(screen.getByRole("link", { name: "Scores" }));
        const table = await screen.findByRole("table", {
            name: "Token-probability baseline",
        });
        const row = within(table).getByRole("row", { name: /test-model/ });
        expect(row).toHaveTextContent("5%");
        expect(row).toHaveTextContent("1 of 1 (100%)");
        expect(row).toHaveTextContent("1 (1 program)");
    });

    it("says how to start the API when it cannot be reached", async () => {
        vi.stubGlobal(
            "fetch",
            vi.fn().mockRejectedValue(new TypeError("Failed to fetch")),
        );
        render(<App />);
        expect(await screen.findByRole("alert")).toHaveTextContent(
            "Start it with uv run serve",
        );
    });
});
