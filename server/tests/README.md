# server/tests

The backend tests. None of them call Gemini or download a model. Gemini is replaced by fake HTTP responses or a fake client, and the baseline by a fake scorer.

**README prose word count: 261** (excluding code, commands, file paths, the table of contents and the generated coverage report)

## Table of Contents
1. [Running Tests](#running-tests)
2. [What each file covers](#what-each-file-covers)
3. [Coverage Report](#coverage-report)


## Running Tests

From `server/`:

```bash
uv run tests
uv run tests tests/test_explainer.py
uv run check
```

`uv run tests` runs pytest with coverage and passes any extra arguments through. `uv run check` adds formatting, lint, mypy and Pyright.

## What each file covers

| File | Covers |
|---|---|
| `test_detector.py` | Each detector rule fires on its construct, and only there |
| `test_rules.py` | Every rule id has a booklet entry that cites a source, and sites take their category and reason from their rule |
| `test_gemini.py` | The key setting, the request Gemini receives (key header, system prompt, schema), early stops, and 503 retries without retrying 429s |
| `test_explainer.py` | The prompt, and the checks on Gemini's answer: unknown and repeated sites, Java lines out of range, dropped sites with a reason, fixes kept only for "behaves differently" |
| `test_evaluation.py` | Run archiving, resuming, the model and prompt guard, and scoring: catches, latent catches, false alarms, and "can't tell" counted as surfaced |
| `test_baseline.py` | Token-to-line mapping, the line-budget threshold and baseline scoring |
| `test_api.py` | Every route, that review responses hide the tags and Gemini's reasoning, error codes passed through, unknown or unsafe sample ids answered with 404, and the decision log |
| `test_samples.py` | Sample selection: balance across bug categories, controls, and never overwriting a sample |
| `test_sample_data.py` | Every committed `meta.json` is valid, every tagged line exists in its file, and controls have no bug lines |

Some tests were checked by breaking the code on purpose: for example, letting Gemini's reasoning reach the API, or keeping a fix for every verdict, makes them fail.

## Coverage Report

![Coverage](coverage.svg)

<!-- coverage:start -->
**Total: 78%** of 1169 statements (261 missed), from the pytest suite on commit `9f91868`, 2026-11-25. Updated by the Coverage workflow.

<details>
<summary>Coverage by file</summary>

| File | Statements | Missed | Covered |
|---|---:|---:|---:|
| `__init__.py` | 0 | 0 | 100% |
| `api/__init__.py` | 2 | 0 | 100% |
| `api/app.py` | 97 | 3 | 97% |
| `api/decisions.py` | 14 | 0 | 100% |
| `api/models.py` | 67 | 0 | 100% |
| `api/serve.py` | 8 | 8 | 0% |
| `baseline/__init__.py` | 5 | 0 | 100% |
| `baseline/archive.py` | 40 | 0 | 100% |
| `baseline/cli.py` | 32 | 32 | 0% |
| `baseline/lines.py` | 18 | 0 | 100% |
| `baseline/models.py` | 42 | 0 | 100% |
| `baseline/scorer.py` | 38 | 38 | 0% |
| `baseline/scoring.py` | 37 | 3 | 92% |
| `dataset/__init__.py` | 3 | 0 | 100% |
| `dataset/download.py` | 27 | 27 | 0% |
| `dataset/models.py` | 34 | 0 | 100% |
| `dataset/samples.py` | 81 | 14 | 83% |
| `dataset/types.py` | 5 | 0 | 100% |
| `dataset/utils.py` | 25 | 25 | 0% |
| `detection/__init__.py` | 4 | 0 | 100% |
| `detection/cli.py` | 8 | 8 | 0% |
| `detection/detector.py` | 17 | 0 | 100% |
| `detection/models/__init__.py` | 3 | 0 | 100% |
| `detection/models/enums.py` | 32 | 0 | 100% |
| `detection/models/models.py` | 20 | 0 | 100% |
| `detection/rules/__init__.py` | 2 | 0 | 100% |
| `detection/rules/rules.py` | 5 | 0 | 100% |
| `detection/rules/sources.py` | 14 | 0 | 100% |
| `detection/utils.py` | 7 | 0 | 100% |
| `detection/visitor.py` | 93 | 20 | 78% |
| `dev.py` | 31 | 31 | 0% |
| `evaluation/__init__.py` | 4 | 0 | 100% |
| `evaluation/archive.py` | 43 | 0 | 100% |
| `evaluation/cli.py` | 32 | 32 | 0% |
| `evaluation/models.py` | 41 | 0 | 100% |
| `evaluation/scoring.py` | 32 | 0 | 100% |
| `explanation/__init__.py` | 4 | 0 | 100% |
| `explanation/cli.py` | 15 | 15 | 0% |
| `explanation/explainer.py` | 30 | 0 | 100% |
| `explanation/models.py` | 32 | 0 | 100% |
| `explanation/prompts.py` | 12 | 0 | 100% |
| `gemini.py` | 34 | 1 | 97% |
| `settings/__init__.py` | 6 | 0 | 100% |
| `settings/api.py` | 13 | 1 | 92% |
| `settings/base.py` | 8 | 0 | 100% |
| `settings/baseline.py` | 12 | 1 | 92% |
| `settings/dataset.py` | 13 | 0 | 100% |
| `settings/evaluation.py` | 11 | 1 | 91% |
| `settings/gemini.py` | 16 | 1 | 94% |

</details>
<!-- coverage:end -->
