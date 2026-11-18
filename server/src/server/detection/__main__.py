"""Print the mismatch sites for a Python file as JSON."""

import json
import sys

from .detector import detect


def main() -> None:
    """Read the file named on cmd and print its sites."""
    with open(sys.argv[1], encoding="utf-8") as f:
        print(json.dumps([s.to_dict() for s in detect(f.read())], indent=2))


if __name__ == "__main__":
    main()
