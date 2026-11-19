"""Data models for the dataset download."""

from pydantic import BaseModel, ConfigDict


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
