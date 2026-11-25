# server

[![Coverage](tests/coverage.svg)](tests/README.md#coverage-report)

The backend for this project: the detector, the Gemini explainer, the run archive and scoring, the token-probability baseline, and the review API.
> See the [root README](../README.md) for the project overview.

**README prose word count: 674** (excluding code, commands, file paths and the table of contents)

## Table of Contents
1. [Running Locally](#running-locally)
   - [Requirements](#requirements)
   - [Steps](#steps)
   - [Developer tooling \& running features](#developer-tooling--running-features)
2. [Folder Layout](#folder-layout)
3. [How the explainer's answer is checked](#how-the-explainers-answer-is-checked)
4. [Scoring Rules](#scoring-rules)
5. [Settings](#settings)
6. [API](#api)

## Running Locally

### Requirements
1. [uv](https://docs.astral.sh/uv/getting-started/installation/)
2. Python 3.13+

### Steps
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

### Developer tooling & running features

> Every setting has a default, so nothing needs configuring to browse the archived data. For Gemini calls, copy `.env.example` to `.env` and set `GEMINI_API_KEY`. `.env` is gitignored.

| Command | What it does | Needs |
|---|---|---|
| `uv run get-dataset` | Downloads Pan et al.'s Zenodo data into `data/raw/`, checks the checksums and keeps only the Python-to-Java parts (about 900 MB) | Network |
| `uv run make-samples` | Selects 25 buggy and 10 control programs (seed 2026) into `data/samples/`. Never overwrites an existing sample, so the hand tags are safe | `data/raw/` |
| `uv run detect FILE.py` | Prints the detector's sites for a Python file as JSON | Nothing |
| `uv run explain FILE.py FILE.java` | Runs the detector and asks Gemini about each site; prints the checked flags as JSON | Key |
| `uv run evaluate --name RUN [--model ID] [--samples ID ...]` | Runs the explainer over the samples into `data/runs/RUN/`, one file per program as it finishes. Rerunning resumes; a run name cannot mix models or prompt versions | Key |
| `uv run score RUN` | Scores a run against the tags and writes `data/runs/RUN/score.json` | Nothing |
| `uv run baseline --name NAME [--model ID] [--samples ID ...]` | Scores every Java token with a local model into `data/baselines/NAME/` (downloads the model from Hugging Face on first use: about 3 GB for 1.5B, 6 GB for 3B) | Disk, time |
| `uv run score-baseline NAME [--threshold P]` | Scores a baseline; without `--threshold`, the threshold that marks `BASELINE_LINE_BUDGET` lines | Nothing |
| `uv run serve` | Starts the review API on `API_HOST:API_PORT` | Key only for `/analyse` |

The archived runs were made with, for example:

```bash
uv run evaluate --name hydrogen-v2 --model gemini-4-hydrogen
uv run score hydrogen-v2
```

A prompt-v1 run has to be made from a checkout of [`455b3eb`](https://github.com/InfinityDude007/translation-assumption-flags/commit/455b3eb) or earlier, because the run guard rejects a prompt version that differs from the run's.

## Folder Layout

| Package | Contents |
|---|---|
| `detection/` | `MismatchVisitor` (the `ast` rules), `detect()`, and `rules/`: the rule booklet, where each rule has a category, a reason and its sources |
| `explanation/` | The prompt (`PROMPT_VERSION`, system prompt, `build_prompt`), the answer schema, and `explain()`, which calls Gemini and checks the answer |
| `gemini.py` | Cached Gemini client: structured output against a pydantic schema, 503 retries (1–10 s, up to 10 retries), errors keep the HTTP status |
| `evaluation/` | Run archive (`run_samples`, resume, model and prompt guard) and scoring |
| `baseline/` | Token scoring with a local model, token-to-line mapping, the line-budget threshold and scoring |
| `dataset/` | Download, sample selection and the `meta.json` model (`SampleMeta`, with `bug_lines` and `latent`) |
| `api/` | FastAPI app, request and response models, and the append-only decision log |
| `settings/` | One pydantic-settings class per area, read from `.env` |
| `dev.py` | The `check`, `tests` and `fix` commands |

## How the explainer's answer is checked

Gemini's answer is a claim; the server decides what reaches the reviewer. In `explanation/explainer.py`:

- Answers for unknown or repeated site ids are ignored.
- Java line numbers outside the translation are removed. A site left with no Java line, or with no answer, is dropped with a recorded reason, which the interface shows.
- A suggested fix is kept only for a "behaves differently" verdict.
- Gemini's raw answer, model and prompt version are saved with each result. The reasoning field is kept in the archive for inspection but never sent to the interface.

## Scoring Rules

In `evaluation/scoring.py`:

- **Caught**: a "behaves differently" flag has a tagged Java line. **Surfaced**: the same, counting "can't tell" flags too, since the interface tints both.
- **False alarm**: a "behaves differently" flag that hits no bug or latent line.
- A flag on a latent line counts as a catch, and latent bugs are reported separately.
- The 4 programs with no translation bug count like controls.

## Settings

All optional except the key. See `.env.example` for the full list.

| Variable | Default |
|---|---|
| `GEMINI_API_KEY` | none (needed for Gemini calls) |
| `GEMINI_MODEL` | `gemini-4-hydrogen` |
| `GEMINI_MAX_OUTPUT_TOKENS` | `24000` |
| `EVALUATION_PAUSE_SECONDS` | `6.0`, pause between calls for the free-tier rate limit |
| `BASELINE_MODEL` | `Qwen/Qwen2.5-Coder-1.5B-Instruct` |
| `BASELINE_LINE_BUDGET` | `70` |
| `API_HOST`, `API_PORT` | `127.0.0.1`, `8000` |
| `API_CORS_ORIGINS` | `["http://localhost:5173"]` |
| `DATASET_*_DIR`, `EVALUATION_RUNS_DIR`, `BASELINE_BASELINES_DIR`, `API_DECISIONS_FILE` | folders under `data/` |

## API

| Route | Returns |
|---|---|
| `GET /samples`, `GET /samples/{id}` | The programs, without tags, Pan's labels or notes |
| `GET /runs`, `GET /runs/{run}/samples/{id}` | Archived runs and one program's checked flags (no Gemini call) |
| `GET /runs/{run}/score` | The run's scores, computed on request |
| `GET /baselines`, `GET /baselines/{name}/samples/{id}`, `GET /baselines/{name}/score` | Token probabilities and their scores |
| `POST /analyse` | Live analysis with Gemini. Passes 429 and 503 through; 503 with a message when no key is set |
| `POST /decisions`, `GET /decisions` | Append a reviewer decision; list decisions for a program and run |

Interactive docs are at http://127.0.0.1:8000/docs while the server runs.
