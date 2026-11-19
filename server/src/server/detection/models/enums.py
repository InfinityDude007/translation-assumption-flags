"""String enums for mismatch categories and rule ids."""

from enum import StrEnum


class Category(StrEnum):
    """Mismatch categories, mapped onto Pan et al. (2024)'s bug taxonomy."""

    NUMERIC = "numeric"  # C1: incorrect data type
    INPUT = "input"  # C2: incorrect input parsing
    OUTPUT = "output"  # C3: output formatting
    API = "api"  # A3/B6: API behaviour mismatch
    DIVISION = "division"  # A4: incorrect use of operator
    ERRORS = "errors"  # exception handling


class RuleId(StrEnum):
    """Identifiers for the entries in the rule booklet."""

    CONST_OVERFLOW = "const_overflow"
    LITERAL_OVERFLOW = "literal_overflow"
    INT_OVERFLOW = "int_overflow"
    INT_PARSE = "int_parse"
    SUM_OVERFLOW = "sum_overflow"
    FLOAT_PRECISION = "float_precision"
    MODULAR_POW = "modular_pow"
    TRUE_DIVISION = "true_division"
    FLOOR_DIVISION = "floor_division"
    MODULO_SIGN = "modulo_sign"
    LINE_INPUT = "line_input"
    WHITESPACE_SPLIT = "whitespace_split"
    PERCENT_FORMAT = "percent_format"
    STR_FORMAT = "str_format"
    FSTRING_SPEC = "fstring_spec"
    PRINT_SEP_END = "print_sep_end"
    PRINT_STARRED = "print_starred"
    PRINT_ARGS = "print_args"
    PRINT_BOOL = "print_bool"
    ROUNDING = "rounding"
    SLICING = "slicing"
    NEGATIVE_INDEX = "negative_index"
    EXCEPTIONS = "exceptions"
