"""Download and extract the parts of Pan et al.'s dataset this project uses."""

import hashlib
import urllib.request
import zipfile
from dataclasses import dataclass
from pathlib import Path

RAW_DIR = Path(__file__).resolve().parents[4] / "data" / "raw"
"""Where the extracted dataset goes (git-ignored)."""

RECORD_URL = "https://zenodo.org/api/records/10447705/files"
"""Zenodo record for Pan et al. (2024)'s artefact, MIT licensed."""

CHUNK_SIZE = 1 << 20
"""Bytes read per step when downloading and hashing (1 MiB)."""


@dataclass(frozen=True)
class Archive:
    """A Zenodo archive and the parts of it to extract.

    Attributes:
        name: File name on Zenodo.
        md5: Expected MD5 checksum, as published by Zenodo.
        prefixes: Path prefixes inside the zip to extract.
    """

    name: str
    md5: str
    prefixes: tuple[str, ...]


ARCHIVES = (
    Archive(
        "dataset.zip",
        "b48d52eb53147c845635d01defae3996",
        ("dataset/avatar/Python/", "dataset/codenet/Python/"),
    ),
    Archive(
        "artifacts.zip",
        "af77884df386d1662d7f92a1cecc42d2",
        (
            "Artifacts/RQ2-Manual Labeling/",
            "Artifacts/RQ1-Translations/GPT-4/avatar/Python/Java/",
            "Artifacts/RQ1-Translations/GPT-4/codenet/Python/Java/",
        ),
    ),
)
"""The archives to fetch: Python sources and tests, GPT-4 translations, bug labels."""


def _download(url: str, dest: Path) -> None:
    """Helper to stream a URL to a file, printing progress.

    Args:
        url: Address to download.
        dest: File to write.
    """
    with urllib.request.urlopen(url) as response, dest.open("wb") as out:
        total = int(response.headers.get("Content-Length", 0))
        done = 0
        while chunk := response.read(CHUNK_SIZE):
            out.write(chunk)
            done += len(chunk)
            if total:
                print(f"\r  {done / total:4.0%} of {total / 1e6:.0f} MB", end="")
    print()


def _md5(path: Path) -> str:
    """Helper to return the MD5 hex digest of a file.

    Args:
        path: File to hash.

    Returns:
        The digest as a hex string.
    """
    digest = hashlib.md5(usedforsecurity=False)
    with path.open("rb") as f:
        while chunk := f.read(CHUNK_SIZE):
            digest.update(chunk)
    return digest.hexdigest()


def _extract(zip_path: Path, prefixes: tuple[str, ...], dest: Path) -> int:
    """Helper to extract the zip members under the given prefixes.

    Args:
        zip_path: Archive to read.
        prefixes: Path prefixes to keep.
        dest: Folder to extract into.

    Returns:
        The number of members extracted.
    """
    with zipfile.ZipFile(zip_path) as zf:
        members = [
            m
            for m in zf.namelist()
            if m.startswith(prefixes) and not m.endswith(".DS_Store")
        ]
        zf.extractall(dest, members)
    return len(members)


def fetch(archive: Archive, dest: Path) -> None:
    """Download, verify and extract one archive, unless already done.

    Args:
        archive: The archive to fetch.
        dest: Folder to extract into.

    Raises:
        SystemExit: If the download's checksum does not match.
    """
    marker = dest / f".{archive.name}.done"
    if marker.exists():
        print(f"{archive.name}: already extracted, skipping")
        return

    zip_path = dest / archive.name
    print(f"{archive.name}: downloading")
    _download(f"{RECORD_URL}/{archive.name}/content", zip_path)

    if _md5(zip_path) != archive.md5:
        zip_path.unlink()
        raise SystemExit(f"{archive.name}: checksum mismatch, download deleted")

    count = _extract(zip_path, archive.prefixes, dest)
    zip_path.unlink()
    marker.touch()
    print(f"{archive.name}: extracted {count} files")


def main() -> None:
    """Fetch every archive into the raw data folder."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    for archive in ARCHIVES:
        fetch(archive, RAW_DIR)
    print(f"Dataset ready in {RAW_DIR}")
