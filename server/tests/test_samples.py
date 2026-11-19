"""Tests for sample selection."""

import json
import random
from pathlib import Path

from server.dataset import (
    Label,
    Program,
    find_tests,
    parse_label_rows,
    select_buggy,
    select_controls,
    write_sample,
)


def row(dataset: str, filename: str, bug_type: str, impact: str) -> tuple[object, ...]:
    """Build a label sheet row for a Python-to-Java translation."""
    return (dataset, "py", "java", filename, bug_type, None, None, impact)


def program(name: str) -> Program:
    """Build an AVATAR program with the given name."""
    return Program(dataset="avatar", name=name)


def label(code: str, impact: str = "Runtime Error") -> Label:
    """Build a label with the given bug code."""
    return Label(code=code, bug_type=f"{code}: test", impact=impact)


def test_parse_keeps_only_python_to_java_avatar_and_codenet() -> None:
    """Rows for other language pairs or datasets are dropped."""
    labels = parse_label_rows(
        [
            row("Avatar", "a.java", "C1: Incorrect data type", "Runtime Error"),
            row("CodeNet", "s1.java", "C2: Incorrect input parsing", "Wrong Output"),
            ("Avatar", "py", "go", "a.go", "C1: x", None, None, "Runtime Error"),
            row("Eval+", "e.java", "C1: x", "Runtime Error"),
        ]
    )
    assert set(labels) == {
        Program(dataset="avatar", name="a"),
        Program(dataset="codenet", name="s1"),
    }
    assert labels[Program(dataset="avatar", name="a")][0].code == "C1"


def test_buggy_skips_compile_errors_and_non_semantic_codes() -> None:
    """Only compiling translations with a semantic bug code are picked."""
    labels = {
        program("ok"): [label("C1")],
        program("compile"): [label("C1", impact="Compilation Error")],
        program("import"): [label("B1")],
    }
    assert select_buggy(labels, 10, random.Random(0)) == [program("ok")]


def test_buggy_spreads_picks_across_codes() -> None:
    """Round-robin picking takes one of each code before a second of any."""
    labels = {program(f"c1_{i}"): [label("C1")] for i in range(5)}
    labels |= {program("a4"): [label("A4")], program("c3"): [label("C3")]}
    picks = select_buggy(labels, 3, random.Random(0))
    assert {p.name for p in picks} >= {"a4", "c3"}


def test_selection_is_reproducible() -> None:
    """The same seed gives the same picks."""
    labels = {program(f"p{i}"): [label("C2")] for i in range(20)}
    first = select_buggy(labels, 5, random.Random(1))
    assert first == select_buggy(labels, 5, random.Random(1))


def test_controls_exclude_labelled_programs() -> None:
    """Control samples come only from programs with no label."""
    programs = [program(f"p{i}") for i in range(10)]
    labels = {program(f"p{i}"): [label("C1")] for i in range(5)}
    controls = select_controls(programs, labels, 5, random.Random(0))
    assert set(controls) == set(programs[5:])


def make_raw(raw: Path) -> Program:
    """Create a minimal raw data folder holding one AVATAR program."""
    code = raw / "dataset" / "avatar" / "Python" / "Code"
    tests = code.parent / "TestCases"
    java = raw / "Artifacts" / "RQ1-Translations" / "GPT-4" / "avatar" / "Python"
    for folder in (code, tests, java / "Java"):
        folder.mkdir(parents=True)
    (code / "prog_A.py").write_text("print(1)\n")
    (java / "Java" / "prog_A.java").write_text("class A {}\n")
    for name in ("prog_A_0.in", "prog_A_0.out", "prog_AB_0.in"):
        (tests / name).write_text("1\n")
    return program("prog_A")


def test_find_tests_matches_only_the_programs_files(tmp_path: Path) -> None:
    """Tests of a program whose name starts the same are not included."""
    prog = make_raw(tmp_path)
    assert [p.name for p in find_tests(tmp_path, prog)] == [
        "prog_A_0.in",
        "prog_A_0.out",
    ]


def test_write_sample_never_overwrites(tmp_path: Path) -> None:
    """An existing sample folder, with any hand-tagging, is left untouched."""
    prog = make_raw(tmp_path / "raw")
    samples = tmp_path / "samples"
    assert write_sample(prog, "buggy", [label("C1")], tmp_path / "raw", samples)

    meta_path = samples / prog.id / "meta.json"
    meta = json.loads(meta_path.read_text())
    assert meta["tests"] == ["prog_A_0.in", "prog_A_0.out"]
    meta["bug_lines"]["source"] = [1]
    meta_path.write_text(json.dumps(meta))

    assert not write_sample(prog, "buggy", [], tmp_path / "raw", samples)
    assert json.loads(meta_path.read_text())["bug_lines"]["source"] == [1]
