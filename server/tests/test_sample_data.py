"""Integrity checks for the committed samples and their tags."""

from pathlib import Path

import pytest

from server.dataset import SampleMeta
from server.settings import get_dataset_settings

META_FILES = sorted(get_dataset_settings().samples_dir.glob("*/meta.json"))


def line_count(path: Path) -> int:
    """Return the number of lines in a text file."""
    return len(path.read_text().splitlines())


@pytest.mark.parametrize("meta_path", META_FILES, ids=lambda p: p.parent.name)
def test_meta_is_valid_and_tags_point_at_real_lines(meta_path: Path) -> None:
    """Each meta.json matches the model, and every tagged line exists in its file."""
    meta = SampleMeta.model_validate_json(meta_path.read_text())
    assert meta.id == meta_path.parent.name

    source = line_count(meta_path.parent / "source.py")
    translation = line_count(meta_path.parent / "translation.java")
    for lines in (meta.bug_lines, meta.latent):
        assert all(1 <= n <= source for n in lines.source)
        assert all(1 <= n <= translation for n in lines.translation)


@pytest.mark.parametrize("meta_path", META_FILES, ids=lambda p: p.parent.name)
def test_controls_have_no_test_exposed_bug(meta_path: Path) -> None:
    """Control samples never carry bug_lines, only latent lines."""
    meta = SampleMeta.model_validate_json(meta_path.read_text())
    if meta.group == "control":
        assert not meta.bug_lines.source and not meta.bug_lines.translation
