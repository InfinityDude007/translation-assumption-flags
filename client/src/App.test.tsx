// Tests for the review screen, over a fake API.

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
        [`GET /runs/test-v2/samples/${SAMPLE}`]: REVIEW,
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
                { status: reply ? 200 : 404 },
            );
        }),
    );
});

afterEach(() => {
    vi.unstubAllGlobals();
});

describe("App", () => {
    it("shows archived flags with where they came from, without calling Gemini", async () => {
        render(<App />);
        expect(
            await screen.findByText("0 of 2 flags decided"),
        ).toBeInTheDocument();
        expect(
            screen.getByText(
                /Saved by gemini-test with prompt version 2, in run test-v2/,
            ),
        ).toBeInTheDocument();
        expect(posted).toEqual([]);
    });

    it("opens the first undecided flag with its evidence", async () => {
        render(<App />);
        expect(await screen.findByText("assumption 1")).toBeInTheDocument();
        expect(screen.getByText("reason 1")).toBeInTheDocument();
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
        expect(
            await screen.findByText("1 of 2 flags decided"),
        ).toBeInTheDocument();
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
        expect(
            await screen.findByText("1 of 2 flags decided"),
        ).toBeInTheDocument();
        expect(screen.getByText("assumption 2")).toBeInTheDocument();
    });

    it("asks before a live analysis, explains a used-up limit and lets the reviewer retry", async () => {
        const user = userEvent.setup();
        routes["POST /analyse"] = {
            status: 429,
            detail: "RESOURCE_EXHAUSTED",
        } satisfies Failure;
        render(<App />);
        await screen.findByText("assumption 1");
        await user.selectOptions(screen.getByLabelText("Flags from"), "live");
        expect(posted).toEqual([]);

        await user.click(
            screen.getByRole("button", { name: "Analyse with Gemini" }),
        );
        expect(await screen.findByRole("alert")).toHaveTextContent(
            "Gemini's daily request limit for this key is used up",
        );

        routes["POST /analyse"] = REVIEW;
        await user.click(screen.getByRole("button", { name: "Try again" }));
        expect(
            await screen.findByText("0 of 2 flags decided"),
        ).toBeInTheDocument();
        expect(posted.map((call) => call.path)).toEqual([
            "/analyse",
            "/analyse",
        ]);
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
