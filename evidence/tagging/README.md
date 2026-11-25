# evidence/tagging

Evidence for the line-level bug tags in `data/samples/*/meta.json`.
>See [`data/README.md`](../../data/README.md) for how the tags are used.

**README prose word count: 273** (excluding code, commands, file paths and the table of contents)

## Table of Contents
1. [Files](#files)
2. [Rerunning a check](#rerunning-a-check)
3. [What is not here](#what-is-not-here)

## Files

| Path | What it is |
|---|---|
| `bug_lines_review.md` | The tagging review, sample by sample: tagged lines, test counts before and after the fix, and agreement with Pan et al. **Written by Claude Code** as output for my review |
| `runone.py` | Runs one sample's dataset tests against any Java file and prints the pass count |
| `fixes/<id>/<Class>.java` | The fixed translation behind each "after" count, for the 21 samples with a translation bug |

Each fix changes the tagged lines, plus lines needed to compile in some samples. ABC150_C is the exception: it was fixed at line 23, as its notes explain. The fixes are modified copies of Pan et al.'s GPT-4 translations (CC BY 4.0).

## Rerunning a check

Needs a JDK (`javac` and `java`) and the dataset's tests, which are not committed. From `server/`:

1. Download the dataset
   - From `server/`:
```bash
uv run get-dataset
```
2. Run the check on a translation
   - From project root:
```bash
python3 -I evidence/tagging/runone.py avatar-codeforces_387_A data/samples/avatar-codeforces_387_A/translation.java
```
3. Run the check on a fixed translation
   - From project root:
```bash
python3 -I evidence/tagging/runone.py avatar-codeforces_387_A evidence/tagging/fixes/avatar-codeforces_387_A/codeforces_387_A.java
```

- Step 2 fails some tests (30 of 47 pass).
- Step 3 passes all 47.
- codeforces_30_A passes 50 of 68 after the fix, because the Python source fails the same 18.

## What is not here

The tagging was run outside this repository, so the test harness, the fuzzing and checker scripts for the latent bugs and no-bug samples, and the compiled Java are not part of the submission. The latent-bug and no-bug results are described in the review file instead of being reproducible from here.
