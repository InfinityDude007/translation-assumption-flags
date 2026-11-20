"""Print the explainer's flags for a Python file and its Java translation as JSON."""

import sys
from pathlib import Path

from ..claude import ClaudeError
from .explainer import explain


def main() -> None:
    """Explain the two files named on the command line and print the result.

    Usage: explain <source.py> <translation.java>
    """
    if len(sys.argv) != 3:
        sys.exit("usage: explain <source.py> <translation.java>")

    source, translation = (
        Path(arg).read_text(encoding="utf-8") for arg in sys.argv[1:]
    )

    try:
        result = explain(source, translation)
    except (ClaudeError, ValueError) as error:
        sys.exit(f"explain: {error}")

    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
