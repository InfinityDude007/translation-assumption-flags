"""Data models for rules and detected mismatch sites."""

from pydantic import BaseModel, ConfigDict

from .enums import Category, RuleId


class Source(BaseModel):
    """A documentation page that backs a rule.

    Attributes:
        title: Short citation, e.g. "JLS §15.17.2".
        url: Link to the cited section.
    """

    model_config = ConfigDict(frozen=True)

    title: str
    url: str


class Rule(BaseModel):
    """One booklet entry: a Python construct that differs in Java, and why.

    Attributes:
        id: Unique rule identifier.
        category: Mismatch category the rule belongs to.
        reason: How Python and Java differ at this construct.
        sources: Documentation that backs the reason.
    """

    model_config = ConfigDict(frozen=True)

    id: RuleId
    category: Category
    reason: str
    sources: tuple[Source, ...]


class Site(BaseModel):
    """A place in the source where the translation had to make an assumption.

    Attributes:
        rule: The booklet rule that matched.
        category: The kind of mismatch.
        line: First source line of the construct (1-based).
        end_line: Last source line of the construct.
        snippet: Source text of the construct, truncated to 60 characters.
        reason: How Python and Java differ at this construct.
    """

    model_config = ConfigDict(frozen=True)

    rule: RuleId
    category: Category
    line: int
    end_line: int
    snippet: str
    reason: str
