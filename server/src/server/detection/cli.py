"""Print the mismatch sites for a Python file as JSON."""

import json
import sys

from .detector import detect


def main() -> None:
    """Read the file named on the command line and print its sites."""
    with open(sys.argv[1], encoding="utf-8") as file:
        print(
            json.dumps(
                [site.model_dump(mode="json") for site in detect(file.read())], indent=2
            )
        )


if __name__ == "__main__":
    main()
