"""Tests for the review API, over temporary samples, runs and decisions."""

import json
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from pydantic import BaseModel
from pydantic_settings import SettingsConfigDict

from server.api import create_app, gemini_client
from server.baseline import BaselineConfig, SampleBaseline, line_probabilities
from server.dataset import SampleMeta
from server.evaluation import RunConfig, SampleRun
from server.explanation import PROMPT_VERSION, GeminiAnswer, SiteAnswer, explain
from server.gemini import GeminiClient, GeminiError
from server.settings import ApiSettings

SOURCE = "n = int(input())\nprint(n // 2)\n"
"""Three sites: ids 0 and 1 on line 1, id 2 (floor division) on line 2."""

TRANSLATION = "\n".join(
    [
        "import java.util.Scanner;",
        "public class Main {",
        "    public static void main(String[] args) {",
        "        int n = new Scanner(System.in).nextInt();",
        "        System.out.println(n / 2);",
        "    }",
        "}",
    ]
)

SAMPLE = "avatar-atcoder_ABC000_A"
ORIGIN = "http://localhost:5173"


class FakeClient(GeminiClient):
    """A Gemini client that returns a fixed answer, or raises a fixed error."""

    def __init__(self, error: GeminiError | None = None) -> None:
        """Store the error to raise, if any; no SDK client is created."""
        self._model = "gemini-test"
        self.error = error

    def complete[T: BaseModel](self, system: str, prompt: str, schema: type[T]) -> T:
        """Raise the stored error, or answer every site of SOURCE."""
        if self.error:
            raise self.error
        answers = [
            SiteAnswer(
                site_id=site_id,
                verdict="mismatch" if site_id == 2 else "handled",
                translation_lines=[line],
                assumption="assumes something",
                suggestion="Math.floorDiv(n, 2)" if site_id == 2 else None,
                reasoning="secret working",
            )
            for site_id, line in [(0, 4), (1, 4), (2, 5)]
        ]
        return schema.model_validate(GeminiAnswer(answers=answers).model_dump())


@pytest.fixture
def folders(tmp_path: Path) -> dict[str, Path]:
    """Write one sample and one archived run holding it."""
    sample = tmp_path / "samples" / SAMPLE
    sample.mkdir(parents=True)
    meta = SampleMeta.model_validate(
        {
            "id": SAMPLE,
            "dataset": "avatar",
            "program": "atcoder_ABC000_A",
            "group": "buggy",
            "pan_labels": [],
            "tests": [],
            "bug_lines": {"source": [2], "translation": [5]},
            "notes": "the answer",
        }
    )
    (sample / "meta.json").write_text(meta.model_dump_json())
    (sample / "source.py").write_text(SOURCE)
    (sample / "translation.java").write_text(TRANSLATION)

    run = tmp_path / "runs" / "test-v1"
    run.mkdir(parents=True)
    now = datetime.now(UTC)
    config = RunConfig(
        name="test-v1", model="gemini-test", prompt_version="1", created_at=now
    )
    (run / "run.json").write_text(config.model_dump_json())
    archived = SampleRun(
        sample_id=SAMPLE,
        finished_at=now,
        seconds=1.0,
        explanation=explain(SOURCE, TRANSLATION, FakeClient()),
    )
    (run / f"{SAMPLE}.json").write_text(archived.model_dump_json())
    (run / "score.json").write_text("{}")

    baseline = tmp_path / "baselines" / "test-model"
    baseline.mkdir(parents=True)
    (baseline / "baseline.json").write_text(
        BaselineConfig(
            name="test-model", model="fake/model", prompt_version="1", created_at=now
        ).model_dump_json()
    )
    lines = line_probabilities(TRANSLATION, [(0, len(TRANSLATION), 0.5)])
    lines[4] = lines[4].model_copy(update={"lowest": 0.01})
    scored = SampleBaseline(sample_id=SAMPLE, finished_at=now, seconds=0.1, lines=lines)
    (baseline / f"{SAMPLE}.json").write_text(scored.model_dump_json())

    return {
        "samples": tmp_path / "samples",
        "runs": tmp_path / "runs",
        "decisions": tmp_path / "decisions.jsonl",
        "baselines": tmp_path / "baselines",
    }


@pytest.fixture
def api(folders: dict[str, Path]) -> Iterator[TestClient]:
    """A test client for the app over the temporary folders."""
    app = create_app(
        folders["samples"],
        folders["runs"],
        folders["decisions"],
        [ORIGIN],
        folders["baselines"],
        1,
    )
    app.dependency_overrides[gemini_client] = lambda: FakeClient()
    yield TestClient(app)


def decision(review: dict[str, Any], kind: str = "confirmed") -> dict[str, Any]:
    """Build a decision request on the review's floor-division flag."""
    return {
        "sample_id": SAMPLE,
        "run": review["run"],
        "model": review["model"],
        "prompt_version": review["prompt_version"],
        "flag": review["flags"][-1],
        "decision": kind,
    }


def test_samples_are_listed_without_labels(api: TestClient) -> None:
    """The picker gets ids only: no group, labels, tagged lines or notes."""
    response = api.get("/samples")
    assert response.status_code == 200
    assert response.json() == [
        {"id": SAMPLE, "dataset": "avatar", "program": "atcoder_ABC000_A"}
    ]


def test_sample_code_is_returned(api: TestClient) -> None:
    """A sample's code is read from its folder."""
    body = api.get(f"/samples/{SAMPLE}").json()
    assert body == {"id": SAMPLE, "source": SOURCE, "translation": TRANSLATION}


@pytest.mark.parametrize("sample_id", ["nope", "..", "%2E%2E%2Fruns"])
def test_unknown_samples_are_not_found(api: TestClient, sample_id: str) -> None:
    """Only listed sample ids are served, so ids cannot reach other folders."""
    assert api.get(f"/samples/{sample_id}").status_code == 404


def test_runs_are_listed_with_their_sample_count(api: TestClient) -> None:
    """run.json and score.json are not counted as samples."""
    [run] = api.get("/runs").json()
    assert (run["name"], run["model"], run["prompt_version"]) == (
        "test-v1",
        "gemini-test",
        "1",
    )
    assert run["samples"] == 1


def test_archived_review_hides_gemini_working(api: TestClient) -> None:
    """Reviewers see flags with stable ids, but not the reasoning or raw answer."""
    response = api.get(f"/runs/test-v1/samples/{SAMPLE}")
    assert response.status_code == 200
    review = response.json()
    assert review["run"] == "test-v1"
    assert [flag["id"] for flag in review["flags"]] == [
        "input-1",
        "numeric-1",
        "division-2",
    ]
    assert "secret working" not in response.text
    assert "answer" not in review


@pytest.mark.parametrize(
    "path", ["/runs/nope/samples/" + SAMPLE, "/runs/test-v1/samples/nope"]
)
def test_missing_archived_reviews_are_not_found(api: TestClient, path: str) -> None:
    """An unknown run or sample is a 404."""
    assert api.get(path).status_code == 404


def test_run_score_counts_caught_bugs(api: TestClient) -> None:
    """The score is worked out from the archived flags and the tagged lines."""
    response = api.get("/runs/test-v1/score")
    assert response.status_code == 200
    score = response.json()
    assert score["config"]["name"] == "test-v1"
    assert (score["bugs"], score["bugs_caught"]) == (1, 1)
    assert (score["mismatch_flags"], score["false_alarms"]) == (1, 0)
    [sample] = score["samples"]
    assert (sample["sample_id"], sample["bug_caught"]) == (SAMPLE, True)
    assert score["missing"] == []


def test_unknown_run_has_no_score(api: TestClient) -> None:
    """Scoring a run that does not exist is a 404."""
    assert api.get("/runs/nope/score").status_code == 404


def test_baselines_are_listed(api: TestClient) -> None:
    """Each baseline is listed with its model and sample count."""
    [baseline] = api.get("/baselines").json()
    assert (baseline["name"], baseline["model"]) == ("test-model", "fake/model")
    assert baseline["samples"] == 1


def test_probabilities_come_with_the_threshold(api: TestClient) -> None:
    """With a budget of one line, the threshold sits just above the lowest line."""
    response = api.get(f"/baselines/test-model/samples/{SAMPLE}")
    assert response.status_code == 200
    body = response.json()
    assert (body["baseline"], body["model"], body["threshold"]) == (
        "test-model",
        "fake/model",
        0.5,
    )
    assert [line["lowest"] for line in body["lines"]][3:5] == [0.5, 0.01]


@pytest.mark.parametrize(
    "path", ["/baselines/nope/samples/x", f"/baselines/nope/samples/{SAMPLE}"]
)
def test_unknown_baselines_are_not_found(api: TestClient, path: str) -> None:
    """An unknown baseline is a 404, before the sample is looked at."""
    assert api.get(path).status_code == 404


def test_baseline_score_uses_the_threshold(api: TestClient) -> None:
    """Only the one budgeted line is highlighted, and it is the bug line."""
    score = api.get("/baselines/test-model/score").json()
    assert (score["threshold"], score["bugs_caught"], score["highlighted"]) == (
        0.5,
        1,
        1,
    )


def test_no_baselines_folder_means_none(folders: dict[str, Path]) -> None:
    """Without a baselines folder the list is empty and lookups are 404."""
    api = TestClient(
        create_app(folders["samples"], folders["runs"], folders["decisions"], [])
    )
    assert api.get("/baselines").json() == []
    assert api.get("/baselines/test-model/score").status_code == 404


def test_analyse_explains_live(api: TestClient) -> None:
    """A live analysis has no run and keeps Gemini's working out of the response."""
    response = api.post("/analyse", json={"source": SOURCE, "translation": TRANSLATION})
    assert response.status_code == 200
    review = response.json()
    assert review["run"] is None
    assert review["prompt_version"] == PROMPT_VERSION
    assert review["flags"][-1]["verdict"] == "mismatch"
    assert "secret working" not in response.text


def test_analyse_rejects_invalid_python(api: TestClient) -> None:
    """Source that does not parse is a 422 with the parser's message."""
    response = api.post("/analyse", json={"source": "def (", "translation": ""})
    assert response.status_code == 422
    assert "not valid Python" in response.json()["detail"]


@pytest.mark.parametrize(
    ("gemini_status", "expected"), [(429, 429), (503, 503), (400, 502), (None, 502)]
)
def test_gemini_failures_map_to_statuses(
    folders: dict[str, Path], gemini_status: int | None, expected: int
) -> None:
    """Rate limits and overload pass through; other failures are a bad gateway."""
    app = create_app(folders["samples"], folders["runs"], folders["decisions"], [])
    app.dependency_overrides[gemini_client] = lambda: FakeClient(
        GeminiError("failed", gemini_status)
    )
    response = TestClient(app).post(
        "/analyse", json={"source": SOURCE, "translation": TRANSLATION}
    )
    assert response.status_code == expected
    assert response.json()["detail"] == "failed"


def test_missing_key_is_unavailable(
    folders: dict[str, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Without a Gemini key, live analysis is a 503 that says what to set."""

    def no_key() -> GeminiClient:
        raise ValueError("set GEMINI_API_KEY")

    monkeypatch.setattr("server.api.app.get_client", no_key)
    app = create_app(folders["samples"], folders["runs"], folders["decisions"], [])
    response = TestClient(app).post(
        "/analyse", json={"source": SOURCE, "translation": TRANSLATION}
    )
    assert response.status_code == 503
    assert response.json()["detail"] == "set GEMINI_API_KEY"


def test_decisions_are_appended_and_listed(
    api: TestClient, folders: dict[str, Path]
) -> None:
    """Each decision is one JSON line; later ones are added, not replaced."""
    review = api.get(f"/runs/test-v1/samples/{SAMPLE}").json()
    first = api.post("/decisions", json=decision(review, "confirmed"))
    second = api.post("/decisions", json=decision(review, "dismissed"))
    assert (first.status_code, second.status_code) == (201, 201)
    assert first.json()["decided_at"]

    lines = folders["decisions"].read_text().splitlines()
    assert [json.loads(line)["decision"] for line in lines] == [
        "confirmed",
        "dismissed",
    ]
    listed = api.get("/decisions", params={"sample_id": SAMPLE}).json()
    assert [d["flag"]["id"] for d in listed] == ["division-2", "division-2"]
    assert api.get("/decisions", params={"run": "other"}).json() == []


def test_unknown_decisions_are_rejected(api: TestClient) -> None:
    """Only confirmed, intended and dismissed are accepted."""
    review = api.get(f"/runs/test-v1/samples/{SAMPLE}").json()
    response = api.post("/decisions", json=decision(review, "maybe"))
    assert response.status_code == 422


def test_no_decisions_file_means_no_decisions(api: TestClient) -> None:
    """Listing before anything is logged gives an empty list."""
    assert api.get("/decisions").json() == []


def test_frontend_origin_is_allowed(api: TestClient) -> None:
    """The configured frontend origin gets CORS headers; others do not."""
    allowed = api.get("/samples", headers={"Origin": ORIGIN})
    other = api.get("/samples", headers={"Origin": "http://evil.example"})
    assert allowed.headers["access-control-allow-origin"] == ORIGIN
    assert "access-control-allow-origin" not in other.headers


class IsolatedApiSettings(ApiSettings):
    """API settings that skip the developer's .env file."""

    model_config = SettingsConfigDict(env_prefix="API_", env_file=None)


def test_api_settings_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    """The API listens locally and allows the Vite dev server by default."""
    for name in ("API_HOST", "API_PORT", "API_CORS_ORIGINS", "API_DECISIONS_FILE"):
        monkeypatch.delenv(name, raising=False)
    settings = IsolatedApiSettings()
    assert (settings.host, settings.port) == ("127.0.0.1", 8000)
    assert settings.cors_origins == [ORIGIN]
    assert settings.decisions_file.name == "decisions.jsonl"
