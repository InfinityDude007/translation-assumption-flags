"""Rule booklet: each mismatch rule with its reason and documentation sources."""

from ..models import Category, Rule, RuleId, Source
from .sources import (
    API,
    JAVA_FORMATTER,
    JLS,
    JLS_DIVISION,
    JLS_FLOAT,
    JLS_INT_OPS,
    JLS_INT_RANGE,
    PY,
    PY_ARITHMETIC,
    PY_FORMAT_SPEC,
    PY_NUMERIC,
    PY_PRINT,
    PY_SEQUENCES,
)

_RULES = (
    Rule(
        id=RuleId.CONST_OVERFLOW,
        category=Category.NUMERIC,
        reason="This constant is outside Java's int range (-2^31 to 2^31-1), "
        "so the translation needs long or BigInteger.",
        sources=(JLS_INT_RANGE,),
    ),
    Rule(
        id=RuleId.LITERAL_OVERFLOW,
        category=Category.NUMERIC,
        reason="This literal is outside Java's int range; without an L suffix it "
        "is a compile error, and beyond long range it needs BigInteger.",
        sources=(
            Source(title="JLS §3.10.1", url=f"{JLS}/jls-3.html#jls-3.10.1"),
            JLS_INT_RANGE,
        ),
    ),
    Rule(
        id=RuleId.INT_OVERFLOW,
        category=Category.NUMERIC,
        reason="Python ints have unlimited precision; Java int and long arithmetic "
        "wraps silently on overflow (1000000 * 1000000 as an int is -727379968).",
        sources=(
            PY_NUMERIC,
            JLS_INT_OPS,
            Source(title="JLS §15.17.1", url=f"{JLS}/jls-15.html#jls-15.17.1"),
        ),
    ),
    Rule(
        id=RuleId.INT_PARSE,
        category=Category.NUMERIC,
        reason="Python int() accepts any size; Java Integer.parseInt and "
        "Scanner.nextInt throw for values outside int range, so the translation "
        "must choose int, long or BigInteger.",
        sources=(
            PY_NUMERIC,
            Source(
                title="Java Integer.parseInt",
                url=f"{API}/java/lang/Integer.html#parseInt(java.lang.String,int)",
            ),
            Source(
                title="Java Scanner.nextInt",
                url=f"{API}/java/util/Scanner.html#nextInt()",
            ),
        ),
    ),
    Rule(
        id=RuleId.SUM_OVERFLOW,
        category=Category.NUMERIC,
        reason="A Python sum() of ints never overflows; a Java int accumulator "
        "wraps silently.",
        sources=(PY_NUMERIC, JLS_INT_OPS),
    ),
    Rule(
        id=RuleId.FLOAT_PRECISION,
        category=Category.NUMERIC,
        reason="Python floats are usually 64-bit doubles; Java float is 32-bit, "
        "so the translation should use double.",
        sources=(PY_NUMERIC, JLS_FLOAT),
    ),
    Rule(
        id=RuleId.MODULAR_POW,
        category=Category.NUMERIC,
        reason="Three-argument pow computes base**exp % mod exactly; Java's "
        "Math.pow returns a double, so the translation needs BigInteger.modPow "
        "or a modular loop.",
        sources=(
            Source(title="Python pow()", url=f"{PY}/library/functions.html#pow"),
            Source(
                title="Java Math.pow",
                url=f"{API}/java/lang/Math.html#pow(double,double)",
            ),
            Source(
                title="Java BigInteger.modPow",
                url=f"{API}/java/math/BigInteger.html"
                "#modPow(java.math.BigInteger,java.math.BigInteger)",
            ),
        ),
    ),
    Rule(
        id=RuleId.TRUE_DIVISION,
        category=Category.DIVISION,
        reason="Python / on ints gives a float (7 / 2 is 3.5); Java int / int "
        "truncates (7 / 2 is 3).",
        sources=(PY_ARITHMETIC, JLS_DIVISION),
    ),
    Rule(
        id=RuleId.FLOOR_DIVISION,
        category=Category.DIVISION,
        reason="Python // rounds down (-7 // 2 is -4); Java integer / rounds "
        "toward zero (-7 / 2 is -3). Math.floorDiv matches Python.",
        sources=(
            PY_ARITHMETIC,
            JLS_DIVISION,
            Source(
                title="Java Math.floorDiv",
                url=f"{API}/java/lang/Math.html#floorDiv(int,int)",
            ),
        ),
    ),
    Rule(
        id=RuleId.MODULO_SIGN,
        category=Category.DIVISION,
        reason="Python % takes the divisor's sign (-7 % 2 is 1); Java % takes the "
        "dividend's (-7 % 2 is -1). Math.floorMod matches Python.",
        sources=(
            PY_ARITHMETIC,
            Source(title="JLS §15.17.3", url=f"{JLS}/jls-15.html#jls-15.17.3"),
            Source(
                title="Java Math.floorMod",
                url=f"{API}/java/lang/Math.html#floorMod(int,int)",
            ),
        ),
    ),
    Rule(
        id=RuleId.LINE_INPUT,
        category=Category.INPUT,
        reason="Python reads whole lines; Java Scanner reads whitespace-separated "
        "tokens, and nextLine() after nextInt() returns the rest of the current "
        "line, often an empty string.",
        sources=(
            Source(title="Python input()", url=f"{PY}/library/functions.html#input"),
            Source(
                title="Java Scanner.nextLine",
                url=f"{API}/java/util/Scanner.html#nextLine()",
            ),
        ),
    ),
    Rule(
        id=RuleId.WHITESPACE_SPLIT,
        category=Category.INPUT,
        reason="split() with no argument treats any run of whitespace as one "
        'separator and drops leading and trailing empties; Java split(" ") '
        "splits on every single space and keeps a leading empty string.",
        sources=(
            Source(
                title="Python str.split", url=f"{PY}/library/stdtypes.html#str.split"
            ),
            Source(
                title="Java String.split",
                url=f"{API}/java/lang/String.html#split(java.lang.String)",
            ),
        ),
    ),
    Rule(
        id=RuleId.PERCENT_FORMAT,
        category=Category.OUTPUT,
        reason="Python %-formatting is lenient ('%d' % 3.7 gives '3'); Java "
        "String.format throws IllegalFormatConversionException for %d with a "
        "double.",
        sources=(
            Source(
                title="Python printf-style formatting",
                url=f"{PY}/library/stdtypes.html#old-string-formatting",
            ),
            JAVA_FORMATTER,
        ),
    ),
    Rule(
        id=RuleId.STR_FORMAT,
        category=Category.OUTPUT,
        reason="str.format uses Python's format spec mini-language (e.g. {:,} or "
        "{:>5}); Java String.format uses %-style specifiers, so each spec must "
        "be rewritten.",
        sources=(PY_FORMAT_SPEC, JAVA_FORMATTER),
    ),
    Rule(
        id=RuleId.FSTRING_SPEC,
        category=Category.OUTPUT,
        reason="f-string format specs (e.g. {x:.2f}) use Python's format spec "
        "mini-language; Java String.format uses %-style specifiers, so each "
        "spec must be rewritten.",
        sources=(PY_FORMAT_SPEC, JAVA_FORMATTER),
    ),
    Rule(
        id=RuleId.PRINT_SEP_END,
        category=Category.OUTPUT,
        reason="A custom sep or end changes what print() writes between and "
        "after items; Java must reproduce it exactly.",
        sources=(PY_PRINT,),
    ),
    Rule(
        id=RuleId.PRINT_STARRED,
        category=Category.OUTPUT,
        reason="print(*xs) prints items separated by spaces; Java prints a List "
        "as [1, 2] and an array as its type and hash code.",
        sources=(
            PY_PRINT,
            Source(
                title="Java AbstractCollection.toString",
                url=f"{API}/java/util/AbstractCollection.html#toString()",
            ),
            Source(
                title="Java Object.toString",
                url=f"{API}/java/lang/Object.html#toString()",
            ),
        ),
    ),
    Rule(
        id=RuleId.PRINT_ARGS,
        category=Category.OUTPUT,
        reason="print(a, b) puts a space between arguments; Java string "
        "concatenation adds nothing.",
        sources=(PY_PRINT,),
    ),
    Rule(
        id=RuleId.PRINT_BOOL,
        category=Category.OUTPUT,
        reason="Python prints True/False; Java prints true/false.",
        sources=(
            Source(
                title="Java String.valueOf(boolean)",
                url=f"{API}/java/lang/String.html#valueOf(boolean)",
            ),
        ),
    ),
    Rule(
        id=RuleId.ROUNDING,
        category=Category.API,
        reason="Python round() rounds ties to even (round(2.5) is 2) and returns "
        "an int; Java Math.round rounds ties up (2.5 gives 3) and returns a long.",
        sources=(
            Source(title="Python round()", url=f"{PY}/library/functions.html#round"),
            Source(
                title="Java Math.round",
                url=f"{API}/java/lang/Math.html#round(double)",
            ),
        ),
    ),
    Rule(
        id=RuleId.SLICING,
        category=Category.API,
        reason="Python slicing clamps out-of-range bounds ([1, 2][5:9] is []); "
        "Java subList and substring throw, and Arrays.copyOfRange pads with "
        "zeros.",
        sources=(
            PY_SEQUENCES,
            Source(
                title="Java List.subList",
                url=f"{API}/java/util/List.html#subList(int,int)",
            ),
            Source(
                title="Java String.substring",
                url=f"{API}/java/lang/String.html#substring(int,int)",
            ),
            Source(
                title="Java Arrays.copyOfRange",
                url=f"{API}/java/util/Arrays.html#copyOfRange(int%5B%5D,int,int)",
            ),
        ),
    ),
    Rule(
        id=RuleId.NEGATIVE_INDEX,
        category=Category.API,
        reason="Negative indices count from the end in Python (xs[-1] is the last "
        "item); Java throws ArrayIndexOutOfBoundsException.",
        sources=(
            PY_SEQUENCES,
            Source(title="JLS §15.10.4", url=f"{JLS}/jls-15.html#jls-15.10.4"),
        ),
    ),
    Rule(
        id=RuleId.EXCEPTIONS,
        category=Category.ERRORS,
        reason="The same failure raises different exceptions (int('x') raises "
        'ValueError; Integer.parseInt("x") throws NumberFormatException), so '
        "the translation must choose what to catch.",
        sources=(
            Source(
                title="Python built-in exceptions",
                url=f"{PY}/library/exceptions.html",
            ),
            Source(
                title="Java Integer.parseInt",
                url=f"{API}/java/lang/Integer.html#parseInt(java.lang.String,int)",
            ),
        ),
    ),
)

RULES: dict[RuleId, Rule] = {rule.id: rule for rule in _RULES}
"""Every booklet rule, keyed by its id."""
