"""AST visitor that records where Python and Java semantics differ."""

import ast

from .models import RuleId, Site
from .rules import RULES
from .utils import MAX_INT32, ast_int


class MismatchVisitor(ast.NodeVisitor):
    """Walks a module's AST and collects mismatch sites."""

    def __init__(self, source: str) -> None:
        """Store the source text so snippets can be extracted for each site.

        Args:
            source: The Python source the AST was parsed from.
        """
        self.source = source
        self.sites: list[Site] = []

    def _add(self, rule_id: RuleId, node: ast.expr | ast.stmt) -> None:
        """Record a site for the node, taking its category and reason from the booklet.

        Args:
            rule_id: The rule that matched.
            node: The node that matched it.
        """
        rule = RULES[rule_id]
        snippet = ast.get_source_segment(self.source, node) or type(node).__name__
        self.sites.append(
            Site(
                rule=rule.id,
                category=rule.category,
                line=node.lineno,
                end_line=node.end_lineno or node.lineno,
                snippet=snippet.splitlines()[0][:60],
                reason=rule.reason,
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
                    self._add(RuleId.CONST_OVERFLOW, node)
            else:
                self._add(RuleId.INT_OVERFLOW, node)
        elif isinstance(op, ast.Div):
            self._add(RuleId.TRUE_DIVISION, node)
        elif isinstance(op, ast.FloorDiv):
            self._add(RuleId.FLOOR_DIVISION, node)
        elif isinstance(op, ast.Mod):
            if isinstance(left, (ast.Constant, ast.JoinedStr)) and isinstance(
                getattr(left, "value", None), str
            ):
                self._add(RuleId.PERCENT_FORMAT, node)
            else:
                self._add(RuleId.MODULO_SIGN, node)

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
            self._add(RuleId.LITERAL_OVERFLOW, node)
        elif type(node.value) is float:
            self._add(RuleId.FLOAT_PRECISION, node)

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
            self._add(RuleId.LINE_INPUT, node)
        elif attr == "split" and not node.args:
            self._add(RuleId.WHITESPACE_SPLIT, node)
        elif name == "int":
            self._add(RuleId.INT_PARSE, node)
        elif name == "float":
            self._add(RuleId.FLOAT_PRECISION, node)
        elif name == "sum":
            self._add(RuleId.SUM_OVERFLOW, node)
        elif name == "pow" and len(node.args) == 3:
            self._add(RuleId.MODULAR_POW, node)
        elif name == "round":
            self._add(RuleId.ROUNDING, node)
        elif name == "print":
            self._check_print(node)
        elif attr == "format":
            self._add(RuleId.STR_FORMAT, node)
        self.generic_visit(node)

    def _check_print(self, node: ast.Call) -> None:
        """Flag print calls whose output Java would not reproduce by default."""
        kw = {k.arg for k in node.keywords}
        if kw & {"sep", "end"}:
            self._add(RuleId.PRINT_SEP_END, node)
        elif any(isinstance(a, ast.Starred) for a in node.args):
            self._add(RuleId.PRINT_STARRED, node)
        elif len(node.args) > 1:
            self._add(RuleId.PRINT_ARGS, node)
        elif any(
            isinstance(a, (ast.Compare, ast.BoolOp))
            or (isinstance(a, ast.Constant) and type(a.value) is bool)
            for a in node.args
        ):
            self._add(RuleId.PRINT_BOOL, node)

    def visit_JoinedStr(self, node: ast.JoinedStr) -> None:
        """Flag f-strings that use format specs, such as `f"{x:.2f}"`."""
        if any(
            isinstance(v, ast.FormattedValue) and v.format_spec for v in node.values
        ):
            self._add(RuleId.FSTRING_SPEC, node)
        self.generic_visit(node)

    def visit_Subscript(self, node: ast.Subscript) -> None:
        """Flag slicing and negative indexing."""
        s = node.slice
        if isinstance(s, ast.Slice):
            self._add(RuleId.SLICING, node)
        elif isinstance(s, ast.UnaryOp) and isinstance(s.op, ast.USub):
            self._add(RuleId.NEGATIVE_INDEX, node)
        self.generic_visit(node)

    def visit_Try(self, node: ast.Try) -> None:
        """Flag try/except blocks, since exception types differ between the languages."""
        self._add(RuleId.EXCEPTIONS, node)
        self.generic_visit(node)
