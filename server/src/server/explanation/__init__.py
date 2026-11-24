"""Gemini explanations of detector sites, checked before they become flags."""

from .explainer import explain
from .models import Explanation, GeminiAnswer, SiteAnswer
from .prompts import PROMPT_VERSION, SYSTEM_PROMPT, build_prompt

__all__ = [
    "PROMPT_VERSION",
    "SYSTEM_PROMPT",
    "Explanation",
    "GeminiAnswer",
    "SiteAnswer",
    "build_prompt",
    "explain",
]
