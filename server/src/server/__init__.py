"""Backend for flagging semantic assumptions in LLM Python-to-Java translations."""

from .detection import Category, detect

__all__ = ["Category", "detect"]
