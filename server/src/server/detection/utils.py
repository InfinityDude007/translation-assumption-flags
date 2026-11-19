"""Helpers for reading Python ASTs against Java's integer limits."""

import ast

MAX_INT32 = 2**31 - 1
"""Largest value a signed 32-bit Java int can hold."""


def ast_int(node: ast.AST) -> int | None:
    """Return the value if the node is an integer literal, else None."""
    if isinstance(node, ast.Constant) and type(node.value) is int:
        return node.value
    return None
