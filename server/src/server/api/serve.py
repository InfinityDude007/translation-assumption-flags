"""Command to serve the review API locally."""

import uvicorn

from ..settings import (
    get_api_settings,
    get_baseline_settings,
    get_dataset_settings,
    get_evaluation_settings,
)
from .app import create_app


def main() -> None:
    """Serve the API with uvicorn, configured from the settings.

    Usage: serve
    """
    api = get_api_settings()
    baseline = get_baseline_settings()
    app = create_app(
        get_dataset_settings().samples_dir,
        get_evaluation_settings().runs_dir,
        api.decisions_file,
        api.cors_origins,
        baseline.baselines_dir,
        baseline.threshold,
    )
    uvicorn.run(app, host=api.host, port=api.port)
