# Translation assumption flags
Submission for Assignment 2, Intelligent & Interactive Systems, University of Birmingham.

A review aid for LLM code translation.

When an LLM translates Python to Java, some lines force it to assume something the Python never states, such as how large an integer gets or how negative division rounds. This system finds those lines, has Gemini say what the Java assumed, and leaves the verdict to the reviewer.

**README prose word count: 1565** (excluding code, commands, file paths and the table of contents)

## Table of Contents
1. [Project Status](#project-status)
2. [Tech Stack](#tech-stack)
3. [Running or inspecting the work](#running-or-inspecting-the-work)
   - [Requirements](#requirements)
   - [Backend (`server/`)](#backend-server)
   - [Frontend (`client/`)](#frontend-client)
4. [Archive](#archive)
5. [Development Record](#development-record)
6. [AI assistance](#ai-assistance)
7. [More Details](#more-details)
8. [Additional Files](#additional-files)
9.  [Data and Licences](#data-and-licences)


## Project Status

| Part | Status |
|---|---|
| **Detector**: `ast` rules mark Python sites whose Java needs an assumption, in six categories from Pan et al.'s (2024) bug taxonomy, each rule with sources | Implemented, tested |
| **Explainer**: Gemini gives each site a verdict (behaves differently / can't tell / handled), the Java lines, the assumption and a fix, the server checks drop answers citing no real Java line | Implemented, tested |
| **Review interface**: Python and Java side by side, evidence labelled by who produced it, Confirm / Intended / Dismiss logged per flag | Implemented |
| **Archived runs** in `data/runs/`: 2 models and 2 prompt versions plus 2 repeats, so everything can be inspected without a key | Implemented |
| **Live analysis** of any sample with your own Gemini key | Implemented |
| **Scores page** against hand-tagged bug lines | Implemented |
| **Token-probability baseline** (the usual "highlight unlikely tokens") | Implemented with a **stand-in model**: real probabilities for the exact Java, from local Qwen2.5-Coder 1.5B/3B, not GPT-4 |
| **Translation**: the Java is Pan et al.'s saved GPT-4 output, which the tags depend on | Replayed from the dataset |
| **Live translation** of new programs | **Planned** |
| **Prompt v3**: give the explainer the problem's input constraints | **Planned** |

Results on 35 programs (21 test-exposed bugs, 8 latent bugs no test catches, 10 controls):

| Run | Bugs caught | Counting "can't tell" | Latent | False alarms |
|---|---|---|---|---|
| hydrogen v1 / v1b (repeat) | 14 / 13 | 14 / 13 | 7 / 7 | 28 / 24 |
| hydrogen v2 / v2b (repeat) | 12 / 11 | 14 / 13 | 7 / 7 | 16 / 13 |
| flash 3.8 v1 / v2 | 9 / 7 | 9 / 9 | 7 / 5 | 10 / 5 |
| Qwen 1.5B / 3B baseline, 70 lines | 7 / 7 | n/a | 1 / 2 | 61 / 60 lines |

**Limitations** (discussed in the report):
- 4 of the 21 bugs have no detector site, so Gemini is never asked about them. The detector was kept fixed so runs stay comparable.
- The explainer never sees the problem statement, so most remaining false alarms are "this `int` may overflow" where the bound is only in the problem text. Prompt v2 also moved 20 "handled" sites to "can't tell", so more lines are tinted (62 to 82).
- Identical repeats agree on 95% of verdicts. With 21 bugs, hydrogen's lead over flash (6 to 1 on bugs only one caught) is a direction, not proof (sign test p ≈ 0.125).
- Gemini's free tier (20 requests per model per day, frequent 503s, 2–4 minutes per program) made each run take days. This is why the archive exists.

## Tech Stack

| Technology | Role |
|---|---|
| Python 3.13, [uv](https://docs.astral.sh/uv/) | Backend, dependencies, `uv run` commands |
| `ast` | Parses Python for the detector |
| Gemini (`google-genai`) | Explainer; default `gemini-4-hydrogen`, chosen over `gemini-3.8-flash` on recall. Structured JSON against a pydantic schema |
| pydantic, FastAPI, uvicorn | Models, settings and the review API |
| PyTorch, `transformers` | Local Qwen2.5-Coder baseline |
| React 19, TypeScript, Vite | Review interface |
| ruff, mypy, Pyright, pytest; oxlint, tsc, Vitest | `uv run check`, `npm run check` |
| Claude Code (Anthropic) | AI assistant, see [AI assistance](#ai-assistance) |

**Undecided:** the model for live translation (one returning token probabilities would let the baseline score the translating model itself), and how prompt v3 should get the problem's constraints.

## Running or inspecting the work

### Requirements
1. [uv](https://docs.astral.sh/uv/getting-started/installation/)
2. Python 3.13+
3. Node.js 20.19+ or 22.12+.
4. npm 11.21.0+

> NOTE: No key is needed for the archived runs and scores.

### Backend (`server/`)
1. Install dependencies:
   - From `server/` (`uv sync` includes PyTorch, a large download):

```bash
uv sync
```

2. Check installed build is clean and working:
   - Runs mypy, pyright, ruff, and the pytest suite.
```bash
uv run check
```

3. Serve the API for the frontend:
```bash
uv run serve
```

### Frontend (`client/`)

1. Install dependencies:
   - From `client/`, in a second terminal:
```bash
npm install
```

2. Check installed build is clean and working:
   - Runs oxlint, the TypeScript checker and the vitest suite.
```bash
npm run check
```

3. Run the frontend:
```bash
npm run dev
```

4. Then open http://localhost:5173

> **Your own key** (live analysis and new runs only): get a free key from [Google AI Studio](https://aistudio.google.com/apikey), copy the template from [`.env.example`](server/.env.example) and set `GEMINI_API_KEY` in `server/.env`.

```bash
cp server/.env.example server/.env
```

## Archive
Without running anything, `data/runs/<run>/` holds every answer with its model and prompt version, plus `score.json`.
- `data/samples/<id>/meta.json` holds the tags.
- The prompt is in `server/src/server/explanation/prompts.py` and the rules in `server/src/server/detection/rules/rules.py`.

## Development Record

**Detector** ([`6961eaa`](https://github.com/InfinityDude007/translation-assumption-flags/commit/6961eaa)-[`c9eb5e7`](https://github.com/InfinityDude007/translation-assumption-flags/commit/c9eb5e7), [`9b24424`](https://github.com/InfinityDude007/translation-assumption-flags/commit/9b24424))
- Categories follow Pan et al. so flags can be scored against their bugs. Run on all 450 AVATAR and CodeNet programs: one labelled `int()` overflow had no site, so I added an `int()` rule.
- I found the rule reasons were unsourced, so I moved them into a sourced rule booklet. Checking each against the Python docs, the Java spec and small test programs found two wrong (`split(" ")`, `copyOfRange`); output on all 450 programs was unchanged.

**Ground truth** ([`0d8d09e`](https://github.com/InfinityDude007/translation-assumption-flags/commit/0d8d09e), [`2f04ab1`](https://github.com/InfinityDude007/translation-assumption-flags/commit/2f04ab1), [`b4dc849`](https://github.com/InfinityDude007/translation-assumption-flags/commit/b4dc849), [`fa74889`](https://github.com/InfinityDude007/translation-assumption-flags/commit/fa74889))
- Pan et al. label files, not lines. Each line tag was checked by fixing only the tagged lines and rerunning the tests (fixes in `evidence/tagging/fixes/`).
- Pan's labels failed for 8 of 25: 4 had no translation bug (exact-match tests) and 4 a different category. I kept Pan's labels, noted ours, and scored the 4 like controls.
- I added a `latent` field for differences no test catches, so flags on them are not false alarms. 3 of 10 "clean" controls hide one.

**Explainer and model** ([`bc6248a`](https://github.com/InfinityDude007/translation-assumption-flags/commit/bc6248a), [`ff0fec3`](https://github.com/InfinityDude007/translation-assumption-flags/commit/ff0fec3), [`08d67a5`](https://github.com/InfinityDude007/translation-assumption-flags/commit/08d67a5))
- First built on Claude; calls failed (HTTP 429) with my subscription token, which Anthropic reserves for its own apps, so I switched to Gemini's free tier.
- Gemini proposes, the server checks: answers citing no real Java line are dropped with a reason, and each result records its model and prompt version.
- I chose hydrogen (14 of 21 bugs, 28 false alarms) over flash (9, 10): in a review tool a missed bug costs more than a dismissed flag.

**Archive and scoring** ([`7ea73a4`](https://github.com/InfinityDude007/translation-assumption-flags/commit/7ea73a4), [`c529df6`](https://github.com/InfinityDude007/translation-assumption-flags/commit/c529df6), [`6d498f2`](https://github.com/InfinityDude007/translation-assumption-flags/commit/6d498f2))
- Because of the free-tier limits, answers are saved as they arrive, stopped runs resume, and scoring never calls Gemini. A run cannot mix models or prompts.
- I decided latent hits count as catches and the no-bug programs as controls, and that only 503s are retried, never 429s.

**Prompt iteration** ([`eac14a5`](https://github.com/InfinityDude007/translation-assumption-flags/commit/eac14a5), [`378a844`](https://github.com/InfinityDude007/translation-assumption-flags/commit/378a844); runs [`5fd5567`](https://github.com/InfinityDude007/translation-assumption-flags/commit/5fd5567)–[`4f60e07`](https://github.com/InfinityDude007/translation-assumption-flags/commit/4f60e07))
- 20 of v1's 28 false alarms claimed overflow for an unstated range. v2 changed one rule: a range "behaves differently" only with evidence in the program. I predicted it would lose two catches (ABC123_C, AGC019_A).
- Repeat runs measured the noise: one bug, 3–4 false alarms. False alarms fell 28/24 → 16/13, far beyond it. The lost catches moved to "can't tell", which the interface tints, so I added that score: 14/13 in both versions. I kept v2; v3 is planned.

**Review API and interface** ([`20758a2`](https://github.com/InfinityDude007/translation-assumption-flags/commit/20758a2), [`53ee2c4`](https://github.com/InfinityDude007/translation-assumption-flags/commit/53ee2c4), [`38f06d5`](https://github.com/InfinityDude007/translation-assumption-flags/commit/38f06d5), [`683cc0c`](https://github.com/InfinityDude007/translation-assumption-flags/commit/683cc0c))
- Review pages never receive the tags or Gemini's reasoning, so they cannot give the answer away; tests check this. Decisions are logged with the flag, model, prompt and run.
- After the first version I asked for live analysis on its own page, verdict-only colours (category colours read as severity), a key guide, and scores on a separate tab.

**Baseline** ([`029832a`](https://github.com/InfinityDude007/translation-assumption-flags/commit/029832a), [`e8db953`](https://github.com/InfinityDude007/translation-assumption-flags/commit/e8db953), [`6bf6e63`](https://github.com/InfinityDude007/translation-assumption-flags/commit/6bf6e63))
- No API gives GPT-4's probabilities for its saved output, so a local model scores the exact Java, labelled as a stand-in.
- Each threshold is set without the tags to mark 70 lines, about as many as the flags. Both models catch 7 of 21, so the gap is the method, not model size. ABC123_C's overflowing lines score 94–100%: the model shares the assumption.

## AI assistance

I used **Claude Code** (Anthropic) throughout.

- **Backend:** Claude gave code in chat. I applied and edited it, never with direct writes to the source. For example, I dropped a redundant credential validator, renamed settings, and split the detector into packages. Claude wrote the tests and docstrings first, I edited and adopted them as needed.
- **Reviews:** Claude's reviews of my commits found real faults I then fixed, such as renamed `visit_*` methods that silently disabled the detector, tests left on old setting names after my rename, and `uv run serve` pointing at a renamed file.
- **Tagging:** Claude Code ran each translation, proposed the bug lines and fixes, and verified them against the tests. I directed the rechecks (Pan's labels, the no-bug programs, checks beyond test output), decided the `latent` field and scoring rules, and adopted all 25 proposals unchanged. `evidence/tagging/bug_lines_review.md` is Claude's report for my review.
- **Frontend, mostly AI-generated:** Claude Code generated `client/` (design, code, styles and tests) with Anthropic's frontend-design skill. I set the scope, asked for the revisions above, fixed broken or misaligned elements myself, and checked it with `npm run check`, a build and browser checks on real runs, which caught a wrong default run.
- **Tests, mostly AI-generated:** Claude Code wrote unit and coverage tests (in `server/tests`). I reviewed the test cases to ensure they made sense and covered key functionality.
- **Analysis:** Claude computed run comparisons and the sign test from the archive, I chose what to run next and when to stop.
- **Direct writes**, with my permission: `evidence/tagging/` and `client/`. Claude also looked up commit hashes for this record.

## More Details
1. [`server/README.md`](server/README.md) (per-stage commands, API)
2. [`client/README.md`](client/README.md) (interface)
3. [`data/README.md`](data/README.md) (data formats and tags)
4. [`server/tests/README.md`](server/tests/README.md) (tests).

## Additional Files

- `data/samples/`, `data/runs/`, `data/baselines/`: programs and tags, saved runs, baseline probabilities.
- `evidence/tagging/`: the tagging review, `runone.py` and 21 fixed translations, see its [README](evidence/tagging/README.md) for rerunning a check. The fuzzing scripts were run outside the repository and are not included.
- Not committed: `data/raw/` (from `uv run get-dataset`, about 900 MB) and `data/decisions.jsonl` (written by the decision buttons on the UI).
- No ZIP accompanies the report.

## Data and Licences

- **Code:** MIT
- **Programs, translations and bug labels:** Pan, R. et al. (2024) *Lost in Translation: A Study of Bugs Introduced by Large Language Models while Translating Code*, ICSE 2024, [doi:10.5281/zenodo.10447705](https://doi.org/10.5281/zenodo.10447705), CC BY 4.0. Changes listed in `data/NOTICE`.
