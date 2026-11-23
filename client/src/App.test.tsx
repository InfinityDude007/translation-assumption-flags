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
