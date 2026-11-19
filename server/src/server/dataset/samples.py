"""Select buggy and control samples from Pan et al.'s data into data/samples."""

import random
import re
import shutil
from collections import defaultdict
from collections.abc import Iterable
from itertools import zip_longest
from pathlib import Path

from openpyxl import load_workbook

from ..settings import get_dataset_settings
from .models import Label, Program, SampleMeta
from .types import Dataset, Group

SEMANTIC_CODES = ("A3", "A4", "B6", "C1", "C2", "C3")
"""Pan et al. bug codes for language-semantics bugs that the detector targets."""

BUGGY_COUNT = 25
CONTROL_COUNT = 10
SEED = 2026

LABELS_FILE = Path("Artifacts/RQ2-Manual Labeling/manual labeling.xlsx")
"""Pan et al.'s label sheet, relative to the raw data folder."""

DATASETS: dict[str, Dataset] = {"Avatar": "avatar", "CodeNet": "codenet"}
"""Dataset names in the label sheet, mapped to their folder names."""


def parse_label_rows(rows: Iterable[tuple[object, ...]]) -> dict[Program, list[Label]]:
    """Collect the Python-to-Java labels for AVATAR and CodeNet programs.

    Args:
        rows: Sheet rows without the header: dataset, source language, target
            language, file name, bug type, two comment columns, impact.

    Returns:
        Each labelled program with its labels, in sheet order.
    """
    labels: dict[Program, list[Label]] = defaultdict(list)
    for row in rows:
        dataset, source, target, filename, bug_type, _, _, impact = row[:8]
        if source != "py" or target != "java" or dataset not in DATASETS:
            continue
        program = Program(dataset=DATASETS[str(dataset)], name=Path(str(filename)).stem)
        labels[program].append(
            Label(
                code=str(bug_type).split(":")[0],
                bug_type=str(bug_type),
                impact=str(impact),
            )
        )
    return dict(labels)


def read_labels(path: Path) -> dict[Program, list[Label]]:
    """Read the Python-to-Java labels from Pan et al.'s sheet.

    Args:
        path: The label sheet.

    Returns:
        Each labelled program with its labels.
    """
    sheet = load_workbook(path, read_only=True)["manual labeling"]
    return parse_label_rows(sheet.iter_rows(min_row=2, values_only=True))


def select_buggy(
    labels: dict[Program, list[Label]], count: int, rng: random.Random
) -> list[Program]:
    """Pick programs with a semantic bug, spread evenly across bug codes.

    Programs whose translation fails to compile are skipped, since the compiler
    already reports those. Picks go round-robin over the codes so rare codes
    are not crowded out by C1.

    Args:
        labels: Labelled programs from the sheet.
        count: How many programs to pick.
        rng: Random source, seeded for reproducibility.

    Returns:
        The picked programs.
    """
    by_code: dict[str, list[Program]] = defaultdict(list)
    for program, program_labels in sorted(labels.items(), key=lambda kv: kv[0].id):
        if any(label.impact == "Compilation Error" for label in program_labels):
            continue
        codes = [label.code for label in program_labels if label.code in SEMANTIC_CODES]
        if codes:
            by_code[codes[0]].append(program)
    for programs in by_code.values():
        rng.shuffle(programs)
    rounds = zip_longest(*(by_code[code] for code in sorted(by_code)))
    return [program for picks in rounds for program in picks if program][:count]


def select_controls(
    programs: Iterable[Program],
    labels: dict[Program, list[Label]],
    count: int,
    rng: random.Random,
) -> list[Program]:
    """Pick programs whose translation has no bug label.

    Args:
        programs: Every program with a translation.
        labels: Labelled programs from the sheet.
        count: How many programs to pick.
        rng: Random source, seeded for reproducibility.

    Returns:
        The picked programs.
    """
    unlabelled = sorted((p for p in programs if p not in labels), key=lambda p: p.id)
    return rng.sample(unlabelled, count)


def python_dir(raw_dir: Path, dataset: Dataset) -> Path:
    """Return the folder holding a dataset's Python code and tests."""
    return raw_dir / "dataset" / dataset / "Python"


def translation_dir(raw_dir: Path, dataset: Dataset) -> Path:
    """Return the folder holding a dataset's GPT-4 Java translations."""
    return (
        raw_dir
        / "Artifacts"
        / "RQ1-Translations"
        / "GPT-4"
        / dataset
        / "Python"
        / "Java"
    )


def list_programs(raw_dir: Path) -> list[Program]:
    """Return every program that has a GPT-4 translation."""
    return [
        Program(dataset=dataset, name=path.stem)
        for dataset in DATASETS.values()
        for path in sorted(translation_dir(raw_dir, dataset).glob("*.java"))
    ]


def find_tests(raw_dir: Path, program: Program) -> list[Path]:
    """Return a program's test input and output files.

    AVATAR names them `<name>_<n>.in/.out`; CodeNet uses `<name>_in.txt/_out.txt`.

    Args:
        raw_dir: The raw data folder.
        program: The program whose tests to find.

    Returns:
        The test files, sorted by name.
    """
    folder = python_dir(raw_dir, program.dataset) / "TestCases"
    pattern = re.compile(rf"{re.escape(program.name)}_(\d+\.(in|out)|(in|out)\.txt)")
    return sorted(p for p in folder.iterdir() if pattern.fullmatch(p.name))


def write_sample(
    program: Program,
    group: Group,
    labels: list[Label],
    raw_dir: Path,
    samples_dir: Path,
) -> bool:
    """Copy a program and its translation into a sample folder with a meta.json.

    Tests are listed in meta.json but not copied, since some programs have tens
    of megabytes of them; they stay in the raw data folder. Existing folders are
    left alone, so hand-tagged bug lines are never lost.

    Args:
        program: The program to copy.
        group: Whether it is a buggy or control sample.
        labels: Pan et al.'s labels for it.
        raw_dir: The raw data folder.
        samples_dir: The samples folder.

    Returns:
        True if the sample was written, False if it already existed.
    """
    folder = samples_dir / program.id
    if folder.exists():
        return False
    folder.mkdir(parents=True)
    code = python_dir(raw_dir, program.dataset) / "Code" / f"{program.name}.py"
    java = translation_dir(raw_dir, program.dataset) / f"{program.name}.java"
    shutil.copy(code, folder / "source.py")
    shutil.copy(java, folder / "translation.java")
    meta = SampleMeta(
        id=program.id,
        dataset=program.dataset,
        program=program.name,
        group=group,
        pan_labels=labels,
        tests=[test.name for test in find_tests(raw_dir, program)],
    )
    (folder / "meta.json").write_text(meta.model_dump_json(indent=2) + "\n")
    return True


def main() -> None:
    """Select the samples and write any that do not exist yet."""
    settings = get_dataset_settings()
    raw_dir, samples_dir = settings.raw_dir, settings.samples_dir
    if not (raw_dir / LABELS_FILE).exists():
        raise SystemExit(f"No dataset in {raw_dir}; run `uv run get-dataset` first")

    labels = read_labels(raw_dir / LABELS_FILE)
    rng = random.Random(SEED)
    buggy: list[tuple[Program, Group]] = [
        (p, "buggy") for p in select_buggy(labels, BUGGY_COUNT, rng)
    ]
    controls: list[tuple[Program, Group]] = [
        (p, "control")
        for p in select_controls(list_programs(raw_dir), labels, CONTROL_COUNT, rng)
    ]
    picks = buggy + controls

    written = sum(
        write_sample(program, group, labels.get(program, []), raw_dir, samples_dir)
        for program, group in picks
    )
    print(f"{len(picks)} samples selected, {written} new, in {samples_dir}")
