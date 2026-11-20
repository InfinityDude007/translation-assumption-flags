"""Tests for the explainer's prompt and its checks on Claude's answer."""

import json

import anthropic
import httpx2
from pydantic import BaseModel
from server.explanation import explain
from server.explanation.models import ClaudeAnswer, Explanation, SiteAnswer
from server.explanation.prompts import PROMPT_VERSION, SYSTEM_PROMPT, build_prompt

from server.claude import ClaudeClient
from server.detection import detect

SOURCE = "n = int(input())\nprint(n // 2)\n"
"""Three sites: line_input (id 0) and int_parse (id 1) on line 1, floor_division (id 2) on line 2."""

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


class FakeClient(ClaudeClient):
    """A Claude client that returns a fixed answer and records each call."""

    def __init__(self, answer: ClaudeAnswer) -> None:
        """Store the answer to return; no SDK client is created."""
        self.answer = answer
        self.calls: list[tuple[str, str]] = []

    def complete[T: BaseModel](self, system: str, prompt: str, schema: type[T]) -> T:
        """Record the call and return the fixed answer, validated as `schema`."""
        self.calls.append((system, prompt))
        return schema.model_validate(self.answer.model_dump())


def answer(site_id: int, lines: list[int], verdict: str = "mismatch") -> SiteAnswer:
    """Build one site answer with placeholder text."""
    return SiteAnswer.model_validate(
        {
            "site_id": site_id,
            "verdict": verdict,
            "translation_lines": lines,
            "assumption": "assumes something",
            "suggestion": "change it",
            "reasoning": "working",
        }
    )


def run(*answers: SiteAnswer) -> tuple[Explanation, FakeClient]:
    """Explain the sample program with a fake client giving these answers."""
    client = FakeClient(ClaudeAnswer(answers=list(answers)))
    return explain(SOURCE, TRANSLATION, client), client


def test_no_sites_means_no_call() -> None:
    """A program without mismatch sites is not sent to Claude."""
    client = FakeClient(ClaudeAnswer(answers=[]))
    result = explain("x = 5\n", TRANSLATION, client)
    assert result.flags == [] and result.dropped == [] and client.calls == []


def test_prompt_numbers_both_files_and_lists_every_site() -> None:
    """The message numbers each line and gives every site its id and reason."""
    _, client = run()
    system, prompt = client.calls[0]
    assert system == SYSTEM_PROMPT
    assert "1 | n = int(input())" in prompt
    assert "5 |         System.out.println(n / 2);" in prompt
    sites = json.loads(prompt.split("<sites>")[1].split("</sites>")[0])
    assert [site["id"] for site in sites] == [0, 1, 2]
    assert sites[2]["lines"] == [2, 2] and sites[2]["category"] == "division"


def test_answers_become_flags_with_the_detector_facts() -> None:
    """A valid answer is kept, and the site details come from the detector."""
    result, _ = run(answer(0, [4]), answer(1, [4]), answer(2, [5]))
    assert [flag.translation_lines for flag in result.flags] == [(4,), (4,), (5,)]
    assert result.flags[2].site == detect(SOURCE)[2]
    assert result.prompt_version == PROMPT_VERSION


def test_out_of_range_lines_are_removed_and_sorted() -> None:
    """Line numbers outside the Java file are dropped; the rest are sorted once."""
    result, _ = run(answer(2, [99, 5, 0, 5, 4]), answer(0, [4]), answer(1, [4]))
    assert result.flags[2].translation_lines == (4, 5)


def test_site_without_a_valid_line_is_dropped_with_a_reason() -> None:
    """An answer whose lines are all invalid produces no flag."""
    result, _ = run(answer(0, [4]), answer(1, []), answer(2, [42]))
    assert [flag.site.rule for flag in result.flags] == ["line_input"]
    assert [d.reason for d in result.dropped] == ["no valid Java line"] * 2


def test_unknown_repeated_and_missing_ids() -> None:
    """Unknown ids are ignored, the first answer per id wins, and gaps are reported."""
    result, _ = run(answer(7, [4]), answer(0, [4]), answer(0, [5]))
    assert [flag.translation_lines for flag in result.flags] == [(4,)]
    assert [d.reason for d in result.dropped] == ["no answer for this site"] * 2


def test_suggestion_is_kept_only_for_a_mismatch() -> None:
    """A suggestion on a handled or unclear site is discarded."""
    result, _ = run(
        answer(0, [4], "mismatch"), answer(1, [4], "handled"), answer(2, [5], "unclear")
    )
    assert [flag.suggestion for flag in result.flags] == ["change it", None, None]


def test_schema_is_accepted_by_the_sdk() -> None:
    """The Anthropic SDK turns the answer schema into a structured-output request."""
    seen: list[httpx2.Request] = []

    def handle(request: httpx2.Request) -> httpx2.Response:
        """Record the request and reply with an empty but valid answer."""
        seen.append(request)
        return httpx2.Response(
            200,
            json={
                "id": "msg_1",
                "type": "message",
                "role": "assistant",
                "model": "claude-opus-5-5",
                "content": [{"type": "text", "text": '{"answers": []}'}],
                "stop_reason": "end_turn",
                "stop_sequence": None,
                "usage": {"input_tokens": 1, "output_tokens": 1},
            },
        )

    client = ClaudeClient("claude-opus-5-5", 100, api_key="key")
    client._sdk = anthropic.Anthropic(
        api_key="key",
        http_client=httpx2.Client(transport=httpx2.MockTransport(handle)),
        max_retries=0,
    )
    sites = detect(SOURCE)
    result = client.complete(
        SYSTEM_PROMPT, build_prompt(SOURCE, TRANSLATION, sites), ClaudeAnswer
    )
    assert result == ClaudeAnswer(answers=[])
    body = json.loads(seen[0].content)
    assert "answers" in json.dumps(body["output_config"]["format"]["schema"])
