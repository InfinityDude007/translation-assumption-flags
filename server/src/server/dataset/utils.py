"""Download, hashing and extraction helpers for the dataset."""

import hashlib
import urllib.request
import zipfile
from pathlib import Path


def download(url: str, dest: Path, chunk_size: int) -> None:
    """Stream a URL to a file, printing progress.

    Args:
        url: Address to download.
        dest: File to write.
        chunk_size: Bytes to read per step.
    """
    with urllib.request.urlopen(url) as response, dest.open("wb") as out:
        total = int(response.headers.get("Content-Length", 0))
        done = 0
        while chunk := response.read(chunk_size):
            out.write(chunk)
            done += len(chunk)
            if total:
                print(f"\r  {done / total:4.0%} of {total / 1e6:.0f} MB", end="")
    print()


def md5(path: Path, chunk_size: int) -> str:
    """Return the MD5 hex digest of a file.

    Args:
        path: File to hash.
        chunk_size: Bytes to read per step.

    Returns:
        The digest as a hex string.
    """
    digest = hashlib.md5(usedforsecurity=False)
    with path.open("rb") as f:
        while chunk := f.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def extract(zip_path: Path, prefixes: tuple[str, ...], dest: Path) -> int:
    """Extract only the zip members under the given prefixes.

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
