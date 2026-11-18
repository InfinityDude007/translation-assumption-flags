import ast

from ..models import Category, Site
from ..utils import MAX_INT32, ast_int


class MismatchVisitor(ast.NodeVisitor):
    """Walks a module's AST and collects mismatch sites."""

    def __init__(self, source: str) -> None:
        """Store the source text so snippets can be extracted for each site.

        Args:
            source: The Python source the AST was parsed from.
        """
        self.source = source
        self.sites: list[Site] = []

    def _add(self, category: Category, node: ast.expr | ast.stmt, reason: str) -> None:
        """Record a site for the given node."""
        snippet = ast.get_source_segment(self.source, node) or type(node).__name__
        self.sites.append(
            Site(
                category,
                node.lineno,
                node.end_lineno or node.lineno,
                snippet.splitlines()[0][:60],
                reason,
            )
        )

    def _check_op(
        self,
        op: ast.operator,
        node: ast.expr | ast.stmt,
        left: ast.expr | None,
        right: ast.expr,
    ) -> None:
        """Flag arithmetic operators whose semantics differ between the languages.

        Args:
            op: The operator being applied.
            node: The node to report (the BinOp or AugAssign).
            left: Left operand, or None for augmented assignment.
            right: Right operand.
        """
        if isinstance(op, (ast.Mult, ast.Pow, ast.LShift)):
            lv, rv = (ast_int(left) if left else None), ast_int(right)
            if lv is not None and rv is not None:
                if isinstance(op, (ast.Pow, ast.LShift)) and rv > 64:
                    value = MAX_INT32 + 1
                elif isinstance(op, ast.Pow):
                    value = lv**rv
                elif isinstance(op, ast.LShift):
                    value = lv << rv
                else:
                    value = lv * rv
                if abs(value) > MAX_INT32:
                    self._add(
                        Category.NUMERIC,
                        node,
                        "Constant exceeds Java int range; needs long or BigInteger.",
                    )
            else:
                self._add(
                    Category.NUMERIC,
                    node,
                    "Python ints never overflow; a Java int/long result can wrap around.",
                )
        elif isinstance(op, ast.Div):
            self._add(
                Category.DIVISION,
                node,
                "Python / always gives a float; Java int / int truncates to an int.",
            )
        elif isinstance(op, ast.FloorDiv):
            self._add(
                Category.DIVISION,
                node,
                "Python // rounds toward negative infinity; Java / truncates toward zero "
                "(differs for negatives; Math.floorDiv matches).",
            )
        elif isinstance(op, ast.Mod):
            if isinstance(left, (ast.Constant, ast.JoinedStr)) and isinstance(
                getattr(left, "value", None), str
            ):
                self._add(
                    Category.OUTPUT,
                    node,
                    "%-formatting rules differ from Java String.format.",
                )
            else:
                self._add(
                    Category.DIVISION,
                    node,
                    "Python % takes the divisor's sign; Java % takes the dividend's "
                    "(differs for negatives; Math.floorMod matches).",
                )

    def visit_BinOp(self, node: ast.BinOp) -> None:
        """Check binary operations such as `a * b` or `a // b`."""
        self._check_op(node.op, node, node.left, node.right)
        self.generic_visit(node)

    def visit_AugAssign(self, node: ast.AugAssign) -> None:
        """Check augmented assignments such as `x *= y`."""
        self._check_op(node.op, node, None, node.value)
        self.generic_visit(node)

    def visit_Constant(self, node: ast.Constant) -> None:
        """Flag integer literals beyond Java int range and all float literals."""
        if type(node.value) is int and abs(node.value) > MAX_INT32:
            self._add(
                Category.NUMERIC,
                node,
                "Literal exceeds Java int range; needs long or BigInteger.",
            )
        elif type(node.value) is float:
            self._add(
                Category.NUMERIC,
                node,
                "Python float is 64-bit; Java float is 32-bit, so use double.",
            )

    def visit_Call(self, node: ast.Call) -> None:
        """Flag calls for input, number conversion, rounding, printing and formatting."""
        func = node.func
        name = func.id if isinstance(func, ast.Name) else None
        attr = func.attr if isinstance(func, ast.Attribute) else None

        reads_stdin = (
            isinstance(func, ast.Attribute)
            and func.attr in {"readline", "readlines", "read"}
            and isinstance(func.value, ast.Attribute)
            and func.value.attr == "stdin"
        )

        if name == "input" or reads_stdin:
            self._add(
                Category.INPUT,
                node,
                "Python reads whole lines; Java Scanner token reads (nextInt/next) "
                "can split or skip lines differently.",
            )
        elif attr == "split" and not node.args:
            self._add(
                Category.INPUT,
                node,
                "split() with no argument splits on any whitespace run and drops "
                'empties; Java String.split(" ") keeps empty strings.',
            )
        elif name == "int":
            self._add(
                Category.NUMERIC,
                node,
                "Python int() is unbounded; the translation must choose Java int, "
                "long or BigInteger for this value.",
            )
        elif name == "float":
            self._add(
                Category.NUMERIC,
                node,
                "Python float is 64-bit; Java float is 32-bit, so use double.",
            )
        elif name == "sum":
            self._add(
                Category.NUMERIC,
                node,
                "A Python sum never overflows; a Java int accumulator can.",
            )
        elif name == "pow" and len(node.args) == 3:
            self._add(
                Category.NUMERIC,
                node,
                "Three-argument pow is modular exponentiation; Java needs "
                "BigInteger.modPow or a manual loop.",
            )
        elif name == "round":
            self._add(
                Category.API,
                node,
                "Python round() rounds half to even; Java Math.round() rounds half up.",
            )
        elif name == "print":
            self._check_print(node)
        elif attr == "format":
            self._add(
                Category.OUTPUT,
                node,
                "The str.format mini-language differs from Java String.format.",
            )
        self.generic_visit(node)

    def _check_print(self, node: ast.Call) -> None:
        """Flag print calls whose output Java would not reproduce by default."""
        kw = {k.arg for k in node.keywords}
        if kw & {"sep", "end"}:
            self._add(
                Category.OUTPUT,
                node,
                "Custom sep/end must be reproduced exactly in Java.",
            )
        elif any(isinstance(a, ast.Starred) for a in node.args):
            self._add(
                Category.OUTPUT,
                node,
                "print(*xs) prints space-separated items; Java prints arrays/lists "
                "differently.",
            )
        elif len(node.args) > 1:
            self._add(
                Category.OUTPUT,
                node,
                "print(a, b) inserts spaces between arguments; Java concatenation doesn't.",
            )
        elif any(
            isinstance(a, (ast.Compare, ast.BoolOp))
            or (isinstance(a, ast.Constant) and type(a.value) is bool)
            for a in node.args
        ):
            self._add(
                Category.OUTPUT,
                node,
                "Python prints True/False; Java prints true/false.",
            )

    def visit_JoinedStr(self, node: ast.JoinedStr) -> None:
        """Flag f-strings that use format specs, such as `f"{x:.2f}"`."""
        if any(
            isinstance(v, ast.FormattedValue) and v.format_spec for v in node.values
        ):
            self._add(
                Category.OUTPUT,
                node,
                "f-string format specs differ from Java String.format.",
            )
        self.generic_visit(node)

    def visit_Subscript(self, node: ast.Subscript) -> None:
        """Flag slicing and negative indexing."""
        s = node.slice
        if isinstance(s, ast.Slice):
            self._add(
                Category.API,
                node,
                "Python slicing copies and clamps out-of-range bounds; Java needs "
                "subList/copyOfRange, which throw instead.",
            )
        elif isinstance(s, ast.UnaryOp) and isinstance(s.op, ast.USub):
            self._add(
                Category.API,
                node,
                "Negative indices count from the end in Python; Java throws.",
            )
        self.generic_visit(node)

    def visit_Try(self, node: ast.Try) -> None:
        """Flag try/except blocks, since exception types differ between the languages."""
        self._add(
            Category.ERRORS,
            node,
            "Python exception types (ValueError, IndexError, ...) map to different "
            "Java exceptions; the translation must pick what to catch.",
        )
        self.generic_visit(node)
