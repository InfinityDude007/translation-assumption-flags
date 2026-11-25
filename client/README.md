# client

The review UI, meant to be used by a reviewer when translating code.
- Uses React 19, TypeScript and Vite.
- It talks to the API in `server/` and shows the flags, the evidence for each, the reviewer's decisions and the score.
> See the [root README](../README.md) for the project overview.

**This frontend was mostly AI-generated.** Claude Code wrote it (design plan, code, styles and tests) using Anthropic's frontend-design skill. I set the scope, asked for revisions, checked the result, made changes where required, particularly broken/misaligned elements, and decided what to commit. See [AI assistance](../README.md#ai-assistance).

**README prose word count: 501** (excluding code, commands, file paths and the table of contents)

## Table of Contents
1. [Running Locally](#running-locally)
   - [Requirements](#requirements)
   - [Steps](#steps)
   - [Developer tooling](#developer-tooling)
2. [Pages](#pages)
3. [Decisions and Keys](#decisions-and-keys)
4. [Layout](#layout)
5. [How it was checked](#how-it-was-checked)


## Running Locally

### Requirements
- Node.js 20.19+ or 22.12+
- npm 11.21.0+
- API running (`uv run serve` in `server/`).

### Steps
1. Install project dependencies:
```bash
npm install
```

2. Start the client service:
```bash
npm run dev
```

3. Open http://localhost:5173.
>To use an API somewhere other than http://127.0.0.1:8000, copy `.env.example` to `.env` and set `VITE_API_URL`.

### Developer tooling
1. `npm run check` runs oxlint, the TypeScript compiler and the Vitest tests.
```bash
npm run check
```
2. `npm run build` makes a production build in `dist/`.
```bash
npm run build
```

## Pages

1. **Archived runs** (`#/`):
   - Pick a program and a saved run. Python (source) and Java (translation) sit side by side, with a curve from each flagged Python line to its Java lines.
   - Lines are marked by verdict only: red `!` behaves differently, amber `?` can't tell, grey `–` handled.
   - Selecting a flag opens its evidence in three labelled blocks: **Detector** (rule and reason), **Explainer** (Gemini's verdict, assumption and fix, with model, prompt version and run) and **Your decision**.
   - **Token probabilities** toggle shows the baseline instead: tokens shaded by how unlikely the local model found them, with its own key and guide in place of the verdicts.
2. **Live analysis** (`#/live`): the same view, but Gemini is called only when you click **Analyse with Gemini**, with elapsed time shown and errors that say what to do (no key, rate limit, model unavailable).
3. **Scores** (`#/scores`): every run and baseline against the hand-tagged bug lines, then one run program by program, with a Review link to each program.
   - Only the Scores tab shows ground truth.

## Decisions and Keys

Confirm, Intended and Dismiss (keys `1`, `2`, `3`) send a decision to `POST /decisions` with an optional note, then move to the next undecided flag; `j` and `k` move between flags. Changing a decision appends a new entry, so the log keeps the history. The "What do these mean?" button beside the key explains every mark in the current view, flags or token probabilities.

## Layout

| File                                                                    | Contents                                                  |
| ----------------------------------------------------------------------- | --------------------------------------------------------- |
| `src/App.tsx`                                                           | Page tabs and the state shared between pages              |
| `src/api.ts`                                                            | Typed API client                                          |
| `src/components/ReviewPage.tsx`                                         | Archived and live review                                  |
| `src/components/CodeBench.tsx`                                          | Side-by-side code, gutter marks and the connecting curves |
| `src/components/FlagPanel.tsx`, `Evidence.tsx`                          | Flag list and evidence blocks                             |
| `src/components/ProbabilityPanel.tsx`                                   | Token-probability view                                    |
| `src/components/ScoresPage.tsx`                                         | Scores tables                                             |
| `src/components/KeyGuide.tsx`                                           | The key explanation dialog                                |
| `src/decisions.ts`, `errors.ts`, `highlight.ts`, `labels.ts`, `runs.ts` | Helpers, each with a `.test.ts`                           |

## How it was checked

1. `npm run check` and a production build pass.
2. Browser checks on the real archived runs: a decision was logged with its run, model, prompt version and flag.
3. The no-key message on Live analysis.
4. The Scores figures were compared against `score.json`. 
   
The browser check found one defect, now fixed: the default run was a repeat run instead of the latest prompt version.
