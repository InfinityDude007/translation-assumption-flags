# data

The dataset of sample programs from Pan et. al.'s 2024 study, their hand-checked ground truth, and every model output used in the evaluation.
> See the [root README](../README.md) for the project overview.

**README prose word count: 581** (excluding code, commands, file paths and the table of contents)

## Table of Contents
1. [Contents](#contents)
2. [Samples](#samples)
3. [How the tags were made and checked](#how-the-tags-were-made-and-checked)
4. [Runs and baselines](#runs-and-baselines)
5. [Rebuilding the data](#rebuilding-the-data)
6. [Licence](#licence)


## Contents

| Path | What it holds | Tracked |
|---|---|---|
| `samples/<id>/` | One program each: `source.py`, `translation.java` (GPT-4's translation) and `meta.json` | Yes |
| `runs/<run>/` | One Gemini run: `run.json` (model, prompt version, start time), one `<id>.json` per program and `score.json` | Yes |
| `baselines/<name>/` | One token-probability baseline: `baseline.json`, one `<id>.json` per program and `score.json` | Yes |
| `NOTICE` | CC BY 4.0 attribution for the samples | Yes |
| `raw/` | Pan et al.'s full dataset and tests, from `uv run get-dataset` (about 900 MB) | No |
| `decisions.jsonl` | Reviewer decisions, appended by the interface's buttons | No |

## Samples

35 programs from Pan et al. (2024), AVATAR and CodeNet, picked by `uv run make-samples` with seed 2026: 25 translations Pan labelled as buggy (balanced across bug categories, excluding compile errors, which the compiler already reports) and 10 unlabelled ones as controls.

Each `meta.json` holds:

- `group`: `buggy` or `control`; `pan_labels`: Pan's file-level labels, unchanged; `tests`: test file names in `raw/`.
- `bug_lines`: the `source` and `translation` lines of a bug the dataset's tests expose.
- `latent`: lines where the translation behaves differently on valid input but no test catches it.
- `notes`: the fix, the test counts before and after, and any disagreement with Pan.

The notes contain the answer, so they are never sent to Gemini and never shown on the review pages.

## How the tags were made and checked

Pan et al. label files, not lines, so every buggy translation was tagged by line. Claude Code compiled and ran each translation, proposed the lines and a minimal fix, and the I reviewed, asked for rechecks and adopted the tags ([`fa74889`](https://github.com/InfinityDude007/translation-assumption-flags/commit/fa74889)). A tag counts only if fixing just those lines makes the failing tests pass. The fixes are in [`evidence/tagging/`](../evidence/tagging/).

What happened to bugs that Pan's labels do not describe:

- **Extra bugs Pan missed** (ABC123_C, ABC143_D, codeforces_651_A): added to `bug_lines`, because the tests need them fixed. They are scored like any bug.
- **A different category** (AGC046_B, codeforces_579_A, codeforces_665_A, s259116349): the fix Pan's label implies fails and ours passes. `pan_labels` is kept and our category is in `notes`. Scoring is by line, so this does not change the scores.
- **No translation bug** (ABC126_D, ARC086_B, codeforces_306_A, codeforces_459_A): Java and Python print the same; the tests accept only one of several valid answers. `bug_lines` is empty and they are scored like controls.
- **Latent bugs** (8, including 3 of the 10 controls): tagged in `latent`. Each was confirmed by fuzzing with valid inputs: differences before the fix, none after. A flag on one counts as a catch.

## Runs and baselines

Each `runs/<run>/<id>.json` holds the checked flags, the dropped sites with their reasons, Gemini's raw answer, the model, the prompt version and the time taken. A run name never mixes models or prompt versions.

| Run | Model | Prompt |
|---|---|---|
| `hydrogen-v1`, `hydrogen-v1b` | `gemini-4-hydrogen` | v1 (v1b is a repeat) |
| `hydrogen-v2`, `hydrogen-v2b` | `gemini-4-hydrogen` | v2 (v2b is a repeat) |
| `flash38-v1`, `flash38-v2` | `gemini-3.8-flash` | v1, v2 |

`baselines/qwen-1.5b` and `qwen-3b` hold every Java token's probability under Qwen2.5-Coder-1.5B/3B-Instruct. Each `score.json` is a snapshot from `uv run score` or `uv run score-baseline`; the API recomputes scores on request.

## Rebuilding the data

Everything above except `raw/` is committed, so nothing needs rebuilding to inspect it. To regenerate it, from `server/`:

```bash
uv run get-dataset
uv run make-samples
uv run evaluate --name hydrogen-v2 --model gemini-4-hydrogen
uv run score hydrogen-v2
uv run baseline --name qwen-1.5b
uv run score-baseline qwen-1.5b
```

- `make-samples` never overwrites a sample, so the tags stay. They were added by hand, as described above. 
- `evaluate` needs a Gemini key and resumes if stopped.
- `baseline` downloads the model on first use. Every option is in the [server README](../server/README.md#developer-tooling--running-features).

## Licence

The samples, and the translations inside the runs, come from Pan, R. et al. (2024) *Lost in Translation*, ICSE 2024, [doi:10.5281/zenodo.10447705](https://doi.org/10.5281/zenodo.10447705), CC BY 4.0.

They were selected, renamed and given added fields; see `NOTICE`.
