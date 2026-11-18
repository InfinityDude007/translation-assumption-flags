from dataclasses import asdict, dataclass
from enum import StrEnum
from typing import Any


class Category(StrEnum):
    """Mismatch categories, mapped onto Pan et al. (2024)'s bug taxonomy."""

    NUMERIC = "numeric"  # C1: incorrect data type
    DIVISION = "division"  # A4: incorrect use of operator
    INPUT = "input"  # C2: incorrect input parsing
    OUTPUT = "output"  # C3: output formatting
    API = "api"  # A3/B6: API behaviour mismatch
    ERRORS = "errors"  # exception handling


@dataclass(frozen=True)
class Site:
    """A place in the source where the translation had to make an assumption.

    Attributes:
        category: The kind of mismatch.
        line: First source line of the construct (1-based).
        end_line: Last source line of the construct.
        construct: Source snippet, truncated to 60 characters.
        reason: How Python and Java differ at this construct.
    """

    category: Category
    line: int
    end_line: int
    construct: str
    reason: str

    def to_dict(self) -> dict[str, Any]:
        """Return the site as a JSON-serialisable dict."""
        return asdict(self)
