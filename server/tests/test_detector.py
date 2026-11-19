"""Tests for the rule-based mismatch detector."""

from server.detection import Category, detect


def cats(source: str) -> set[tuple[Category, int]]:
    """Run the detector and return its flags as (category, line) pairs.

    Args:
        source: Python source to analyse.

    Returns:
        The category and line of every site found.
    """
    return {(site.category, site.line) for site in detect(source)}


def test_product_of_variables_flags_overflow() -> None:
    """Multiplying two variables is flagged, since the Java result can overflow."""
    assert (Category.NUMERIC, 2) in cats("n = int(input())\nt = n * n\n")


def test_floor_division_and_modulo() -> None:
    """`//` and `%` are flagged, since both round differently for negatives in Java."""
    found = cats("a = -7 // 2\nb = -7 % 2\n")
    assert (Category.DIVISION, 1) in found and (Category.DIVISION, 2) in found


def test_input_parsing() -> None:
    """Reading and splitting input is flagged as an input-parsing site."""
    assert (Category.INPUT, 1) in cats("a, b = map(int, input().split())\n")


def test_int_parsing_flags_numeric() -> None:
    """`int()` is flagged, since the translation must pick a Java integer type."""
    assert (Category.NUMERIC, 1) in cats("k = int(input())\n")


def test_printing_a_comparison() -> None:
    """Printing a boolean is flagged, since Java prints true/false in lower case."""
    assert (Category.OUTPUT, 1) in cats("print(x > 3)\n")


def test_negative_index() -> None:
    """Negative indexing is flagged, since Java has no equivalent."""
    assert (Category.API, 1) in cats("y = xs[-1]\n")


def test_large_constant_flagged_small_not() -> None:
    """Constant expressions are flagged only when they exceed Java int range."""
    assert (Category.NUMERIC, 1) in cats("M = 10**18\n")
    assert not any(site.category == Category.NUMERIC for site in detect("k = 2 * 3\n"))


def test_plain_code_has_no_flags() -> None:
    """Code with no mismatch constructs produces no sites."""
    assert detect("x = 1\ny = x + 2\n") == []


def test_one_flag_per_category_per_line() -> None:
    """Several matches on one line collapse into a single site per category."""
    sites = detect("a, b = map(int, input().split())\n")
    assert len([site for site in sites if site.category == Category.INPUT]) == 1
