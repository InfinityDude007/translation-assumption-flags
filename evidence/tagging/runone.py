"""Run a sample's dataset tests against a Java file."""

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
TIMEOUT = 5


def normalise(text: str) -> str:
    """Strip trailing spaces on each line and blank lines at either end.

    Args:
        text: Program output or expected output.

    Returns:
        The text in a form that ignores insignificant whitespace.
    """

    return "\n".join(line.rstrip() for line in text.strip().splitlines())


def expected_name(test_in: str) -> str:
    """Return the expected-output file name for a test input file.

    Args:
        test_in: An AVATAR `<name>_<n>.in` or CodeNet `<name>_in.txt` file name.

    Returns:
        The matching `.out` or `_out.txt` file name.
    """

    if test_in.endswith(".in"):
        return test_in[:-3] + ".out"

    return test_in.replace("_in.txt", "_out.txt")


def run_test(class_dir: str, cls: str, test_in: Path, test_out: Path) -> str | None:
    """Run one test and return why it failed, or None if it passed.

    Args:
        class_dir: Folder holding the compiled class.
        cls: Name of the public class.
        test_in: The test's input file.
        test_out: The test's expected output file.

    Returns:
        None on a pass; otherwise the first stderr line, "TIMEOUT" or "wrong output".
    """

    try:
        run = subprocess.run(
            ["java", "-Xss64m", "-cp", class_dir, cls],
            input=test_in.read_bytes(),
            capture_output=True,
            timeout=TIMEOUT,
            check=False,
        )

    except subprocess.TimeoutExpired:
        return "TIMEOUT"

    got = normalise(run.stdout.decode(errors="replace"))
    if run.returncode == 0 and got == normalise(test_out.read_text(errors="replace")):
        return None
    stderr = run.stderr.decode(errors="replace").strip()

    return stderr.splitlines()[0] if stderr else "wrong output"


def main() -> None:
    """Compile the Java file, run every test of the sample and print the pass count.

    Usage: python3 -I runone.py <sample_id> <file.java>. Needs a JDK and the raw
    tests from `uv run get-dataset`.
    """

    if len(sys.argv) != 3:
        sys.exit("usage: python3 -I runone.py <sample_id> <file.java>")

    sample_id, java_file = sys.argv[1], Path(sys.argv[2]).resolve()
    meta = json.loads((REPO / "data" / "samples" / sample_id / "meta.json").read_text())
    tests_dir = (
        REPO / "data" / "raw" / "dataset" / meta["dataset"] / "Python" / "TestCases"
    )

    java = java_file.read_text()
    match = re.search(r"public\s+(?:final\s+)?class\s+(\w+)", java)

    if match is None:
        sys.exit("no public class found")
    cls = match.group(1)

    with tempfile.TemporaryDirectory() as class_dir:
        (Path(class_dir) / f"{cls}.java").write_text(java)
        compiled = subprocess.run(
            ["javac", f"{cls}.java"],
            cwd=class_dir,
            capture_output=True,
            text=True,
            check=False,
        )

        if compiled.returncode:
            sys.exit("COMPILE ERROR\n" + compiled.stderr)
        inputs = [t for t in meta["tests"] if t.endswith((".in", "_in.txt"))]

        failures = [
            (name, reason)
            for name in inputs
            if (
                reason := run_test(
                    class_dir, cls, tests_dir / name, tests_dir / expected_name(name)
                )
            )
        ]

    print(f"{sample_id}: {len(inputs) - len(failures)}/{len(inputs)} tests pass")

    for name, reason in failures[:3]:
        print("  FAIL", name, reason)


if __name__ == "__main__":
    main()
