"""Rule-based detection of Python to Java mismatch sites."""

import ast

from .models import Category, Site
from .visitor import MismatchVisitor


def detect(source: str) -> list[Site]:
    """Find mismatch sites in a Python program.

    Args:
        source: Python 3 source code.

    Returns:
        Sites in line order, at most one per (category, line).

    Raises:
        ValueError: If the source is not valid Python 3.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        raise ValueError(
            f"Source is not valid Python 3 (line {e.lineno}): {e.msg}"
        ) from e
    visitor = MismatchVisitor(source)
    visitor.visit(tree)
    seen: set[tuple[Category, int]] = set()
    sites: list[Site] = []
    for site in sorted(visitor.sites, key=lambda s: (s.line, s.category)):
        if (site.category, site.line) not in seen:
            seen.add((site.category, site.line))
            sites.append(site)
    return sites
