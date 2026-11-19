"""Literal types for navigating the data directory and selecting samples."""

from typing import Literal

Dataset = Literal["avatar", "codenet"]
"""Dataset folder names in Pan et al.'s artefact."""

Group = Literal["buggy", "control"]
"""Whether a sample has a labelled semantic bug or none."""
