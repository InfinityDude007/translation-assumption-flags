"""Download and extract the parts of Pan et al.'s dataset this project uses."""

from ..settings import DatasetSettings, get_dataset_settings
from .models import Archive
from .utils import download, extract, md5

ARCHIVES = (
    Archive(
        name="dataset.zip",
        md5="b48d52eb53147c845635d01defae3996",
        prefixes=("dataset/avatar/Python/", "dataset/codenet/Python/"),
    ),
    Archive(
        name="artifacts.zip",
        md5="af77884df386d1662d7f92a1cecc42d2",
        prefixes=(
            "Artifacts/RQ2-Manual Labeling/",
            "Artifacts/RQ1-Translations/GPT-4/avatar/Python/Java/",
            "Artifacts/RQ1-Translations/GPT-4/codenet/Python/Java/",
        ),
    ),
)
"""The archives to fetch: Python sources and tests, GPT-4 translations, bug labels."""


def fetch(archive: Archive, settings: DatasetSettings) -> None:
    """Download, verify and extract one archive, unless already done.

    Args:
        archive: The archive to fetch.
        settings: Where to download from and extract to.

    Raises:
        SystemExit: If the download's checksum does not match.
    """
    destination = settings.raw_dir
    marker = destination / f".{archive.name}.done"
    if marker.exists():
        print(f"{archive.name}: already extracted, skipping")
        return

    zip_path = destination / archive.name
    print(f"{archive.name}: downloading")
    download(
        f"{settings.record_url}/{archive.name}/content", zip_path, settings.chunk_size
    )

    if md5(zip_path, settings.chunk_size) != archive.md5:
        zip_path.unlink()
        raise SystemExit(f"{archive.name}: checksum mismatch, download deleted")

    count = extract(zip_path, archive.prefixes, destination)
    zip_path.unlink()
    marker.touch()
    print(f"{archive.name}: extracted {count} files")


def main() -> None:
    """Fetch every archive into the raw data folder."""
    settings = get_dataset_settings()
    settings.raw_dir.mkdir(parents=True, exist_ok=True)
    for archive in ARCHIVES:
        fetch(archive, settings)
    print(f"Dataset ready in {settings.raw_dir}")
