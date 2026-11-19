"""Rule-based detection of Python constructs whose Java translation needs an assumption."""

from .detector import detect
from .models import Category, RuleId
from .rules import RULES

__all__ = ["RULES", "Category", "RuleId", "detect"]
