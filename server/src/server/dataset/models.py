"""Data models for the dataset download and sample selection."""

from pydantic import BaseModel, ConfigDict

from .types import Dataset, Group


class Archive(BaseModel):
    """A Zenodo archive and the parts of it to extract.

    Attributes:
        name: File name on Zenodo.
        md5: Expected MD5 checksum, as published by Zenodo.
        prefixes: Path prefixes inside the zip to extract.
    """

    model_config = ConfigDict(frozen=True)

    name: str
    md5: str
    prefixes: tuple[str, ...]


class Label(BaseModel):
    """One bug label from Pan et al.'s manual labelling sheet.

    Attributes:
        code: Bug type code, e.g. "C1".
        bug_type: Full bug type, e.g. "C1: Incorrect data type".
        impact: Observed effect, e.g. "Runtime Error".
    """

    model_config = ConfigDict(frozen=True)

    code: str
    bug_type: str
    impact: str


class Program(BaseModel):
    """A Python program in the dataset and its GPT-4 Java translation.

    Attributes:
        dataset: Dataset folder name, "avatar" or "codenet".
        name: File name without extension, e.g. "atcoder_ABC149_B".
    """

    model_config = ConfigDict(frozen=True)

    dataset: Dataset
    name: str

    @property
    def id(self) -> str:
        """Name of folder with sample, e.g. "avatar-atcoder_ABC149_B"."""
        return f"{self.dataset}-{self.name}"

    def __hash__(self) -> int:
        """Hash by field values so programs can be dict keys and set members."""
        return hash((self.dataset, self.name))


class BugLines(BaseModel):
    """Hand-tagged line numbers (1-based) of a bug in each file.

    Attributes:
        source: Lines in the Python source.
        translation: Lines in the Java translation.
    """

    source: list[int] = []
    translation: list[int] = []


class SampleMeta(BaseModel):
    """Contents of a sample's meta.json.

    Attributes:
        id: Sample folder name.
        dataset: Dataset folder name.
        program: Program file name without extension.
        group: "buggy" if Pan et al. labelled a semantic bug, else "control".
        pan_labels: Pan et al.'s labels for the translation.
        tests: Test file names in the raw data's TestCases folder.
        bug_lines: Hand-tagged bug lines, empty until tagged.
        notes: Free-text tagging notes.
    """

    id: str
    dataset: Dataset
    program: str
    group: Group
    pan_labels: list[Label]
    tests: list[str]
    bug_lines: BugLines = BugLines()
    notes: str = ""
