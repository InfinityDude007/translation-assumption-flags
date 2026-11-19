"""Documentation sources shared by booklet rules."""

from ..models import Source

# Base URLs
PY = "https://docs.python.org/3"
JLS = "https://docs.oracle.com/javase/specs/jls/se21/html"
API = "https://docs.oracle.com/en/java/javase/21/docs/api/java.base"


# Python
PY_ARITHMETIC = Source(
    title="Python Reference §6.7",
    url=f"{PY}/reference/expressions.html#binary-arithmetic-operations",
)

PY_NUMERIC = Source(
    title="Python numeric types",
    url=f"{PY}/library/stdtypes.html#numeric-types-int-float-complex",
)

PY_SEQUENCES = Source(
    title="Python common sequence operations",
    url=f"{PY}/library/stdtypes.html#common-sequence-operations",
)

PY_PRINT = Source(title="Python print()", url=f"{PY}/library/functions.html#print")

PY_FORMAT_SPEC = Source(
    title="Python format spec mini-language",
    url=f"{PY}/library/string.html#formatspec",
)


# Java
JLS_INT_RANGE = Source(title="JLS §4.2.1", url=f"{JLS}/jls-4.html#jls-4.2.1")
JLS_INT_OPS = Source(title="JLS §4.2.2", url=f"{JLS}/jls-4.html#jls-4.2.2")
JLS_FLOAT = Source(title="JLS §4.2.3", url=f"{JLS}/jls-4.html#jls-4.2.3")
JLS_DIVISION = Source(title="JLS §15.17.2", url=f"{JLS}/jls-15.html#jls-15.17.2")
JAVA_FORMATTER = Source(title="Java Formatter", url=f"{API}/java/util/Formatter.html")
