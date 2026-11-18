import ast


def ast_int(node: ast.AST) -> int | None:
    """Return the value if the node is an integer literal, else None."""
    if isinstance(node, ast.Constant) and type(node.value) is int:
        return node.value
    return None
