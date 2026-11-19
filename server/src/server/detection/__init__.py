"""Rule-based detection of Python constructs whose Java translation needs an assumption."""

from .detector import detect
from .models import Category, Site

__all__ = ["Category", "Site", "detect"]
