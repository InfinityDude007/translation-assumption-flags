"""Developer commands exposed through `uv run`."""

import subprocess
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[2]
"""The server project folder (the one containing pyproject.toml)."""

CHECKS: list[tuple[str, list[str]]] = [
    ("ruff format", ["ruff", "format", "--check", "."]),
    ("ruff lint", ["ruff", "check", "."]),
    ("mypy", ["mypy"]),
    ("pytest", ["pytest", "-q"]),
]
"""Each check's display name and the module command that runs it."""


def _run(command: list[str]) -> int:
    """Run a tool as `python -m <command>` from the project folder.

    Args:
        command: The module name followed by its arguments.

    Returns:
        The tool's exit code.
    """
    return subprocess.run(
        [sys.executable, "-m", *command], cwd=PROJECT_DIR, check=False
    ).returncode


def run_tests() -> None:
    """Run the test suite, passing through any extra pytest arguments."""
    print(flush=True)
    code = _run(["pytest", *sys.argv[1:]])
    print()
    sys.exit(code)


def fix() -> None:
    """Apply ruff's formatting and safe lint fixes."""
    print(flush=True)
    _run(["ruff", "format", "."])
    code = _run(["ruff", "check", "--fix", "."])
    print()
    sys.exit(code)


def check() -> None:
    """Run formatting, lint, type and test checks, then report which failed."""
    failed = []
    for name, command in CHECKS:
        print(f"\n{f' {name} '.center(50, '=')}", flush=True)
        if _run(command) != 0:
            failed.append(name)
    print()
    if failed:
        print(f"Failed: {', '.join(failed)}")
        sys.exit(1)
    print("All checks passed.\n")
